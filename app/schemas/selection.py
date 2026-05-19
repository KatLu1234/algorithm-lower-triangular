"""SelectionResult — C 선택과 비교의 출력, 응답 단계의 입력.

LLM-B(설명 생성)가 컨텍스트로 받는 자료의 *최종 형태*. 알고리즘 트리의 모든
결정이 본 객체에 응축돼 있고, LLM-B는 본 객체를 자연어로 풀이만 한다.

권위 있는 출처: `claude/base/drafts/algorithm-tree.md` §9.6.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import CourseId
from .valuation import ScoredSchedule


class RationaleStatus(str, Enum):
    """강의가 결과에 들어갔는가 / 빠졌는가."""

    INCLUDED = "included"
    EXCLUDED = "excluded"


class StageCode(str, Enum):
    """C-3 사유 색인의 단계 코드.

    *어느 단계에서* 그 결정이 났는지를 추적하기 위한 enum. LLM-B가 사람 말로
    풀어줄 때 *"A-1 사용자 제외 목록에 있어 빠졌습니다"* 같은 메시지의 근거.
    """

    # 포함 사유
    A1_MUST_INCLUDE = "A-1.must_include"
    B3_SELECTED = "B-3.selected_by_DP"

    # A-1 단계 배제 사유
    A1_USER_EXCLUDED = "A-1.user_excluded"
    A1_DATA_INVALID = "A-1.data_invalid"
    A1_BLACKOUT_CONFLICT = "A-1.blackout_conflict"

    # A-2 단계 배제 사유
    A2_TIME_CONFLICT = "A-2.time_conflict"
    A2_TRAVEL_INFEASIBLE = "A-2.travel_infeasible"

    # A-3 단계 배제 사유
    A3_PRUNED = "A-3.pruned"

    # B-3 단계 배제 사유
    B3_SCORE_TOO_LOW = "B-3.score_too_low"
    B3_CREDIT_BUMPED = "B-3.credit_bumped"

    # 최종 단계
    C1_NOT_IN_TOP_N = "C-1.not_in_top_n"


class Rationale(BaseModel):
    """한 강의가 결과에 들어갔거나 빠진 이유 한 줄.

    LLM-B가 사람 말로 풀어줄 *모든* 메시지의 근거가 본 객체에서 온다.
    """

    model_config = ConfigDict(frozen=True)

    course_id: CourseId
    status: RationaleStatus
    stage_code: StageCode = Field(description="결정이 일어난 트리 단계")
    detail: str = Field(description="사람이 읽는 1줄 설명 (LLM-B 풀이의 시드)")
    related_course_ids: list[CourseId] = Field(
        default_factory=list,
        description="결정에 관여한 다른 강의들 (예: 시간 충돌 상대)",
    )
    score_contribution: Optional[float] = Field(
        default=None,
        description="포함된 강의의 v(c) 기여 (있을 때만)",
    )


class DiffInfo(BaseModel):
    """두 후보 시간표 간 공통·차이 (C-2 LCS 결과)."""

    model_config = ConfigDict(frozen=True)

    common: list[CourseId] = Field(description="두 시간표의 공통 강의 (백본)")
    only_in_left: list[CourseId] = Field(
        default_factory=list,
        description="왼쪽(상위) 시간표에만 있는 강의",
    )
    only_in_right: list[CourseId] = Field(
        default_factory=list,
        description="오른쪽 시간표에만 있는 강의",
    )
    edit_distance: Optional[int] = Field(
        default=None,
        description="(옵션) 두 시간표 간 편집 거리. 미산출 시 None.",
    )


class SelectionResult(BaseModel):
    """C → 응답 (LLM-B) 인계 패키지.

    구성:
      • ranked_schedules               — 최종 사용자 응답에 들어갈 상위 N개 (정렬 확정)
      • pairwise_diff                  — (i, j) 순위 쌍별 LCS 비교 결과
      • course_rationale               — 강의 ID → Rationale 색인
      • diversity_adjustment_applied   — C-1 다양성 후처리 발동 여부
      • notes                          — 사용자에게 노출할 추가 메모 (옵션)
    """

    model_config = ConfigDict(frozen=True)

    ranked_schedules: list[ScoredSchedule] = Field(
        description="N개 (다양성 후처리 후 확정 순서)",
    )
    pairwise_diff: dict[tuple[int, int], DiffInfo] = Field(
        default_factory=dict,
        description="(i, j) 순위 쌍 → 공통/차이. i < j 권장.",
    )
    course_rationale: dict[CourseId, Rationale] = Field(
        default_factory=dict,
        description="후보 풀의 모든 강의 ID → 사유. LLM-B 풀이의 단일 진실 출처.",
    )
    diversity_adjustment_applied: bool = Field(
        default=False,
        description="C-1 다양성 5% 양보가 적용됐는가",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="사용자에게 노출할 추가 메모 (예: '학점 한도가 빠듯해 X를 추천')",
    )

    @property
    def top_count(self) -> int:
        """최종 표시 시간표 개수."""
        return len(self.ranked_schedules)

    def rationale_for(self, course_id: CourseId) -> Optional[Rationale]:
        """편의 — 강의 ID 룩업."""
        return self.course_rationale.get(course_id)
