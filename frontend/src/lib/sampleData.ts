/**
 * 디자인 미리보기용 *샘플* 데이터.
 *
 * ⚠️ 이것은 화면 디자인을 확인하기 위한 가짜 예시입니다. 알고리즘이 만든 실제
 *    결과가 아닙니다. 시간표 생성 엔드포인트가 서버에 붙으면 이 데이터는
 *    실제 응답으로 교체됩니다. (base/CLAUDE.md §3.5 — 가짜 응답을 실제처럼
 *    위조하지 않기 위해, UI는 이 데이터를 쓸 때 "샘플" 배지를 항상 표시합니다.)
 */

import type {
  Course,
  PreferenceVector,
  SelectionResult,
} from "../types/timetable";

/** 09:00 → 540 같은 변환을 간결히 쓰기 위한 헬퍼. */
const t = (h: number, m = 0) => h * 60 + m;

const SAMPLE_COURSES: Course[] = [
  {
    id: "CS101-01",
    name: "자료구조",
    times: [
      { day: "MON", start_minute: t(9), end_minute: t(10, 30) },
      { day: "WED", start_minute: t(9), end_minute: t(10, 30) },
    ],
    credit: 3,
    building: "공학관",
    category: "전공",
    requirement: "필수",
    course_group_id: "CS101",
    section: "01",
    professor: "홍교수",
  },
  {
    id: "CS101-02",
    name: "자료구조",
    times: [
      { day: "TUE", start_minute: t(13), end_minute: t(14, 30) },
      { day: "THU", start_minute: t(13), end_minute: t(14, 30) },
    ],
    credit: 3,
    building: "공학관",
    category: "전공",
    requirement: "필수",
    course_group_id: "CS101",
    section: "02",
    professor: "김교수",
  },
  {
    id: "CS210-01",
    name: "알고리즘",
    times: [
      { day: "MON", start_minute: t(13), end_minute: t(15) },
      { day: "WED", start_minute: t(13), end_minute: t(15) },
    ],
    credit: 3,
    building: "공학관",
    category: "전공",
    requirement: "선택",
    professor: "이교수",
  },
  {
    id: "MATH201-01",
    name: "선형대수",
    times: [
      { day: "TUE", start_minute: t(9), end_minute: t(10, 30) },
      { day: "THU", start_minute: t(9), end_minute: t(10, 30) },
    ],
    credit: 3,
    building: "과학관",
    category: "전공",
    requirement: "필수",
    professor: "박교수",
  },
  {
    id: "ENG110-01",
    name: "대학영어",
    times: [{ day: "FRI", start_minute: t(10), end_minute: t(12) }],
    credit: 2,
    building: "인문관",
    category: "교양",
    requirement: "필수",
    professor: "Smith",
  },
  {
    id: "PHIL100-01",
    name: "논리학",
    times: [{ day: "MON", start_minute: t(15), end_minute: t(16, 30) }],
    credit: 2,
    building: "인문관",
    category: "교양",
    requirement: "자율",
    professor: "정교수",
  },
  {
    id: "DESIGN150-01",
    name: "디자인씽킹",
    times: [{ day: "WED", start_minute: t(16), end_minute: t(18) }],
    credit: 2,
    building: "예술관",
    category: "일선",
    requirement: "자율",
    professor: "최교수",
  },
  {
    id: "STAT200-01",
    name: "확률통계",
    times: [
      { day: "TUE", start_minute: t(15), end_minute: t(16, 30) },
      { day: "THU", start_minute: t(15), end_minute: t(16, 30) },
    ],
    credit: 3,
    building: "과학관",
    category: "전공",
    requirement: "선택",
    professor: "윤교수",
  },
];

export function buildSamplePreference(): PreferenceVector {
  return {
    courses: SAMPLE_COURSES,
    credit_min: 14,
    credit_max: 18,
    course_importance: {
      "CS101-01": 5,
      "CS101-02": 5,
      "CS210-01": 4,
      "MATH201-01": 4,
      "ENG110-01": 3,
      "PHIL100-01": 2,
      "DESIGN150-01": 2,
      "STAT200-01": 3,
    },
    must_include: [],
    exclude: [],
    must_include_groups: ["CS101"],
    exclude_groups: [],
    blackout_windows: [
      { days: ["FRI"], start_minute: t(13), end_minute: t(18), reason: "통학" },
    ],
    time_penalty_grid: {},
    category_weights: { 전공: 0.5 },
    requirement_weights: { 필수: 1.0 },
    building_penalties: {},
    professor_preferences: { 홍교수: 1.0 },
    travel_time_lambda: 0.1,
    compactness_lambda: 0.5,
    target_active_days: 4,
    diversity_lambda: 0.0,
    back_to_back_preference: 0.0,
    min_break_minutes: 0,
  };
}

/** 서버에서 받은 실제 강의 풀(Course[])로 PreferenceVector 기본값 조립.
 *
 *  국민대 sample_data.csv → /timetable/sample-courses 응답을 받은 직후 사용한다.
 *  중요도·가중치는 기본값(중요도 3·전공 +0.5·필수 +1.0)으로 시작 — 사용자가
 *  폼에서 조정한다.
 */
export function buildPreferenceFromCourses(courses: Course[]): PreferenceVector {
  return {
    courses,
    credit_min: 9,
    credit_max: 18,
    course_importance: Object.fromEntries(courses.map((c) => [c.id, 3])),
    must_include: [],
    exclude: [],
    must_include_groups: [],
    exclude_groups: [],
    blackout_windows: [],
    time_penalty_grid: {},
    category_weights: { 전공: 0.5 },
    requirement_weights: { 필수: 1.0, 선택: 0.3 },
    building_penalties: {},
    professor_preferences: {},
    travel_time_lambda: 0.1,
    compactness_lambda: 0.5,
    target_active_days: 5,
    diversity_lambda: 0.0,
    back_to_back_preference: 0.0,
    min_break_minutes: 0,
  };
}

export function buildSampleResult(): SelectionResult {
  return {
    ranked_schedules: [
      {
        courses: ["CS101-01", "MATH201-01", "CS210-01", "STAT200-01", "ENG110-01"],
        used_credit: 14,
        score_breakdown: {
          core_importance: 57,
          time_penalty: -2,
          building_penalty: 0,
          category_weight: 6,
          travel_penalty: -3.4,
          compactness_penalty: 0,
          diversity_penalty: 0,
          back_to_back_term: 1.5,
        },
      },
      {
        courses: ["CS101-02", "MATH201-01", "CS210-01", "STAT200-01", "ENG110-01"],
        used_credit: 14,
        score_breakdown: {
          core_importance: 57,
          time_penalty: -3,
          building_penalty: 0,
          category_weight: 6,
          travel_penalty: -4.1,
          compactness_penalty: -0.5,
          diversity_penalty: 0,
          back_to_back_term: 0,
        },
      },
    ],
    course_rationale: {
      "CS101-01": {
        course_id: "CS101-01",
        status: "included",
        stage_code: "B-3.selected_by_DP",
        detail: "필수 그룹 CS101에서 선호 교수(홍교수)·이른 시간대라 가장 높은 점수로 선택.",
        related_course_ids: ["CS101-02"],
        score_contribution: 15,
      },
      "CS101-02": {
        course_id: "CS101-02",
        status: "excluded",
        stage_code: "B-3.group_loser",
        detail: "같은 과목 그룹 CS101에서 01분반이 더 높은 점수로 선택됨 (그룹당 1개).",
        related_course_ids: ["CS101-01"],
      },
      "CS210-01": {
        course_id: "CS210-01",
        status: "included",
        stage_code: "B-3.selected_by_DP",
        detail: "중요도 4점 전공 선택. 시간 충돌 없이 누적 점수를 높여 포함.",
        related_course_ids: [],
        score_contribution: 12,
      },
      "MATH201-01": {
        course_id: "MATH201-01",
        status: "included",
        stage_code: "B-3.selected_by_DP",
        detail: "필수 전공, 오전 시간대로 압축도에 유리해 포함.",
        related_course_ids: [],
        score_contribution: 12,
      },
      "STAT200-01": {
        course_id: "STAT200-01",
        status: "included",
        stage_code: "B-3.selected_by_DP",
        detail: "학점 한도 내에서 점수를 추가로 높여 포함.",
        related_course_ids: [],
        score_contribution: 9,
      },
      "ENG110-01": {
        course_id: "ENG110-01",
        status: "included",
        stage_code: "B-3.selected_by_DP",
        detail: "필수 교양. 금요일 오전이라 통학 blackout(금 13:00~)과 충돌하지 않음.",
        related_course_ids: [],
        score_contribution: 6,
      },
      "PHIL100-01": {
        course_id: "PHIL100-01",
        status: "excluded",
        stage_code: "B-3.score_too_low",
        detail: "중요도 2점이라 학점 한도 안에서 더 높은 점수 강의에 밀림.",
        related_course_ids: ["CS210-01"],
      },
      "DESIGN150-01": {
        course_id: "DESIGN150-01",
        status: "excluded",
        stage_code: "B-3.score_too_low",
        detail: "중요도 2점. 포함 시 학점 상한을 넘기지 않으나 점수 기여가 낮아 제외.",
        related_course_ids: [],
      },
    },
    diversity_adjustment_applied: false,
    notes: ["상위 2개 후보는 CS101 분반 선택(01 ↔ 02)에서 갈립니다 — 백본 일치율 80%."],
  };
}
