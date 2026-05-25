"""기능2 — 수업 사이 최소 쉬는 시간(min_break_minutes) A-2 하드 제약 테스트."""
from app.libs.feasibility import build_compatibility
from app.schemas import Course, TimeSlot, Weekday, Category


def _course(cid: str, day: Weekday, start: int, end: int, building: str = "공학관") -> Course:
    return Course(
        id=cid, name=cid, credit=3, category=Category.MAJOR,
        times=[TimeSlot(day=day, start_minute=start, end_minute=end, building=building)],
    )


class TestMinBreak:
    def test_zero_break_keeps_legacy_behavior(self):
        # 같은 날 간격 10분(10:50 종료 → 11:00 시작), 같은 건물(이동 0)
        a = _course("A", Weekday.MON, 600, 650)
        b = _course("B", Weekday.MON, 660, 710)
        compat = build_compatibility([a, b], {}, 0)
        assert compat[("A", "B")] is True  # 기존 동작: 겹치지 않으면 양립

    def test_break_shortfall_makes_incompatible(self):
        a = _course("A", Weekday.MON, 600, 650)
        b = _course("B", Weekday.MON, 660, 710)  # 간격 10분
        compat = build_compatibility([a, b], {}, 15)  # 15분 요구 > 10분
        assert compat[("A", "B")] is False

    def test_break_boundary_exact_is_ok(self):
        a = _course("A", Weekday.MON, 600, 650)
        b = _course("B", Weekday.MON, 660, 710)  # 간격 10분
        compat = build_compatibility([a, b], {}, 10)  # 정확히 10분 = 허용
        assert compat[("A", "B")] is True

    def test_travel_dominates_when_larger(self):
        # 다른 건물 travel=20 > min_break=15, 간격 10분 → required=20 > 10 → 불가
        a = _course("A", Weekday.MON, 600, 650, building="공학관")
        b = _course("B", Weekday.MON, 660, 710, building="본관")
        table = {("공학관", "본관"): 20, ("본관", "공학관"): 20}
        compat = build_compatibility([a, b], table, 15)
        assert compat[("A", "B")] is False

    def test_different_days_unaffected(self):
        a = _course("A", Weekday.MON, 600, 650)
        c = _course("C", Weekday.TUE, 660, 710)
        compat = build_compatibility([a, c], {}, 120)  # 큰 min_break도 요일 다르면 무관
        assert compat[("A", "C")] is True
