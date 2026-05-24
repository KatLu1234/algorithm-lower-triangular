"""time_room 파서 & CSV 로더 단위 테스트.

교시 매핑: 1교시 = 09:00–10:00, n교시 = (n+8):00 – (n+9):00.
"""
from pathlib import Path

import pytest

from app.libs.timeroom_parser import (
    load_courses_from_csv,
    parse_time_room,
    row_to_course,
)
from app.schemas import Category, Requirement, Weekday


class TestParseTimeRoom:
    def test_empty_returns_empty(self):
        assert parse_time_room("") == []
        assert parse_time_room(None) == []
        assert parse_time_room("   ") == []

    def test_single_slot_range(self):
        slots = parse_time_room("화(6-8) 석원경상관 112호")
        assert len(slots) == 1
        s = slots[0]
        assert s.day == Weekday.TUE
        # 6교시 = 14:00, 8교시 끝 = 17:00
        assert s.start_minute == 14 * 60
        assert s.end_minute == 17 * 60
        assert s.building == "석원경상관"

    def test_single_slot_single_period(self):
        slots = parse_time_room("금(5) 과학기술2관 324호")
        assert len(slots) == 1
        s = slots[0]
        # 5교시 = 13:00–14:00
        assert s.start_minute == 13 * 60
        assert s.end_minute == 14 * 60

    def test_multiple_slots_separated_by_br(self):
        slots = parse_time_room("수(2-3) 과학기술2관 324호<br> 금(5) 과학기술2관 324호")
        assert len(slots) == 2
        assert slots[0].day == Weekday.WED
        assert slots[0].start_minute == 10 * 60  # 2교시
        assert slots[0].end_minute == 12 * 60    # 3교시 끝
        assert slots[1].day == Weekday.FRI
        assert slots[1].start_minute == 13 * 60

    def test_period_1_starts_at_9(self):
        slots = parse_time_room("월(1) 공학관 101호")
        assert slots[0].start_minute == 9 * 60
        assert slots[0].end_minute == 10 * 60

    def test_each_slot_has_building(self):
        slots = parse_time_room("월(2) 본관 101호<br>수(3) 공학관 202호")
        assert slots[0].building == "본관"
        assert slots[1].building == "공학관"

    def test_malformed_chip_skipped(self):
        slots = parse_time_room("garbage<br>화(6-8) 석원경상관 112호")
        assert len(slots) == 1
        assert slots[0].day == Weekday.TUE


class TestRowToCourse:
    def _row(self, **overrides):
        base = {
            "cour_cd": "DCSS201", "cour_cls": "01", "params": "DCSS201@01",
            "cour_nm": "자료구조", "isu_nm": "전공필수", "credit": "3",
            "prof_nm": "정인정", "time_room": "수(2-3) 과학기술2관 324호",
        }
        base.update(overrides)
        return base

    def test_basic(self):
        c = row_to_course(self._row())
        assert c is not None
        assert c.id == "DCSS201@01"
        assert c.name == "자료구조"
        assert c.category == Category.MAJOR
        assert c.requirement == Requirement.REQUIRED
        assert c.course_group_id == "DCSS201"
        assert c.section == "01"
        assert c.professor == "정인정"
        assert c.building == "과학기술2관"  # 첫 슬롯 건물

    def test_empty_time_room_returns_none(self):
        assert row_to_course(self._row(time_room="")) is None

    def test_zero_credit_returns_none(self):
        assert row_to_course(self._row(credit="0")) is None

    def test_elective_category(self):
        c = row_to_course(self._row(isu_nm="전공선택"))
        assert c is not None
        assert c.category == Category.MAJOR
        assert c.requirement == Requirement.ELECTIVE


class TestLoadCoursesFromCsv:
    """sample_data.csv 자체로 로드해 본다 — 워크트리 환경에서만 의미 있음."""

    def test_loads_real_sample(self):
        csv_path = Path(__file__).resolve().parents[1] / "sample_data.csv"
        if not csv_path.exists():
            pytest.skip("sample_data.csv 없음 (별도 환경)")
        courses = load_courses_from_csv(csv_path)
        # 모두 시간 있는 강의 + 학점 > 0
        assert len(courses) > 0
        assert all(c.times for c in courses)
        assert all(c.credit >= 1 for c in courses)
        # 같은 cour_cd 분반은 같은 group_id
        groups = {c.course_group_id for c in courses}
        assert "DCSS201" in groups  # 자료구조
