"""고려대 수강 데이터 `time_room` 필드 + CSV 로더.

CSV(예: `sample_data.csv`)는 각 행이 한 분반이며, 시간·장소는 `time_room` 컬럼에
다음 형식의 문자열로 들어 있다:

    <요일>(<교시범위>) <건물> <호실>[<br> <요일>(<교시범위>) <건물> <호실> ...]

예시:
    "화(6-8) 석원경상관 112호"
    "수(2-3) 과학기술2관 324호<br> 금(5) 과학기술2관 324호"
    "" (빈 문자열 — 비대면/시간 미정)

교시 매핑 (사용자 명시):
    1교시 = 09:00–10:00
    2교시 = 10:00–11:00
    ...
    n교시 = (n+8):00 – (n+9):00

연속 교시 범위 `(a-b)`는 a교시 시작(09 + a-1)부터 b교시 끝(09 + b)까지로 합산.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from app.schemas import Category, Course, Requirement, TimeSlot, Weekday

# ── 매핑 상수 ────────────────────────────────────────────────────
_KOREAN_WEEKDAY: dict[str, Weekday] = {
    "월": Weekday.MON,
    "화": Weekday.TUE,
    "수": Weekday.WED,
    "목": Weekday.THU,
    "금": Weekday.FRI,
    "토": Weekday.SAT,
    "일": Weekday.SUN,
}

# 1교시 = 9시(=9*60분). n교시 시작 = (n + 8)*60분, 한 교시 길이 60분.
_PERIOD_HOUR_OFFSET = 8
_MINUTES_PER_PERIOD = 60

# 한 칩 (요일·교시·건물·호실)
_TIME_ROOM_CHIP = re.compile(
    r"""
    (?P<day>[월화수목금토일])      # 요일 1자
    \s*\(
        (?P<start>\d+)              # 시작 교시
        (?:\s*-\s*(?P<end>\d+))?    # (선택) 종료 교시
    \)\s+
    (?P<building>[^\s<]+)           # 건물명 (공백·< 전까지)
    (?:\s+(?P<room>\S+))?           # (선택) 호실
    """,
    re.VERBOSE,
)


def _period_start_minute(period: int) -> int:
    return (period + _PERIOD_HOUR_OFFSET) * 60


def _period_end_minute(period: int) -> int:
    return (period + _PERIOD_HOUR_OFFSET + 1) * 60


def parse_time_room(text: str | None) -> list[TimeSlot]:
    """`time_room` 문자열 → TimeSlot 리스트.

    파싱 실패한 칩은 조용히 건너뛴다. 빈/공백 입력은 [] 반환.
    슬롯별 건물은 항상 TimeSlot.building에 채워 둔다 — 같은 강의가 슬롯마다 건물이
    달라도 정확히 표현되도록 (Course.building에는 첫 슬롯 건물을 기본값으로 둠).
    """
    if not text or not text.strip():
        return []
    slots: list[TimeSlot] = []
    # `<br>` (대소문자·self-closing 모두) 기준으로 칩 분리
    for chunk in re.split(r"<\s*br\s*/?>", text, flags=re.IGNORECASE):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = _TIME_ROOM_CHIP.search(chunk)
        if not m:
            continue
        day = _KOREAN_WEEKDAY.get(m["day"])
        if day is None:
            continue
        start_p = int(m["start"])
        end_p = int(m["end"]) if m["end"] else start_p
        if end_p < start_p:
            continue  # 형식 오류
        try:
            slot = TimeSlot(
                day=day,
                start_minute=_period_start_minute(start_p),
                end_minute=_period_end_minute(end_p),
                building=m["building"],
            )
        except ValueError:
            continue  # 24시 넘는 등 검증 실패
        slots.append(slot)
    return slots


# ── CSV → Course 변환 ────────────────────────────────────────────
_ISU_TO_CATEGORY: dict[str, Category] = {
    "전공필수": Category.MAJOR,
    "전공선택": Category.MAJOR,
    "복수전공": Category.DOUBLE_MAJOR,
    "교양": Category.LIBERAL,
    "일선": Category.GENERAL,
}

_ISU_TO_REQUIREMENT: dict[str, Requirement] = {
    "전공필수": Requirement.REQUIRED,
    "전공선택": Requirement.ELECTIVE,
    "교양": Requirement.ELECTIVE,
    "복수전공": Requirement.ELECTIVE,
    "일선": Requirement.OPTIONAL,
}


def _safe_int(value: str | None, default: int = 0) -> int:
    try:
        return int((value or "").strip())
    except ValueError:
        return default


def row_to_course(row: dict[str, str]) -> Course | None:
    """sample_data.csv 한 행 → Course. 시간 미파싱·학점 0 행은 None."""
    slots = parse_time_room(row.get("time_room"))
    if not slots:
        return None
    credit = _safe_int(row.get("credit"))
    if credit <= 0:
        return None

    cour_cd = (row.get("cour_cd") or "").strip()
    cour_cls = (row.get("cour_cls") or "").strip()
    # 고유 강의 ID — params 컬럼은 보통 "CODE@CLASS" 형식. 없으면 직접 조립.
    cid = (row.get("params") or "").strip() or f"{cour_cd}@{cour_cls}"

    isu = (row.get("isu_nm") or "").strip()
    professor = (row.get("prof_nm") or "").strip() or None

    # Course.building 기본값 — 첫 슬롯 건물 (모든 슬롯 building override 채워둠)
    default_building = slots[0].building or "(미정)"

    return Course(
        id=cid,
        name=(row.get("cour_nm") or "").strip() or cid,
        credit=credit,
        building=default_building,
        category=_ISU_TO_CATEGORY.get(isu, Category.GENERAL),
        requirement=_ISU_TO_REQUIREMENT.get(isu),
        times=slots,
        course_group_id=cour_cd or None,  # 같은 cour_cd = 같은 과목의 분반들
        section=cour_cls or None,
        professor=professor,
    )


def load_courses_from_csv(path: str | Path) -> list[Course]:
    """CSV 파일 → Course 리스트. 파싱 불가/시간 미정 행은 자동 제외."""
    p = Path(path)
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [c for c in (row_to_course(row) for row in reader) if c is not None]
