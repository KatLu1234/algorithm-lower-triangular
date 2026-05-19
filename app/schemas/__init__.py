"""Pydantic 스키마 — 알고리즘 트리의 입출력 계약과 기본 자료형.

권위 있는 출처: `claude/base/drafts/algorithm-tree.md` §9.6.
"""

# 기존 샘플 스키마 (sample item — 골격 단계 잔존, 추후 제거 가능)
from .item import Item, ItemCreate, ItemUpdate
from .msg import Msg

# 공유 도메인 타입
from .common import (
    BlackoutWindow,
    BuildingCode,
    Category,
    Course,
    CourseId,
    InfeasibilityReason,
    InfeasibilityReport,
    Requirement,
    TimeSlot,
    Weekday,
)

# 알고리즘 트리 4개 계약
from .preferences import PreferenceVector
from .feasibility import FeasibilityResult
from .valuation import ScoreBreakdown, ScoredSchedule, ValuationResult
from .selection import (
    DiffInfo,
    Rationale,
    RationaleStatus,
    SelectionResult,
    StageCode,
)

__all__ = [
    "Item",
    "ItemCreate",
    "ItemUpdate",
    "Msg",
    "BlackoutWindow",
    "BuildingCode",
    "Category",
    "Course",
    "CourseId",
    "InfeasibilityReason",
    "InfeasibilityReport",
    "Requirement",
    "TimeSlot",
    "Weekday",
    "PreferenceVector",
    "FeasibilityResult",
    "ScoreBreakdown",
    "ScoredSchedule",
    "ValuationResult",
    "DiffInfo",
    "Rationale",
    "RationaleStatus",
    "SelectionResult",
    "StageCode",
]
