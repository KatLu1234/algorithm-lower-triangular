"""recommend() 빈 결과 진단 정밀화 테스트.

회귀 케이스: A-3 `_check_credit_reach`는 요일별 activity selection으로 도달 학점을
과대평가하므로 feasibility는 통과해도 valuation 백트래킹이 모두 reject되어 빈
결과가 나올 수 있다. 이때 `_max_reachable_credit_under_compat`이 호환 행렬 기반
실제 최대 학점을 계산해 정확한 진단을 제공한다.
"""
import pytest

from app.libs.timetable import (
    _empty_result_diagnosis,
    _max_reachable_credit_under_compat,
    recommend,
)
from app.schemas import (
    Category, Course, FeasibilityResult, InfeasibilityReport,
    PreferenceVector, TimeSlot, Weekday,
)


def _c(cid: str, day: Weekday, start: int, end: int, credit: int,
       cat: Category = Category.MAJOR, building: str = "공학관") -> Course:
    return Course(
        id=cid, name=cid, credit=credit, category=cat,
        times=[TimeSlot(day=day, start_minute=start, end_minute=end, building=building)],
    )


def _feas(courses: list[Course], conflicts: set[tuple[str, str]] = frozenset(),
          must: set[str] = frozenset()) -> FeasibilityResult:
    """수동 합성 — conflicts에 든 정렬된 (a,b) 쌍만 False, 나머지 True."""
    compat: dict[tuple[str, str], bool] = {}
    for i, ci in enumerate(courses):
        for cj in courses[i + 1:]:
            key = tuple(sorted((ci.id, cj.id)))
            compat[key] = key not in conflicts  # type: ignore[assignment]
    return FeasibilityResult(
        candidates=courses, must_include_mask=set(must),
        compatible=compat, travel_time_table={},
        ordered_by_start=[c.id for c in courses],
        credit_ceiling_reachable=True, infeasibility=None,
    )


class TestMaxReachableCreditUnderCompat:
    def test_no_conflicts_returns_full_sum(self):
        pool = [_c("A", Weekday.MON, 540, 590, 3),
                _c("B", Weekday.TUE, 540, 590, 3),
                _c("C", Weekday.WED, 540, 590, 3)]
        feas = _feas(pool)
        prefs = PreferenceVector(courses=pool, credit_min=0, credit_max=12)
        assert _max_reachable_credit_under_compat(feas, prefs) == 9

    def test_pair_conflict_caps_credit(self):
        """A↔B 충돌 — 둘 다 못 가짐. {A,C}=6 또는 {B,C}=6 → 최대 6."""
        pool = [_c("A", Weekday.MON, 540, 590, 3),
                _c("B", Weekday.MON, 540, 590, 3),
                _c("C", Weekday.TUE, 540, 590, 3)]
        feas = _feas(pool, conflicts={("A", "B")})
        prefs = PreferenceVector(courses=pool, credit_min=0, credit_max=12)
        assert _max_reachable_credit_under_compat(feas, prefs) == 6

    def test_credit_max_caps(self):
        """A=3, B=3, C=3, max=5 — 한 강의(3)만 넣을 수 있다."""
        pool = [_c("A", Weekday.MON, 540, 590, 3),
                _c("B", Weekday.TUE, 540, 590, 3),
                _c("C", Weekday.WED, 540, 590, 3)]
        feas = _feas(pool)
        prefs = PreferenceVector(courses=pool, credit_min=0, credit_max=5)
        assert _max_reachable_credit_under_compat(feas, prefs) == 3

    def test_must_include_locks_in(self):
        """must={A} — A는 무조건 포함. {A,B}=6 가능 ({A,C}=6도 가능)."""
        pool = [_c("A", Weekday.MON, 540, 590, 3),
                _c("B", Weekday.TUE, 540, 590, 3),
                _c("C", Weekday.WED, 540, 590, 3)]
        feas = _feas(pool, must={"A"})
        prefs = PreferenceVector(courses=pool, credit_min=0, credit_max=12,
                                 must_include={"A"})
        assert _max_reachable_credit_under_compat(feas, prefs) == 9


class TestEmptyResultDiagnosis:
    def test_credit_min_unreachable_message(self):
        """양립 최대 6학점 < credit_min 9 — 학점 하한 인하 안내."""
        pool = [_c("A", Weekday.MON, 540, 590, 3),
                _c("B", Weekday.MON, 540, 590, 3),
                _c("C", Weekday.TUE, 540, 590, 3)]
        feas = _feas(pool, conflicts={("A", "B")})
        prefs = PreferenceVector(courses=pool, credit_min=9, credit_max=12)
        report = _empty_result_diagnosis(feas, prefs)
        assert isinstance(report, InfeasibilityReport)
        assert "최대 학점 합은 6학점" in report.detail
        assert "하한 9학점에 미달" in report.detail
        assert "6학점 이하로 낮추거나" in (report.resolution_hint or "")

    def test_other_constraint_when_credit_reachable(self):
        """학점은 충족 가능한데 category_count_min이 막은 경우."""
        pool = [_c("A", Weekday.MON, 540, 590, 3, Category.MAJOR),
                _c("B", Weekday.TUE, 540, 590, 3, Category.MAJOR),
                _c("C", Weekday.WED, 540, 590, 3, Category.MAJOR)]
        feas = _feas(pool)
        # 학점은 9까지 도달 가능하지만 LIBERAL을 1개 요구 — 풀에 LIBERAL 없음
        prefs = PreferenceVector(
            courses=pool, credit_min=3, credit_max=12,
            category_count_min={Category.LIBERAL: 1},
        )
        report = _empty_result_diagnosis(feas, prefs)
        assert "학점 한도는 충족 가능" in report.detail
        assert "category_count_min" in report.detail


class TestRecommendIntegration:
    """recommend() 루트 — 빈 결과 시 정확한 진단을 받는지 end-to-end.

    재현 조건: A-3 요일별 activity_selection은 학점 도달 가능으로 보지만
    A-2 호환 행렬(여기서는 course_group_id 공유 = 상호 배타)이 막아 valuation
    백트래킹이 모두 reject되는 경우. 이때 새 _empty_result_diagnosis가 호출되어
    "양립 최대 X학점 < 하한 Y" 형식의 정확한 진단을 만들어야 한다.
    """

    def test_group_conflict_credit_shortfall(self):
        """OS-A·OS-B는 같은 group_id로 상호 배타. 다른 요일에 두어 A-3는 통과시킨다."""
        pool = [
            _c("ALG", Weekday.MON, 540, 590, 3),
            Course(
                id="OS-A", name="OS-A", credit=3, category=Category.MAJOR,
                course_group_id="OS",
                times=[TimeSlot(day=Weekday.TUE, start_minute=540, end_minute=590, building="공학관")],
            ),
            Course(
                id="OS-B", name="OS-B", credit=3, category=Category.MAJOR,
                course_group_id="OS",
                times=[TimeSlot(day=Weekday.WED, start_minute=540, end_minute=590, building="공학관")],
            ),
        ]
        prefs = PreferenceVector(
            courses=pool, credit_min=9, credit_max=18,
            must_include={"ALG"},
        )
        outcome = recommend(prefs, building_codes=["공학관"],
                            base_walk_minutes=[[0]], top_k=3)
        assert isinstance(outcome, InfeasibilityReport)
        assert outcome.stage == "B-3", f"기대 B-3 진단, 실제 {outcome.stage}"
        assert "최대 학점 합은 6학점" in outcome.detail
        assert "하한 9학점에 미달" in outcome.detail
        assert outcome.resolution_hint is not None
        assert "6학점 이하로 낮추거나" in outcome.resolution_hint
