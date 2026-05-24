import pytest
from pydantic import ValidationError
from app.schemas import (
    Course, TimeSlot, Weekday, Category, Requirement,
    PreferenceVector,
)


class TestTimeSlot:
    def test_overlap_same_day(self):
        a = TimeSlot(day=Weekday.MON, start_minute=600, end_minute=720)
        b = TimeSlot(day=Weekday.MON, start_minute=660, end_minute=780)
        assert a.overlaps(b)
        assert b.overlaps(a)

    def test_no_overlap_different_day(self):
        a = TimeSlot(day=Weekday.MON, start_minute=600, end_minute=720)
        b = TimeSlot(day=Weekday.TUE, start_minute=600, end_minute=720)
        assert not a.overlaps(b)

    def test_rejects_reverse_time(self):
        with pytest.raises(ValidationError):
            TimeSlot(day=Weekday.MON, start_minute=720, end_minute=600)

    def test_resolve_building_default(self):
        s = TimeSlot(day=Weekday.MON, start_minute=540, end_minute=600)
        assert s.building is None
        assert s.resolve_building("공학관") == "공학관"

    def test_resolve_building_override(self):
        s = TimeSlot(day=Weekday.MON, start_minute=540, end_minute=600, building="본관")
        assert s.resolve_building("공학관") == "본관"


class TestPreferenceVector:
    def test_minji_scenario_constructs(self, minji_pv):
        assert len(minji_pv.courses) >= 4
        assert "ALG101" in minji_pv.must_include

    def test_importance_of_default(self, minji_pv):
        # 미지정 강의는 기본 3
        assert minji_pv.importance_of("PHL101") == 3

    def test_requirement_weight_none(self, minji_pv):
        # None → 0
        assert minji_pv.requirement_weight(None) == 0.0

    def test_requirement_weight_required(self, minji_pv):
        assert minji_pv.requirement_weight(Requirement.REQUIRED) == 1.5

    def test_credit_min_exceeds_max(self, minji_courses):
        with pytest.raises((ValidationError, ValueError)):
            PreferenceVector(courses=minji_courses, credit_min=20, credit_max=15)

    def test_importance_out_of_range(self, minji_courses):
        with pytest.raises((ValidationError, ValueError)):
            PreferenceVector(
                courses=minji_courses, credit_min=3, credit_max=18,
                course_importance={"ALG101": 6},
            )

    def test_unknown_course_id_in_exclude(self, minji_courses):
        with pytest.raises((ValidationError, ValueError)):
            PreferenceVector(
                courses=minji_courses, credit_min=3, credit_max=18,
                exclude={"NONEXISTENT"},
            )

    def test_json_roundtrip(self, minji_pv):
        json_str = minji_pv.model_dump_json()
        restored = PreferenceVector.model_validate_json(json_str)
        assert minji_pv == restored