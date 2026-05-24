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
            id="ALG101", name="알고리즘", credit=3,
            category=Category.MAJOR, requirement=Requirement.REQUIRED,
            times=[
                TimeSlot(day=Weekday.MON, start_minute=600, end_minute=690, building="공학관"),
                TimeSlot(day=Weekday.WED, start_minute=600, end_minute=690, building="공학관"),
                TimeSlot(day=Weekday.FRI, start_minute=600, end_minute=690, building="공학관"),
            ],
        ),
        Course(
            id="OS201", name="운영체제", credit=3,
            category=Category.MAJOR, requirement=Requirement.REQUIRED,
            times=[
                TimeSlot(day=Weekday.TUE, start_minute=780, end_minute=870, building="공학관"),
                TimeSlot(day=Weekday.THU, start_minute=780, end_minute=870, building="공학관"),
            ],
        ),
        Course(
            id="DB201", name="데이터베이스", credit=3,
            category=Category.MAJOR, requirement=Requirement.ELECTIVE,
            times=[
                TimeSlot(day=Weekday.TUE, start_minute=630, end_minute=720, building="본관"),
                TimeSlot(day=Weekday.THU, start_minute=630, end_minute=720, building="본관"),
            ],
        ),
        Course(
            id="PHL101", name="철학", credit=3,
            category=Category.LIBERAL, requirement=Requirement.ELECTIVE,
            times=[TimeSlot(day=Weekday.TUE, start_minute=870, end_minute=990, building="인문관")],
        ),
        # 다건물 강의 — 요일마다 다른 건물 (TimeSlot.building 검증용)
        Course(
            id="GSFC038", name="국제교류세미나", credit=2,
            category=Category.LIBERAL, requirement=Requirement.OPTIONAL,
            times=[
                TimeSlot(day=Weekday.MON, start_minute=800, end_minute=845, building="과학기술1관"),
                TimeSlot(day=Weekday.WED, start_minute=900, end_minute=945, building="농심국제관"),
            ],
        ),
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