"""PreferenceVector — 사용자 선호·제약의 표준 입력.

알고리즘 트리(A → B → C)가 *유일하게 받는 입력 형태*. 사용자가 폼으로 직접
채웠든, 자유 텍스트를 LLM-A가 수치화했든(선택), 결국 본 객체 한 덩어리로
조립되어 알고리즘에 들어간다.

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
    CourseId,
    Requirement,
)


class PreferenceVector(BaseModel):
    """알고리즘 트리에 들어가는 입력 패키지.

    네 묶음:
      ① 강의 풀과 학점 한도        — A-3·B-3 핵심 입력
      ② 사용자 명시 제약            — A-1에서 즉시 소비
      ③ 강의별 점수 가중치          — B-1에서 v(c) 계산
      ④ 시간표 단위 후처리 가중치   — B-3 누적 점수의 마이너스 항
    """

    model_config = ConfigDict(frozen=True)

    # ① 강의 풀과 학점 한도
    courses: list[Course] = Field(description="후보 강의 리스트")
    credit_min: int = Field(ge=0, description="학점 합 하한")
    credit_max: int = Field(ge=1, description="학점 합 상한 (배낭 용량)")

    # ② 사용자 명시 제약
    course_importance: dict[CourseId, int] = Field(
        default_factory=dict,
        description="강의 ID → 1~5 중요도. 미지정은 기본 3.",
    )
    must_include: set[CourseId] = Field(default_factory=set, description="반드시 포함 강의 ID")
    exclude: set[CourseId] = Field(default_factory=set, description="절대 제외 강의 ID")
    blackout_windows: list[BlackoutWindow] = Field(
        default_factory=list,
        description="사용자 외부 일정. A-1에서 완전 겹침 제거",
    )

    # ③ 강의별 점수 가중치
    time_penalty_grid: dict[str, float] = Field(
        default_factory=dict,
        description="시간대 페널티 (구간 문자열 키 → 가중치)",
    )
    category_weights: dict[Category, float] = Field(
        default_factory=dict,
        description="카테고리별 가산·감산 (예: 전공 +2)",
    )
    requirement_weights: dict[Requirement, float] = Field(
        default_factory=dict,
        description=(
            "이수 요건별 가산·감산 (예: 필수 +1.5). "
            "Category와 직교 차원이라 둘 다 합산. "
            "requirement=None 이거나 매핑 없으면 0."
        ),
    )
    building_penalties: dict[BuildingCode, float] = Field(
        default_factory=dict,
        description="건물별 가산·감산",
    )

    # ④ 시간표 단위 후처리 가중치
    travel_time_lambda: float = Field(default=0.1, ge=0.0, description="이동시간 분당 페널티 λ₁")
    compactness_lambda: float = Field(default=0.5, ge=0.0, description="활성 요일 초과당 페널티 λ₂")
    target_active_days: int = Field(default=5, ge=1, le=7, description="목표 활성 요일 수")
    diversity_lambda: float = Field(default=0.0, ge=0.0, description="건물 다양성 페널티 λ₃")
    back_to_back_preference: float = Field(default=0.0, description="연강/공강 선호")

    @model_validator(mode="after")
    def _check_consistency(self) -> "PreferenceVector":
        if self.credit_min > self.credit_max:
            raise ValueError(
                f"credit_min({self.credit_min}) > credit_max({self.credit_max})"
            )
        for cid, score in self.course_importance.items():
            if not 1 <= score <= 5:
                raise ValueError(
                    f"course_importance[{cid}]={score} out of range [1, 5]"
                )
        course_ids = {c.id for c in self.courses}
        unknown_exclude = self.exclude - course_ids
        unknown_must = self.must_include - course_ids
        if unknown_exclude:
            raise ValueError(f"exclude에 후보 풀에 없는 ID: {unknown_exclude}")
        if unknown_must:
            raise ValueError(f"must_include에 후보 풀에 없는 ID: {unknown_must}")
        return self

    # 편의 메서드
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
