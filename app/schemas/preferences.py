"""PreferenceVector — 사용자 선호·제약의 표준 입력.

알고리즘 트리(A → B → C)가 *유일하게 받는 입력 형태*.

권위 있는 출처: `claude/base/drafts/algorithm-tree.md` §9.6.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import (
    BlackoutWindow,
    BuildingCode,
    Category,
    Course,
    CourseGroupId,
    CourseId,
    Requirement,
)


class PreferenceVector(BaseModel):
    """알고리즘 트리에 들어가는 입력 패키지.

    다섯 묶음:
      ① 강의 풀과 학점 한도        — A-3·B-3 핵심 입력
      ② 사용자 명시 제약 (강의·그룹) — A-1에서 즉시 소비
      ③ 강의별 점수 가중치          — B-1에서 v(c) 계산
      ④ 시간표 단위 후처리 가중치   — B-3 누적 점수의 마이너스 항
      ⑤ 교수별 가중치 (선택)        — B-1에 한 항으로 가산
    """

    model_config = ConfigDict(frozen=True)

    # ① 강의 풀과 학점 한도
    courses: list[Course] = Field(description="후보 강의 리스트")
    credit_min: int = Field(ge=0, description="학점 합 하한")
    credit_max: int = Field(ge=1, description="학점 합 상한 (배낭 용량)")
    category_count_min: dict[Category, int] = Field(
        default_factory=dict,
        description=(
            "카테고리별 강의 *개수* 하한 (예: {Category.MAJOR: 3} = 전공 ≥3개). "
            "credit_min/max는 학점 *합* 제약이고 본 필드는 *개수* 제약(직교). "
            "빈 dict면 비활성(기존 동작). B-3 record 시점 하드 검사."
        ),
    )
    category_count_max: dict[Category, int] = Field(
        default_factory=dict,
        description=(
            "카테고리별 강의 *개수* 상한 (예: {Category.LIBERAL: 2} = 교양 ≤2개). "
            "빈 dict면 비활성. B-3 record 시점 하드 검사."
        ),
    )

    # ② 사용자 명시 제약 — 강의 단위 + 그룹 단위
    course_importance: dict[CourseId, int] = Field(
        default_factory=dict,
        description="강의 ID → 1~5 중요도. 미지정은 기본 3.",
    )
    must_include: set[CourseId] = Field(
        default_factory=set,
        description="반드시 포함할 *특정* 강의 ID (분반까지 콕 집은 경우)",
    )
    exclude: set[CourseId] = Field(
        default_factory=set,
        description="절대 제외할 *특정* 강의 ID",
    )
    must_include_groups: set[CourseGroupId] = Field(
        default_factory=set,
        description=(
            "반드시 포함할 *과목 그룹* ID. 그룹 내 분반 중 *적어도 하나*가 결과에 포함되어야 함. "
            "어떤 분반을 고를지는 시스템이 자동 선택. "
            "must_include(특정 강의)와 함께 쓰면, 그 강의의 그룹은 자동으로 충족."
        ),
    )
    exclude_groups: set[CourseGroupId] = Field(
        default_factory=set,
        description="*과목 그룹* 전체 제외. 같은 group_id의 모든 분반이 풀에서 제거.",
    )
    blackout_windows: list[BlackoutWindow] = Field(
        default_factory=list,
        description="사용자 외부 일정. A-1에서 겹치는 슬롯이 하나라도 있는 강의를 통째로 제거",
    )
    min_break_minutes: int = Field(
        default=0,
        ge=0,
        description=(
            "같은 날 연속 수업 사이에 확보할 최소 쉬는 시간(분). 0이면 비활성(기존 동작). "
            "A-2에서 두 강의 사이 간격이 max(이동시간, min_break_minutes) 미만이면 양립 불가로 처리(하드 제약)."
        ),
    )

    # ③ 강의별 점수 가중치 (B-1에서 v(c)에 합산)
    time_penalty_grid: dict[str, float] = Field(
        default_factory=dict,
        description="시간대 페널티 (구간 문자열 키 → 가중치)",
    )
    category_weights: dict[Category, float] = Field(
        default_factory=dict,
        description="카테고리별 가산·감산",
    )
    requirement_weights: dict[Requirement, float] = Field(
        default_factory=dict,
        description="이수 요건별 가산·감산. Category와 직교 차원이라 둘 다 합산.",
    )
    building_penalties: dict[BuildingCode, float] = Field(
        default_factory=dict,
        description="건물별 가산·감산",
    )

    # ⑤ 교수별 가중치 (옵셔널) — 분반 선호 표현용
    professor_preferences: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "교수별 가산·감산 (예: {'홍교수': +1.0, '김교수': -0.5}). "
            "B-1이 강의의 professor 필드를 룩업해 v(c)에 가산. "
            "같은 그룹 내 분반 선택 시 결정적 신호."
        ),
    )

    # ④ 시간표 단위 후처리 가중치
    travel_time_lambda: float = Field(default=0.1, ge=0.0, description="이동시간 분당 페널티 λ₁")
    compactness_lambda: float = Field(default=0.5, ge=0.0, description="활성 요일 초과당 페널티 λ₂")
    target_active_days: int = Field(default=5, ge=1, le=7, description="목표 활성 요일 수")
    diversity_lambda: float = Field(default=0.0, ge=0.0, description="건물 다양성 페널티 λ₃")
    back_to_back_preference: float = Field(default=0.0, description="연강/공강 선호")
    # S-02 — 시간대 선호 페널티 λ₄ (이른 아침·늦은 저녁 회피의 연속 임계값 표현).
    # time_penalty_grid(정확 구간 문자열)와 공존 — 본 λ는 연속 버전.
    time_window_lambda: float = Field(
        default=0.0, ge=0.0,
        description=(
            "선호 시간창 밖 분(minutes)당 페널티 λ₄. 기본 0=비활성. "
            "preferred_start_minute/preferred_end_minute로 창을 정한다."
        ),
    )
    preferred_start_minute: int = Field(
        default=0, ge=0, le=24 * 60,
        description="선호 시간창 시작(자정 기준 분). 기본 0=하루 시작.",
    )
    preferred_end_minute: int = Field(
        default=24 * 60, ge=0, le=24 * 60,
        description="선호 시간창 종료(자정 기준 분). 기본 1440=하루 끝.",
    )
    # S-03 — 하루 등교 길이(span) 페널티 λ₅. compactness_lambda(요일 수)와 보완 관계.
    daily_span_lambda: float = Field(
        default=0.0, ge=0.0,
        description=(
            "요일별 (마지막 종료 − 첫 시작) 시간(시간 단위) 합당 페널티 λ₅. "
            "기본 0=비활성. '가는 날엔 짧게 끝내고 싶다'를 표현."
        ),
    )

    @model_validator(mode="after")
    def _check_consistency(self) -> "PreferenceVector":
        # 학점 하한·상한
        if self.credit_min > self.credit_max:
            raise ValueError(
                f"credit_min({self.credit_min}) > credit_max({self.credit_max})"
            )
        # 중요도 범위
        for cid, score in self.course_importance.items():
            if not 1 <= score <= 5:
                raise ValueError(
                    f"course_importance[{cid}]={score} out of range [1, 5]"
                )
        # 강의 ID 존재 확인
        course_ids = {c.id for c in self.courses}
        unknown_exclude = self.exclude - course_ids
        unknown_must = self.must_include - course_ids
        if unknown_exclude:
            raise ValueError(f"exclude에 후보 풀에 없는 ID: {unknown_exclude}")
        if unknown_must:
            raise ValueError(f"must_include에 후보 풀에 없는 ID: {unknown_must}")
        # 중복 강의 ID
        course_id_list = [c.id for c in self.courses]
        if len(course_id_list) != len(course_ids):
            from collections import Counter
            dupes = sorted(cid for cid, n in Counter(course_id_list).items() if n > 1)
            raise ValueError(f"중복된 강의 ID: {dupes}")
        # 그룹 ID 존재 확인
        all_groups = {c.course_group_id for c in self.courses if c.course_group_id}
        unknown_must_groups = self.must_include_groups - all_groups
        unknown_exclude_groups = self.exclude_groups - all_groups
        if unknown_must_groups:
            raise ValueError(f"must_include_groups에 없는 그룹: {unknown_must_groups}")
        if unknown_exclude_groups:
            raise ValueError(f"exclude_groups에 없는 그룹: {unknown_exclude_groups}")
        # 그룹 모순 (필수+제외 동시)
        conflict_groups = self.must_include_groups & self.exclude_groups
        if conflict_groups:
            raise ValueError(f"같은 그룹이 필수·제외 동시: {conflict_groups}")
        # 카테고리 개수 — 값 ≥0, 같은 키는 min ≤ max
        for cat, n in self.category_count_min.items():
            if n < 0:
                raise ValueError(f"category_count_min[{cat}]={n} < 0")
        for cat, n in self.category_count_max.items():
            if n < 0:
                raise ValueError(f"category_count_max[{cat}]={n} < 0")
        for cat, n_min in self.category_count_min.items():
            n_max = self.category_count_max.get(cat)
            if n_max is not None and n_min > n_max:
                raise ValueError(
                    f"category_count: {cat} min({n_min}) > max({n_max})"
                )
        # S-02 — 선호 시간창은 start < end
        if self.preferred_start_minute >= self.preferred_end_minute:
            raise ValueError(
                f"preferred_start_minute({self.preferred_start_minute}) "
                f">= preferred_end_minute({self.preferred_end_minute})"
            )
        return self

    # ── 편의 메서드 ──────────────────────────────────────────────
    def importance_of(self, course_id: CourseId, default: int = 3) -> int:
        """강의별 중요도 룩업. 미지정은 기본 3."""
        return self.course_importance.get(course_id, default)

    def building_weight(self, building: BuildingCode) -> float:
        """건물 가중치 룩업. 매핑 없으면 0."""
        return self.building_penalties.get(building, 0.0)

    def category_weight(self, category: Category) -> float:
        """카테고리 가중치 룩업. 매핑 없으면 0."""
        return self.category_weights.get(category, 0.0)

    def requirement_weight(self, requirement: Optional[Requirement]) -> float:
        """이수 요건 가중치 룩업. None 또는 매핑 없으면 0."""
        if requirement is None:
            return 0.0
        return self.requirement_weights.get(requirement, 0.0)

    def professor_weight(self, professor: Optional[str]) -> float:
        """교수 가중치 룩업. None 또는 매핑 없으면 0."""
        if professor is None:
            return 0.0
        return self.professor_preferences.get(professor, 0.0)

    def courses_in_group(self, group_id: CourseGroupId) -> list[Course]:
        """주어진 그룹 ID에 속한 분반 강의 리스트. 그룹 처리 시 A 단계에서 호출."""
        return [c for c in self.courses if c.course_group_id == group_id]
