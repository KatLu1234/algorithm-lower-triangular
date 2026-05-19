"""시간표 추천 도메인 계약 (algorithm-tree.md §9.6 잠정안 기반).

A → B → C 트리 경계의 입출력 모델. 외부 HTTP 노출 시점에서 필드명·구조가
fine-tune 될 수 있음 (§9.9 "구현 시 결정").
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class CourseCategory(str, Enum):
    MAJOR = "major"
    LIBERAL = "liberal"
    ELECTIVE = "elective"


class TimeSlot(BaseModel):
    day: int = Field(ge=0, le=6, description="0=Mon ... 6=Sun")
    start_min: int = Field(ge=0, le=24 * 60)
    end_min: int = Field(ge=0, le=24 * 60)

    @model_validator(mode="after")
    def _check_order(self) -> "TimeSlot":
        if self.start_min >= self.end_min:
            raise ValueError("start_min must be < end_min")
        return self


class Course(BaseModel):
    code: str
    title: str
    credit: int = Field(ge=1)
    importance: int = Field(ge=1, le=5)
    building: str
    category: CourseCategory
    times: list[TimeSlot]


class Blackout(BaseModel):
    day: int = Field(ge=0, le=6)
    start_min: int = Field(ge=0, le=24 * 60)
    end_min: int = Field(ge=0, le=24 * 60)


class Preferences(BaseModel):
    must_include: list[str] = Field(default_factory=list)
    must_exclude: list[str] = Field(default_factory=list)
    blackouts: list[Blackout] = Field(default_factory=list)
    credit_ceiling: int = Field(ge=1)
    credit_floor: int | None = Field(default=None, ge=0)
    top_k: int = Field(default=3, ge=1, le=15)


class TimetableInput(BaseModel):
    courses: list[Course]
    building_codes: list[str]
    base_walk_minutes: list[list[int]]
    preferences: Preferences


class FeasibilityResult(BaseModel):
    candidates: list[Course]
    must_include_mask: list[bool]
    compatible: list[list[bool]]
    building_index: dict[str, int]
    travel_time_matrix: list[list[int]]
    ordered_by_start: list[int]
    credit_ceiling_reachable: bool
    infeasibility_reason: str | None = None


class ScoreBreakdown(BaseModel):
    importance_contribution: float
    credit_contribution: float
    time_penalty: float
    travel_penalty: float
    total: float


class ScheduleCandidate(BaseModel):
    course_codes: list[str]
    used_credit: int
    total_score: float
    score_breakdown: ScoreBreakdown


class ValuationResult(BaseModel):
    top_k_candidates: list[ScheduleCandidate]
    num_total_feasible: int
    best_score: float
    k_threshold_score: float


class PairwiseDiff(BaseModel):
    rank_a: int
    rank_b: int
    common_backbone: list[str]
    only_in_a: list[str]
    only_in_b: list[str]


class CourseRationale(BaseModel):
    code: str
    included_in_ranks: list[int]
    excluded_reason: str | None = None


class SelectionResult(BaseModel):
    ranked_schedules: list[ScheduleCandidate]
    pairwise_diff: list[PairwiseDiff]
    course_rationale: list[CourseRationale]
    diversity_adjustment_applied: bool


class InfeasibilityReport(BaseModel):
    reason: str
    suggestions: list[str]


class TimetableResult(BaseModel):
    selection: SelectionResult | None = None
    infeasibility: InfeasibilityReport | None = None
