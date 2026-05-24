"""공유 도메인 타입.

알고리즘 트리 A·B·C와 PreferenceVector / FeasibilityResult / ValuationResult /
SelectionResult 4개 계약 모두가 공유하는 기본 타입을 모아둔다.

권위 있는 출처: `claude/base/drafts/algorithm-tree.md` §9.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

CourseId = str
"""강의 코드 (예: 'CS101-01-홍교수')."""

BuildingCode = str
"""건물 코드 (예: '공학관')."""

CourseGroupId = str
"""과목 그룹 ID — 같은 과목의 분반들을 묶는 키 (예: 'CS101').

같은 group_id를 공유하는 강의들은 *상호 배타* — 시간표에 그룹당 최대 1개만 선택됨.
"""


class Weekday(str, Enum):
    """요일. 문자열 enum."""

    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class Category(str, Enum):
    """강의 카테고리 (학문 영역 분류)."""

    MAJOR = "전공"
    DOUBLE_MAJOR = "복수전공"
    LIBERAL = "교양"
    GENERAL = "일선"


class Requirement(str, Enum):
    """이수 요건 분류 — Category와 직교하는 두 번째 차원.

    옵셔널 — 미지정 시 None. 가중치 0으로 처리.
    """

    REQUIRED = "필수"
    ELECTIVE = "선택"
    OPTIONAL = "자율"


class TimeSlot(BaseModel):
    """한 강의의 한 요일·시간 구간.

    `building`은 *슬롯 단위 override*. None이면 호출자가 Course.building을 기본으로 사용.
    같은 강의가 요일마다 다른 건물(예: 월 본관 강의 / 수 공학관 실습)을 쓰는 경우에만 채움.
    """

    model_config = ConfigDict(frozen=True)

    day: Weekday
    start_minute: int = Field(ge=0, lt=24 * 60, description="자정 기준 분 (0–1439)")
    end_minute: int = Field(ge=1, le=24 * 60, description="자정 기준 분 (1–1440)")
    building: Optional["BuildingCode"] = Field(
        default=None,
        description=(
            "슬롯 단위 건물 override. None이면 Course.building 사용. "
            "A-2 이동시간 검사·B-3 travel_penalty가 이 값을 우선 사용."
        ),
    )

    @model_validator(mode="after")
    def _check_order(self) -> "TimeSlot":
        if self.start_minute >= self.end_minute:
            raise ValueError(
                f"TimeSlot: start_minute({self.start_minute}) "
                f"must be < end_minute({self.end_minute})"
            )
        return self

    def overlaps(self, other: "TimeSlot") -> bool:
        """두 TimeSlot이 같은 요일에 시간 겹침이 있으면 True."""
        if self.day != other.day:
            return False
        return self.start_minute < other.end_minute and other.start_minute < self.end_minute

    def resolve_building(self, course_default: "BuildingCode") -> "BuildingCode":
        """슬롯 override 우선, 없으면 호출자가 넘긴 Course.building."""
        return self.building if self.building is not None else course_default


class BlackoutWindow(BaseModel):
    """사용자가 *절대 불가*로 표시한 시간대 (외부 일정·통학·알바 등)."""

    model_config = ConfigDict(frozen=True)

    days: list[Weekday] = Field(min_length=1, description="적용되는 요일 목록")
    start_minute: int = Field(ge=0, lt=24 * 60)
    end_minute: int = Field(ge=1, le=24 * 60)
    reason: Optional[str] = Field(default=None, description="사용자 표기 사유 (예: '통학')")

    @model_validator(mode="after")
    def _check_order(self) -> "BlackoutWindow":
        if self.start_minute >= self.end_minute:
            raise ValueError(
                f"BlackoutWindow: start_minute({self.start_minute}) "
                f"must be < end_minute({self.end_minute})"
            )
        return self

    def overlaps_slot(self, slot: TimeSlot) -> bool:
        """주어진 TimeSlot이 본 blackout과 겹치면 True (부분 겹침도 True)."""
        if slot.day not in self.days:
            return False
        return slot.start_minute < self.end_minute and self.start_minute < slot.end_minute


class Course(BaseModel):
    """한 강의(분반)의 메타데이터.

    같은 *과목*의 다른 분반들은 서로 다른 `id`를 가지되 *같은 `course_group_id`*를
    공유한다. A-2가 그룹 동일성을 양립 불가 조건으로 적용해 그룹당 최대 1개 선택.
    """

    model_config = ConfigDict(frozen=True)

    id: CourseId
    name: str
    times: list[TimeSlot] = Field(min_length=1, description="강의가 열리는 모든 시간대")
    credit: int = Field(ge=1, description="학점 (양수)")
    building: BuildingCode
    category: Category
    requirement: Optional[Requirement] = Field(
        default=None,
        description="이수 요건 (필수/선택/자율). 옵셔널.",
    )

    # ── 분반·교수 (옵셔널) ────────────────────────────────────────
    course_group_id: Optional[CourseGroupId] = Field(
        default=None,
        description=(
            "같은 과목의 분반들을 묶는 그룹 ID. 같은 값 공유 강의는 *상호 배타* — "
            "그룹당 최대 1개만 시간표에 선택됨. None 이면 그룹 없음 (단독 강의)."
        ),
    )
    section: Optional[str] = Field(
        default=None,
        description="분반 표시 라벨 (예: 'A반', '01'). 표시용 — 알고리즘은 course_group_id로 판정.",
    )
    professor: Optional[str] = Field(
        default=None,
        description="담당 교수 이름. 표시용 + (선택) professor_preferences 룩업 키.",
    )


class InfeasibilityReason(str, Enum):
    """알고리즘 트리가 진단할 수 있는 불가능 사유 코드."""

    # A-1
    USER_CONTRADICTION = "user_contradiction"
    MUST_INCLUDE_INVALID = "must_include_invalid"
    MUST_INCLUDE_BLACKOUT_CONFLICT = "must_include_blackout_conflict"
    EMPTY_POOL = "empty_pool"
    MUST_INCLUDE_GROUP_EMPTY = "must_include_group_empty"
    """must_include_groups의 그룹에 정제 후 후보가 0개."""

    # A-2
    MUST_INCLUDE_PAIR_CONFLICT = "must_include_pair_conflict"
    GROUP_PAIR_CONFLICT = "group_pair_conflict"
    """두 must_include_groups의 어떤 분반 조합도 시간·이동 양립 불가."""

    # A-3
    CREDIT_CEILING_UNREACHABLE = "credit_ceiling_unreachable"


class InfeasibilityReport(BaseModel):
    """알고리즘 트리의 *조기 종료* 신호."""

    model_config = ConfigDict(frozen=True)

    reason: InfeasibilityReason
    stage: str = Field(description="검출 단계 코드 (예: 'A-1', 'A-2', 'A-3')")
    detail: str = Field(description="사람이 읽는 1–2줄 진단")
    resolution_hint: Optional[str] = Field(
        default=None,
        description="어느 제약을 풀면 가능한지 안내",
    )
    offending_course_ids: list[CourseId] = Field(
        default_factory=list,
        description="원인이 되는 강의 ID 목록",
    )
    offending_group_ids: list[CourseGroupId] = Field(
        default_factory=list,
        description="원인이 되는 과목 그룹 ID 목록 (그룹 단위 infeasibility 시)",
    )
