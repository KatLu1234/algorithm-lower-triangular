"""ValuationResult — B 가치 평가의 출력, C 선택과 비교의 입력.

알고리즘 트리 B → C 사이의 *유일한 계약*. B-3 DP가 산출한 top-K 후보 시간표
각각의 점수와 점수 분해를 담는다. C 단계는 본 결과만 보고 정렬·비교·사유 색인을
만든다.

권위 있는 출처: `claude/base/drafts/algorithm-tree.md` §9.6.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .common import CourseId


class ScoreBreakdown(BaseModel):
    """한 후보 시간표의 점수 분해.

    LLM-B가 사람 말로 풀어줄 때 *어느 항이 어느만큼 기여*했는지 보여주기 위해
    분해된 형태로 유지한다 (`product.md` §4-2 설명 가능성 1순위).

    합산 규칙:
        total = core_importance
              + time_penalty
              + building_penalty
              + category_weight
              + travel_penalty
              + compactness_penalty
              + diversity_penalty
              + back_to_back_term
              + time_window_penalty   ← S-02 (λ₄)
              + daily_span_penalty    ← S-03 (λ₅)

    페널티 항은 *부호를 그대로* 들고 있으므로 보통 음수다 (∴ 합산은 그냥 +).
    """

    model_config = ConfigDict(frozen=True)

    core_importance: float = Field(
        description="Σ_c (중요도(c) × 학점(c)) — 핵심 점수",
    )
    time_penalty: float = Field(
        default=0.0,
        description="Σ_c 시간대 페널티(c) — 보통 ≤ 0",
    )
    building_penalty: float = Field(
        default=0.0,
        description="Σ_c 건물 페널티(c) — 부호 사용자 정의",
    )
    category_weight: float = Field(
        default=0.0,
        description="Σ_c 카테고리 가중치(c) — 보통 ≥ 0",
    )
    travel_penalty: float = Field(
        default=0.0,
        description="−λ₁ · 총 이동 시간(S) — 보통 ≤ 0",
    )
    compactness_penalty: float = Field(
        default=0.0,
        description="−λ₂ · (활성 요일 수 − 목표) — 보통 ≤ 0",
    )
    diversity_penalty: float = Field(
        default=0.0,
        description="−λ₃ · 방문 건물 수 — 보통 ≤ 0",
    )
    back_to_back_term: float = Field(
        default=0.0,
        description="연강/공강 선호 항 (사용자 부호)",
    )
    time_window_penalty: float = Field(
        default=0.0,
        description=(
            "−λ₄ · 선호 시간창[preferred_start, preferred_end] *밖*에 놓인 슬롯 분 합 — 보통 ≤ 0. "
            "λ₄(time_window_lambda)=0 또는 창=하루 전체이면 0."
        ),
    )
    daily_span_penalty: float = Field(
        default=0.0,
        description=(
            "−λ₅ · 요일별 (마지막 종료 − 첫 시작) 시간(시간 단위) 합 — 보통 ≤ 0. "
            "λ₅(daily_span_lambda)=0이면 0."
        ),
    )

    @property
    def total(self) -> float:
        """모든 항을 합한 총 점수."""
        return (
            self.core_importance
            + self.time_penalty
            + self.building_penalty
            + self.category_weight
            + self.travel_penalty
            + self.compactness_penalty
            + self.diversity_penalty
            + self.back_to_back_term
            + self.time_window_penalty
            + self.daily_span_penalty
        )


class ScoredSchedule(BaseModel):
    """한 후보 시간표 — 강의 집합 + 점수.

    ``courses`` 는 *순서가 의미 없는 집합* 이지만, B-3가 시간 순으로 정렬해
    넘기는 편이 LLM 응답·UI 표시 모두에서 편하므로 시간 순 시퀀스로 기대한다.
    """

    model_config = ConfigDict(frozen=True)

    courses: list[CourseId] = Field(
        description="선택된 강의 ID들. 보통 시작 시간 순으로 정렬됨.",
    )
    used_credit: int = Field(ge=0, description="학점 합")
    score_breakdown: ScoreBreakdown

    @property
    def total_score(self) -> float:
        """편의 — ``score_breakdown.total`` 와 동일."""
        return self.score_breakdown.total


class ValuationResult(BaseModel):
    """B → C 인계 패키지.

    top-K 후보 시간표 + 통계. C-1 정렬·동률 처리가 이 입력을 받아 사용자에게
    보여줄 N개를 골라낸다 (K ≥ N).
    """

    model_config = ConfigDict(frozen=True)

    top_k_candidates: list[ScoredSchedule] = Field(
        description="DP 백트래킹으로 추출한 top-K 후보. 점수 내림차순 권장.",
    )
    num_total_feasible: int = Field(
        ge=0,
        description="가지치기 후 가능한 시간표 총 개수 (사용자 안내 용도)",
    )
    best_score: float = Field(description="top-K 중 최고 점수")
    k_threshold_score: float = Field(description="top-K 중 최하 점수 (다양성 후처리 기준)")

    @property
    def is_empty(self) -> bool:
        """후보가 0개면 True (C에서 빈 상태 응답 분기)."""
        return len(self.top_k_candidates) == 0
