"""S-02 (λ₄ 시간창) + S-03 (λ₅ 하루 span) 테스트.

각 항은 ScoreBreakdown에 *전용 필드*로 잡힌다 (다른 항에 묻지 않음 — 설명 가능성).
기본값(λ=0 또는 창=하루 전체)에서는 0이라 기존 시간표 결과에 영향 없음(하위호환).
"""
import pytest

from app.libs.valuation import (
    _build_breakdown, _schedule_out_of_window_minutes,
    _schedule_total_daily_span_hours,
)
from app.libs.timetable import recommend
from app.schemas import (
    Category, Course, FeasibilityResult, PreferenceVector, SelectionResult,
    TimeSlot, Weekday,
)


def _c(cid: str, day: Weekday, start: int, end: int) -> Course:
    return Course(
        id=cid, name=cid, credit=3, category=Category.MAJOR,
        times=[TimeSlot(day=day, start_minute=start, end_minute=end, building="공학관")],
    )


def _multi(cid: str, slots: list[tuple[Weekday, int, int]]) -> Course:
    return Course(
        id=cid, name=cid, credit=3, category=Category.MAJOR,
        times=[TimeSlot(day=d, start_minute=s, end_minute=e, building="공학관")
               for d, s, e in slots],
    )


def _feas(courses: list[Course]) -> FeasibilityResult:
    """전부 호환 — _build_breakdown 단위 검증용 (travel/compat은 0)."""
    compat = {}
    for i, ci in enumerate(courses):
        for cj in courses[i + 1:]:
            compat[tuple(sorted((ci.id, cj.id)))] = True
    return FeasibilityResult(
        candidates=courses, must_include_mask=set(),
        compatible=compat, travel_time_table={},
        ordered_by_start=[c.id for c in courses],
        credit_ceiling_reachable=True, infeasibility=None,
    )


# ─── S-02 — _schedule_out_of_window_minutes ────────────────────────
class TestOutOfWindowMinutes:
    def test_all_inside_zero(self):
        c = _c("A", Weekday.MON, 540, 600)  # 09:00–10:00
        assert _schedule_out_of_window_minutes([c], 480, 1080) == 0  # 08:00–18:00

    def test_fully_outside_full_length(self):
        c = _c("A", Weekday.MON, 420, 480)  # 07:00–08:00
        # 창 09:00–18:00 밖 — 60분
        assert _schedule_out_of_window_minutes([c], 540, 1080) == 60

    def test_partial_overlap_only_outside_counted(self):
        c = _c("A", Weekday.MON, 510, 600)  # 08:30–10:00 (90분)
        # 창 09:00–18:00 — 30분(8:30~9:00) 밖
        assert _schedule_out_of_window_minutes([c], 540, 1080) == 30

    def test_default_full_day_zero(self):
        c = _c("A", Weekday.MON, 0, 1440)
        assert _schedule_out_of_window_minutes([c], 0, 1440) == 0


# ─── S-03 — _schedule_total_daily_span_hours ───────────────────────
class TestDailySpanHours:
    def test_single_slot_returns_slot_length(self):
        c = _c("A", Weekday.MON, 540, 600)  # 1시간
        assert _schedule_total_daily_span_hours([c]) == pytest.approx(1.0)

    def test_two_slots_same_day_span_endpoints(self):
        # 월요일 09:00–10:00 + 17:00–18:00 → span = 18:00 − 09:00 = 9h
        a = _c("A", Weekday.MON, 540, 600)
        b = _c("B", Weekday.MON, 1020, 1080)
        assert _schedule_total_daily_span_hours([a, b]) == pytest.approx(9.0)

    def test_multiple_days_sum(self):
        a = _c("A", Weekday.MON, 540, 600)  # 1h
        b = _c("B", Weekday.TUE, 540, 720)  # 3h
        assert _schedule_total_daily_span_hours([a, b]) == pytest.approx(4.0)


# ─── _build_breakdown 통합 — 전용 필드에 값이 잡히는지 ──────────────
class TestBreakdownFields:
    def _make_prefs(self, courses, **overrides) -> PreferenceVector:
        base = dict(courses=courses, credit_min=0, credit_max=18)
        base.update(overrides)
        return PreferenceVector(**base)

    def test_lambda_zero_default_no_penalty(self):
        pool = [_c("A", Weekday.MON, 420, 480)]  # 창 밖이어도 λ=0이면 0
        prefs = self._make_prefs(pool, preferred_start_minute=540, preferred_end_minute=1080)
        bd = _build_breakdown(pool, _feas(pool), prefs)
        assert bd.time_window_penalty == 0.0
        assert bd.daily_span_penalty == 0.0

    def test_time_window_penalty_negative_for_outside(self):
        pool = [_c("A", Weekday.MON, 420, 480)]  # 60분 창 밖
        prefs = self._make_prefs(
            pool, time_window_lambda=0.1,
            preferred_start_minute=540, preferred_end_minute=1080,
        )
        bd = _build_breakdown(pool, _feas(pool), prefs)
        assert bd.time_window_penalty == pytest.approx(-6.0)  # -0.1 * 60

    def test_daily_span_penalty_negative(self):
        # 월 09–10 + 월 17–18 → span 9h
        pool = [_c("A", Weekday.MON, 540, 600), _c("B", Weekday.MON, 1020, 1080)]
        prefs = self._make_prefs(pool, daily_span_lambda=0.2)
        bd = _build_breakdown(pool, _feas(pool), prefs)
        assert bd.daily_span_penalty == pytest.approx(-1.8)  # -0.2 * 9.0

    def test_total_includes_new_terms(self):
        pool = [_c("A", Weekday.MON, 420, 480)]
        prefs = self._make_prefs(
            pool,
            time_window_lambda=0.1, preferred_start_minute=540, preferred_end_minute=1080,
            daily_span_lambda=0.5,
        )
        bd = _build_breakdown(pool, _feas(pool), prefs)
        # core + time_window_penalty(-6) + daily_span_penalty(-0.5 * 1.0)
        expected = bd.core_importance + (-6.0) + (-0.5) + bd.category_weight + bd.building_penalty
        assert bd.total == pytest.approx(expected)


# ─── PreferenceVector 검증 ─────────────────────────────────────────
class TestPreferenceVectorValidation:
    def test_preferred_window_start_must_be_less_than_end(self):
        from pydantic import ValidationError
        pool = [_c("A", Weekday.MON, 540, 600)]
        with pytest.raises((ValidationError, ValueError), match="preferred_start_minute"):
            PreferenceVector(
                courses=pool, credit_min=0, credit_max=18,
                preferred_start_minute=600, preferred_end_minute=600,
            )

    def test_negative_lambda_rejected(self):
        from pydantic import ValidationError
        pool = [_c("A", Weekday.MON, 540, 600)]
        with pytest.raises((ValidationError, ValueError)):
            PreferenceVector(
                courses=pool, credit_min=0, credit_max=18,
                time_window_lambda=-0.1,
            )
        with pytest.raises((ValidationError, ValueError)):
            PreferenceVector(
                courses=pool, credit_min=0, credit_max=18,
                daily_span_lambda=-0.1,
            )


# ─── recommend() 통합 — λ₄·λ₅가 순위에 반영되는지 ─────────────────
class TestRecommendIntegration:
    def test_time_window_prefers_inside_courses(self):
        """이른 아침 강의 vs 늦은 아침 강의 — 창 09:00~18:00 선호 시 늦은 쪽이 상위."""
        pool = [
            _c("EARLY", Weekday.MON, 420, 480),   # 07:00–08:00 (창 밖)
            _c("LATE",  Weekday.MON, 600, 660),   # 10:00–11:00 (창 안)
        ]
        prefs = PreferenceVector(
            courses=pool, credit_min=3, credit_max=3,
            time_window_lambda=0.5,
            preferred_start_minute=540, preferred_end_minute=1080,
        )
        result = recommend(prefs, ["공학관"], [[0]], top_k=2)
        assert isinstance(result, SelectionResult)
        # 첫 후보는 LATE — 창 안이므로 페널티 0
        assert result.ranked_schedules[0].courses == ["LATE"]
        late_bd = result.ranked_schedules[0].score_breakdown
        early_bd = result.ranked_schedules[1].score_breakdown
        assert late_bd.time_window_penalty == 0.0
        assert early_bd.time_window_penalty < 0.0

    def test_daily_span_prefers_compact_day(self):
        """같은 학점이지만 한 강의는 long-span 다른 강의는 짧음 — λ₅로 짧은 쪽이 상위."""
        pool = [
            _multi("SPREAD", [(Weekday.MON, 540, 600), (Weekday.MON, 1020, 1080)]),  # span 9h
            _multi("TIGHT",  [(Weekday.TUE, 540, 600), (Weekday.TUE, 600, 660)]),    # span 2h
        ]
        prefs = PreferenceVector(
            courses=pool, credit_min=3, credit_max=3,
            daily_span_lambda=1.0,
        )
        result = recommend(prefs, ["공학관"], [[0]], top_k=2)
        assert isinstance(result, SelectionResult)
        assert result.ranked_schedules[0].courses == ["TIGHT"]
