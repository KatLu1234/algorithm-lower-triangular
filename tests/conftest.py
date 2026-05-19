import pytest
from app.schemas import (
    Course, TimeSlot, Weekday, Category, Requirement,
    BlackoutWindow, PreferenceVector,
)

@pytest.fixture
def minji_courses() -> list[Course]:
    """김민지 시나리오 — 8개 강의."""
    return [
        Course(
            id="ALG101", name="알고리즘", credit=3, building="공학관",
            category=Category.MAJOR, requirement=Requirement.REQUIRED,
            times=[
                TimeSlot(day=Weekday.MON, start_minute=600, end_minute=690),
                TimeSlot(day=Weekday.WED, start_minute=600, end_minute=690),
                TimeSlot(day=Weekday.FRI, start_minute=600, end_minute=690),
            ],
        ),
        Course(
            id="OS201", name="운영체제", credit=3, building="공학관",
            category=Category.MAJOR, requirement=Requirement.REQUIRED,
            times=[
                TimeSlot(day=Weekday.TUE, start_minute=780, end_minute=870),
                TimeSlot(day=Weekday.THU, start_minute=780, end_minute=870),
            ],
        ),
        Course(
            id="DB201", name="데이터베이스", credit=3, building="본관",
            category=Category.MAJOR, requirement=Requirement.ELECTIVE,
            times=[
                TimeSlot(day=Weekday.TUE, start_minute=630, end_minute=720),
                TimeSlot(day=Weekday.THU, start_minute=630, end_minute=720),
            ],
        ),
        Course(
            id="PHL101", name="철학", credit=3, building="인문관",
            category=Category.LIBERAL, requirement=Requirement.ELECTIVE,
            times=[TimeSlot(day=Weekday.TUE, start_minute=870, end_minute=990)],
        ),
        # ... 더 추가 가능
    ]


@pytest.fixture
def minji_pv(minji_courses) -> PreferenceVector:
    return PreferenceVector(
        courses=minji_courses,
        credit_min=12,
        credit_max=18,
        course_importance={c.id: 5 for c in minji_courses[:2]},
        must_include={"ALG101"},
        blackout_windows=[
            BlackoutWindow(days=[Weekday.TUE], start_minute=0, end_minute=540,
                          reason="통학"),
        ],
        category_weights={Category.MAJOR: 2.0},
        requirement_weights={Requirement.REQUIRED: 1.5},
    )