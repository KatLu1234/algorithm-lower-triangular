"""POST /api/v1/timetable/solve — 시간표 추천 라우트.

frontend ↔ server 계약:
  요청  TimetableRequest  { preference, top_n?, explain? }
  응답  TimetableResponse { selection?, infeasibility?, explanation? }

MVP 범위 (claude/base/CLAUDE.md §1 안전 순서 step 2):
  - DB·캐시·LLM 미연결. 건물 거리는 후보 강의에서 자동 추출 + 기본 5분.
  - explain=true 여도 explanation=null 반환 (LLM 단계는 별도 base 변경).
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.libs.llm_client import (
    LLMBadResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
    complete,
)
from app.libs.llm_context import build_preference_extraction
from app.libs.buildings_loader import load_building_graph
from app.libs.floyd_warshall import INF as _FW_INF
from app.libs.timeroom_parser import load_courses_from_csv
from app.libs.timetable import recommend
from app.schemas import (
    BuildingCode,
    Course,
    InfeasibilityReport,
    PreferenceVector,
    SelectionResult,
)

# LLM-A delta에서 허용되는 키 — 화이트리스트. 다른 키는 silently 버린다.
_ALLOWED_DELTA_KEYS = frozenset({
    "credit_min", "credit_max",
    "must_include", "exclude", "must_include_groups", "exclude_groups",
    "blackout_windows",
    "course_importance",
    "category_weights", "requirement_weights",
    "professor_preferences", "building_penalties",
    "travel_time_lambda", "compactness_lambda", "diversity_lambda",
    "target_active_days", "back_to_back_preference",
})

router = APIRouter()

# 기본 도보 분 — 같은 건물 0, 다른 건물 _DEFAULT_INTER_BUILDING_MIN.
# 추후 DB(building_travel_times) 또는 app/core/config.py 상수로 대체.
_DEFAULT_INTER_BUILDING_MIN = 5

# 정적 데이터 CSV — 컨테이너에서는 /srv/ 루트 (Dockerfile.backend 참고).
# 로컬 dev에서는 프로젝트 루트.
_ROOT = Path(__file__).resolve().parents[3]
_SAMPLE_CSV_PATH = _ROOT / "sample_data.csv"
_BUILDINGS_CSV_PATH = _ROOT / "buildings.csv"
_TRAVEL_TIMES_CSV_PATH = _ROOT / "building_travel_times.csv"

_sample_courses_cache: list[Course] | None = None
_building_graph_cache: tuple[list[BuildingCode], list[list[int]]] | None = None


def _load_sample_courses() -> list[Course]:
    """sample_data.csv 1회 로드 후 캐시. 파일 없으면 빈 리스트."""
    global _sample_courses_cache
    if _sample_courses_cache is None:
        if _SAMPLE_CSV_PATH.exists():
            _sample_courses_cache = load_courses_from_csv(_SAMPLE_CSV_PATH)
        else:
            _sample_courses_cache = []
    return _sample_courses_cache


def _load_building_graph() -> tuple[list[BuildingCode], list[list[int]]]:
    """buildings.csv + building_travel_times.csv 1회 로드 후 캐시.

    두 파일 중 하나라도 없으면 빈 master로 동작 — _building_grid가 기존 5분 일괄
    행렬로 fallback.
    """
    global _building_graph_cache
    if _building_graph_cache is None:
        if _BUILDINGS_CSV_PATH.exists() and _TRAVEL_TIMES_CSV_PATH.exists():
            _building_graph_cache = load_building_graph(
                _BUILDINGS_CSV_PATH, _TRAVEL_TIMES_CSV_PATH
            )
        else:
            _building_graph_cache = ([], [])
    return _building_graph_cache


class TimetableRequest(BaseModel):
    preference: PreferenceVector
    top_n: int = Field(default=3, ge=1, le=15)
    explain: bool = False


class TimetableResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"description": "솔브 결과 envelope"})

    selection: SelectionResult | None = None
    infeasibility: InfeasibilityReport | None = None
    explanation: str | None = None


def _building_grid(preference: PreferenceVector) -> tuple[list[BuildingCode], list[list[int]]]:
    """후보 강의에서 사용된 건물 ∪ master(buildings.csv) → 거리 행렬.

    CSV가 있으면:
      • master의 직접 간선 그대로 → Floyd-Warshall(B-2)이 간접 경로 산출
      • master에 없는 건물은 5분 fallback으로 모든 건물과 보수적 연결
    CSV 없으면:
      • 후보 강의에서 사용된 건물만 모아 일괄 5분 (기존 동작)
    """
    used: set[BuildingCode] = set()
    for c in preference.courses:
        used.add(c.building)
        for s in c.times:
            if s.building is not None:
                used.add(s.building)

    master_codes, master_matrix = _load_building_graph()

    if not master_codes:
        buildings = sorted(used)
        n = len(buildings)
        walk = [
            [0 if i == j else _DEFAULT_INTER_BUILDING_MIN for j in range(n)]
            for i in range(n)
        ]
        return buildings, walk

    # master 우선, preference에 등장한 새 건물(미등록)도 합집합으로 추가
    all_codes = sorted(set(master_codes) | used)
    n = len(all_codes)
    idx = {c: i for i, c in enumerate(all_codes)}
    walk = [[0 if i == j else _FW_INF for j in range(n)] for i in range(n)]

    # master 직접 간선 복사 (대각 제외)
    for ma, ca in enumerate(master_codes):
        for mb, cb in enumerate(master_codes):
            if ma != mb:
                walk[idx[ca]][idx[cb]] = master_matrix[ma][mb]

    # CSV 미등록 건물: 모든 건물과 _DEFAULT_INTER_BUILDING_MIN으로 보수적 연결 (대칭)
    unknown = used - set(master_codes)
    for c in unknown:
        i = idx[c]
        for j in range(n):
            if i != j and walk[i][j] >= _FW_INF:
                walk[i][j] = _DEFAULT_INTER_BUILDING_MIN
                walk[j][i] = _DEFAULT_INTER_BUILDING_MIN

    return all_codes, walk


class SampleCoursesResponse(BaseModel):
    """샘플 강의 카탈로그 응답."""

    courses: list[Course]
    source: str = Field(description="원본 데이터 소스 (파일명·버전 등)")


class ParsePreferenceRequest(BaseModel):
    """LLM-A 입력 — 자연어 + 현재 PreferenceVector."""

    text: str = Field(min_length=1, max_length=2000)
    preference: PreferenceVector


class ParsePreferenceResponse(BaseModel):
    """LLM-A 결과 — 적용된 PreferenceVector + 이해/미지원 라벨.

    *결정자 아님* — applied/unsupported는 UI가 사용자에게 그대로 보여주는 라벨이며,
    실제 시간표 결정은 PreferenceVector + recommend()가 한다 (product.md §4.4).
    """

    preference: PreferenceVector
    applied: list[str]
    unsupported: list[str]


def _merge_delta(
    base: PreferenceVector, delta: dict, candidates: list[Course]
) -> tuple[PreferenceVector, list[str]]:
    """LLM이 준 delta를 안전하게 병합. 알 수 없는 키·검증 실패는 warnings에 담는다.

    set 필드(must_include, exclude, ...)는 union(기존 ∪ 새 값) — 사용자가 이미 박은
    제약을 LLM이 임의로 비우지 않도록(product.md §4.4 LLM 불변항).
    """
    warnings: list[str] = []
    payload = base.model_dump()
    valid_course_ids = {c.id for c in candidates}
    valid_group_ids = {c.course_group_id for c in candidates if c.course_group_id}

    for key, value in (delta or {}).items():
        if key not in _ALLOWED_DELTA_KEYS:
            warnings.append(f"미지원 필드 무시: {key}")
            continue
        if key in ("must_include", "exclude"):
            ids = [str(x) for x in (value or []) if str(x) in valid_course_ids]
            payload[key] = sorted(set(payload.get(key, []) or []) | set(ids))
            continue
        if key in ("must_include_groups", "exclude_groups"):
            gids = [str(x) for x in (value or []) if str(x) in valid_group_ids]
            payload[key] = sorted(set(payload.get(key, []) or []) | set(gids))
            continue
        if key == "blackout_windows":
            existing = payload.get(key, []) or []
            payload[key] = list(existing) + list(value or [])
            continue
        # dict / scalar — 그대로 교체
        payload[key] = value

    try:
        return PreferenceVector(**payload), warnings
    except ValidationError as e:
        # delta가 부분적으로 깨졌으면 원본 유지 + 사유 안내
        warnings.append("LLM delta 검증 실패 — 부분 업데이트 미적용")
        warnings.append(str(e).splitlines()[0])
        return base, warnings


@router.post("/parse-preference")
def parse_preference(req: ParsePreferenceRequest):
    """자연어 텍스트 → PreferenceVector 부분 업데이트 + 이해/미지원 라벨.

    LLM 키 미설정 시 503 LLM_UNAVAILABLE — 프론트는 자연어 입력 UI를 비활성화.
    """
    messages = build_preference_extraction(
        text=req.text,
        # mode='json'으로 dumping해 set→list, Enum→value 등 JSON-safe 변환
        current_preference=req.preference.model_dump(mode="json"),
        candidate_courses=req.preference.courses,
    )
    try:
        raw = complete(messages, temperature=0.1, response_format="json_object")
    except LLMUnavailableError as e:
        return JSONResponse(
            status_code=503,
            content={"detail": str(e), "code": "LLM_UNAVAILABLE"},
        )
    except LLMTimeoutError as e:
        return JSONResponse(
            status_code=504,
            content={"detail": "LLM 응답 지연. 잠시 후 다시 시도해 주세요.", "code": "LLM_TIMEOUT"},
        )
    except LLMBadResponseError as e:
        return JSONResponse(
            status_code=502,
            content={"detail": "LLM 응답 형식 오류. 잠시 후 다시 시도해 주세요.", "code": "LLM_BAD_RESPONSE"},
        )

    try:
        parsed = json.loads(raw)
        delta = parsed.get("delta") or {}
        applied = [str(x) for x in (parsed.get("applied") or [])]
        unsupported = [str(x) for x in (parsed.get("unsupported") or [])]
    except (ValueError, AttributeError):
        return JSONResponse(
            status_code=502,
            content={"detail": "LLM이 JSON을 반환하지 않았습니다.", "code": "LLM_BAD_RESPONSE"},
        )

    merged, warnings = _merge_delta(req.preference, delta, req.preference.courses)
    return ParsePreferenceResponse(
        preference=merged,
        applied=applied,
        unsupported=unsupported + warnings,
    )


@router.get("/sample-courses", response_model=SampleCoursesResponse)
def sample_courses():
    """국민대 sample_data.csv를 파싱한 강의 풀을 반환.

    프론트가 초기 로드 시 호출해 입력 폼의 후보 강의 풀을 채운다.
    파일이 없거나(로컬 dev 워크트리·테스트 환경) 모두 시간 미정이면 빈 리스트.
    """
    courses = _load_sample_courses()
    return SampleCoursesResponse(
        courses=courses,
        source=_SAMPLE_CSV_PATH.name if _SAMPLE_CSV_PATH.exists() else "(none)",
    )


@router.post("/solve")
def solve(req: TimetableRequest):
    try:
        buildings, walk = _building_grid(req.preference)
        outcome = recommend(req.preference, buildings, walk, top_k=req.top_n)
    except ValueError as e:
        # PreferenceVector 검증 외 도메인 ValueError (recommend 내부의 활동선택·DP 등)
        return JSONResponse(
            status_code=400,
            content={"detail": str(e), "code": "VALIDATION_ERROR"},
        )
    except Exception as e:  # pragma: no cover - 방어선
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "code": "INTERNAL"},
        )

    if isinstance(outcome, InfeasibilityReport):
        body = TimetableResponse(
            selection=None,
            infeasibility=outcome,
            explanation=None,
        )
    else:
        # MVP: LLM 미연결 → explain 플래그와 무관하게 explanation=null
        body = TimetableResponse(
            selection=outcome,
            infeasibility=None,
            explanation=None,
        )
    return body
