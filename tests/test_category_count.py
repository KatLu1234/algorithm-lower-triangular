"""기능 3 — 카테고리별 강의 개수 제약 (category_count_min/max) 테스트.

- 스키마 검증: 값 ≥0, 같은 카테고리 min ≤ max (PreferenceVector._check_consistency).
- 동작 검증: B-3 record()의 satisfies_category_counts 가 결과에 반영되는지 (recommend 통과).
"""
import pytest
from pydantic import ValidationError

from app.schemas import (
    Course, TimeSlot, Weekday, Category, PreferenceVector, SelectionResult,
)
from app.libs.timetable import recommend


def _course(cid: str, cat: Category, day: Weekday) -> Course:
    return Course(
        id=cid, name=cid, credit=3, category=cat,
        times=[TimeSlot(day=day, start_minute=540, end_minute=600, building="공학관")],
    )


# 서로 다른 요일 → 전부 상호 양립 (시간 충돌 없음)
def _pool() -> list[Course]:
    return [
        _course("M1", Category.MAJOR, Weekday.MON),
        _course("M2", Category.MAJOR, Weekday.TUE),
        _course("M3", Category.MAJOR, Weekday.WED),
        _course("L1", Category.LIBERAL, Weekday.THU),
        _course("L2", Category.LIBERAL, Weekday.FRI),
    ]


_BUILDINGS = ["공학관"]
_WALK = [[0]]


def _categories_of(result: SelectionResult, pool: list[Course]) -> list[dict]:
    """각 추천 시간표의 카테고리별 개수 dict 리스트."""
    by_id = {c.id: c for c in pool}
    out = []
    for sched in result.ranked_schedules:
        counts: dict[Category, int] = {}
        for cid in sched.courses:
            cat = by_id[cid].category
            counts[cat] = counts.get(cat, 0) + 1
        out.append(counts)
    return out


class TestCategoryCountSchema:
    def test_negative_min_rejected(self):
        with pytest.raises((ValidationError, ValueError)):
            PreferenceVector(
                courses=_pool(), credit_min=3, credit_max=18,
                category_count_min={Category.MAJOR: -1},
            )

    def test_min_exceeds_max_rejected(self):
        with pytest.raises((ValidationError, ValueError)):
            PreferenceVector(
                courses=_pool(), credit_min=3, credit_max=18,
                category_count_min={Category.MAJOR: 3},
                category_count_max={Category.MAJOR: 1},
            )

    def test_valid_constructs(self):
        pv = PreferenceVector(
            courses=_pool(), credit_min=3, credit_max=18,
            category_count_min={Category.MAJOR: 1},
            category_count_max={Category.MAJOR: 2, Category.LIBERAL: 1},
        )
        assert pv.category_count_max[Category.MAJOR] == 2


class TestCategoryCountBehavior:
    def test_max_caps_major_count(self):
        pool = _pool()
        pv = PreferenceVector(
            courses=pool, credit_min=3, credit_max=18,
            category_count_max={Category.MAJOR: 1},
        )
        result = recommend(pv, _BUILDINGS, _WALK, top_k=5)
        assert isinstance(result, SelectionResult)
        assert result.ranked_schedules, "결과 시간표가 있어야 함"
        for counts in _categories_of(result, pool):
            assert counts.get(Category.MAJOR, 0) <= 1

    def test_min_requires_majors(self):
        pool = _pool()
        pv = PreferenceVector(
            courses=pool, credit_min=6, credit_max=18,
            category_count_min={Category.MAJOR: 2},
        )
        result = recommend(pv, _BUILDINGS, _WALK, top_k=5)
        assert isinstance(result, SelectionResult)
        assert result.ranked_schedules
        for counts in _categories_of(result, pool):
            assert counts.get(Category.MAJOR, 0) >= 2
