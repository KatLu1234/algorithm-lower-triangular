"""LLM-A delta 안전 병합 단위 테스트.

`_merge_delta`는 LLM이 준 JSON delta를 PreferenceVector에 *안전하게* 합쳐야 한다.
주요 불변항 (product.md §4.4):
  - 화이트리스트 외 키는 silently 무시 (warnings에 기록)
  - 기존 must_include/exclude/groups를 LLM이 임의로 비울 수 없음 (합집합)
  - 검증 실패 시 원본 유지 + 경고
"""
import pytest

from app.api.endpoints.timetable import _merge_delta
from app.schemas import Category, Course, PreferenceVector, Requirement, TimeSlot, Weekday


@pytest.fixture
def base_pv() -> PreferenceVector:
    courses = [
        Course(id="A", name="알고리즘", credit=3, building="공학관",
               category=Category.MAJOR, requirement=Requirement.REQUIRED,
               course_group_id="ALG",
               times=[TimeSlot(day=Weekday.MON, start_minute=540, end_minute=600)]),
        Course(id="B", name="자료구조", credit=3, building="본관",
               category=Category.MAJOR, requirement=Requirement.REQUIRED,
               course_group_id="DS",
               times=[TimeSlot(day=Weekday.TUE, start_minute=540, end_minute=600)]),
    ]
    return PreferenceVector(
        courses=courses, credit_min=3, credit_max=12,
        must_include={"A"},
    )


class TestMergeDelta:
    def test_unknown_key_dropped(self, base_pv):
        merged, warns = _merge_delta(base_pv, {"foo": 123, "credit_max": 15}, base_pv.courses)
        assert merged.credit_max == 15
        assert any("foo" in w for w in warns)

    def test_must_include_union_preserves_existing(self, base_pv):
        # LLM이 must_include를 ['B']로만 주면 사용자가 박은 'A'가 사라지면 안 됨
        merged, _ = _merge_delta(base_pv, {"must_include": ["B"]}, base_pv.courses)
        assert merged.must_include == {"A", "B"}

    def test_must_include_invalid_id_dropped(self, base_pv):
        merged, _ = _merge_delta(base_pv, {"must_include": ["NONEXISTENT", "B"]}, base_pv.courses)
        assert "B" in merged.must_include
        assert "NONEXISTENT" not in merged.must_include

    def test_blackout_windows_append(self, base_pv):
        before = len(base_pv.blackout_windows)
        delta = {"blackout_windows": [
            {"days": ["FRI"], "start_minute": 0, "end_minute": 1440, "reason": "통학"}
        ]}
        merged, _ = _merge_delta(base_pv, delta, base_pv.courses)
        assert len(merged.blackout_windows) == before + 1

    def test_blackout_windows_dedup_same_window_twice(self, base_pv):
        """같은 (days, start, end) 조합을 두 번 보내도 한 번만 보존 — 누적 방지."""
        delta = {"blackout_windows": [
            {"days": ["FRI"], "start_minute": 780, "end_minute": 1080, "reason": "통학"},
            {"days": ["FRI"], "start_minute": 780, "end_minute": 1080, "reason": "통학"},
        ]}
        merged, _ = _merge_delta(base_pv, delta, base_pv.courses)
        assert len(merged.blackout_windows) == 1

    def test_blackout_windows_dedup_against_existing(self, base_pv):
        """기존 PreferenceVector에 이미 있는 window를 LLM이 다시 보내도 누적 안 됨."""
        from app.schemas import BlackoutWindow
        # 기존 blackout 1개를 미리 박아둠
        prev = base_pv.model_copy(update={"blackout_windows": [
            BlackoutWindow(days=[Weekday.FRI], start_minute=780, end_minute=1080, reason="통학"),
        ]})
        delta = {"blackout_windows": [
            {"days": ["FRI"], "start_minute": 780, "end_minute": 1080, "reason": "통학"},
        ]}
        merged, _ = _merge_delta(prev, delta, prev.courses)
        assert len(merged.blackout_windows) == 1

    def test_blackout_windows_different_windows_kept(self, base_pv):
        """다른 (days, start, end) 조합은 모두 살아남아야 한다."""
        delta = {"blackout_windows": [
            {"days": ["FRI"], "start_minute": 780, "end_minute": 1080, "reason": "통학"},
            {"days": ["MON"], "start_minute": 720, "end_minute": 780, "reason": "점심"},
        ]}
        merged, _ = _merge_delta(base_pv, delta, base_pv.courses)
        assert len(merged.blackout_windows) == 2

    def test_must_include_groups_union(self, base_pv):
        merged, _ = _merge_delta(base_pv, {"must_include_groups": ["DS"]}, base_pv.courses)
        assert "DS" in merged.must_include_groups

    def test_invalid_group_dropped(self, base_pv):
        merged, _ = _merge_delta(base_pv, {"must_include_groups": ["NOSUCH"]}, base_pv.courses)
        assert "NOSUCH" not in merged.must_include_groups

    def test_invalid_delta_keeps_base(self, base_pv):
        # credit_max < credit_min → ValidationError → base 유지
        merged, warns = _merge_delta(base_pv, {"credit_max": 1}, base_pv.courses)
        assert merged.credit_max == base_pv.credit_max  # 원본 유지
        assert any("delta 검증 실패" in w for w in warns)

    def test_category_weights_replace(self, base_pv):
        merged, _ = _merge_delta(base_pv, {"category_weights": {"전공": 1.5}}, base_pv.courses)
        assert merged.category_weight(Category.MAJOR) == 1.5
