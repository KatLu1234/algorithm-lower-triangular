"""FeasibilityResult — A 가능성 분석의 출력, B 가치 평가의 입력.

알고리즘 트리 A → B 사이의 *유일한 계약*. A 단계의 세 자식(A-1·A-2·A-3)이
협력해 만든 결과를 하나의 데이터 패키지로 묶어 B 단계에 넘긴다.

권위 있는 출처: `claude/base/drafts/algorithm-tree.md` §9.6.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import (
    BuildingCode,
    Course,
    CourseId,
    InfeasibilityReport,
)


class FeasibilityResult(BaseModel):
    """A 가능성 분석의 정제 결과 + 다음 단계가 소비할 보조 자료.

    구성:
      • candidates                 — A-1에서 정제된 강의 풀
      • must_include_mask          — A-1에서 부착된 잠금 플래그
      • compatible                 — A-2 양립 가능성 (강의 쌍)
      • travel_time_table          — A-2에서 룩업·B-2에서 계산되는 건물 거리 표
      • ordered_by_start           — A-3의 시간 순 시퀀스 (B-3 DP의 행 순서)
      • credit_ceiling_reachable   — A-3 도달 가능성 검증 결과
      • infeasibility              — 조기 종료 사유 (있다면)

    `infeasibility != None` 이면 B·C는 실행되지 않고 응답 단계로 단락된다.
    """

    model_config = ConfigDict(frozen=True)

    candidates: list[Course] = Field(
        description="A-1·A-3 정제 후의 후보 강의 (입력 풀의 부분집합)",
    )
    must_include_mask: set[CourseId] = Field(
        default_factory=set,
        description="A-1에서 부착된 필수 잠금 플래그. B-3 DP의 강제 포함 마스크.",
    )
    compatible: dict[tuple[CourseId, CourseId], bool] = Field(
        default_factory=dict,
        description=(
            "강의 쌍 (i, j) → 양립 가능 여부. (i == j) 자기 자신은 포함하지 않음. "
            "키는 사전식 정렬한 튜플로 통일 (i < j)."
        ),
    )
    travel_time_table: dict[tuple[BuildingCode, BuildingCode], int] = Field(
        default_factory=dict,
        description=(
            "건물 쌍 → 최단 도보 분 (플로이드-워셜 산출). "
            "같은 건물은 0. 대칭 가정 — 한쪽 키로 충분하지만 양방향 등록 권장."
        ),
    )
    ordered_by_start: list[CourseId] = Field(
        default_factory=list,
        description="시간 순 강의 시퀀스 (B-3 행렬경로 DP가 소비). 빈 리스트면 미정렬.",
    )
    credit_ceiling_reachable: bool = Field(
        default=True,
        description="활동 선택으로 산출된 최대 부분집합이 사용자 학점 하한에 도달 가능한가",
    )
    infeasibility: Optional[InfeasibilityReport] = Field(
        default=None,
        description="조기 종료 신호. None 이면 B·C로 진행.",
    )

    # ── 편의 메서드 ──────────────────────────────────────────────
    def is_compatible(self, a: CourseId, b: CourseId) -> bool:
        """강의 쌍 (a, b) 양립 가능 여부. 키 순서 무관."""
        if a == b:
            return True
        i, j = sorted((a, b))
        return self.compatible.get((i, j), False)

    def travel_minutes(self, src: BuildingCode, dst: BuildingCode) -> int:
        """건물 src → dst 최단 도보 분. 없으면 매우 큰 값 (실질 unreachable).

        ⚠️ 키가 없으면 ``10_000`` 분을 반환해 *이동 불가*를 의미하게 만든다.
        호출자는 별도 검사 없이 비교에 사용 가능.
        """
        if src == dst:
            return 0
        # 정방향
        if (src, dst) in self.travel_time_table:
            return self.travel_time_table[(src, dst)]
        # 역방향 (대칭 가정)
        if (dst, src) in self.travel_time_table:
            return self.travel_time_table[(dst, src)]
        return 10_000

    @property
    def is_feasible(self) -> bool:
        """조기 종료 신호 없으면 True."""
        return self.infeasibility is None
