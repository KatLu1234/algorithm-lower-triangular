/**
 * 백엔드 Pydantic 스키마(app/schemas/*)를 그대로 미러링한 프론트 타입.
 *
 * 권위 있는 출처: app/schemas/common.py · preferences.py · selection.py ·
 * valuation.py (그 출처는 claude/base/drafts/algorithm-tree.md §9.6).
 *
 * ⚠️ 시간표 생성 엔드포인트는 아직 서버에 등록되지 않았습니다.
 *    요청/응답 envelope(아래 TimetableRequest/TimetableResponse)와 라우트 경로는
 *    "잠정"이며, 서버 팀과 base/CLAUDE.md §3.2 안전 순서로 확정해야 합니다.
 *    여기 정의된 Course/PreferenceVector/SelectionResult 본체는 이미 확정된
 *    스키마를 따릅니다.
 */

// ── 기본 별칭 ────────────────────────────────────────────────
export type CourseId = string; // 예: "CS101-01-홍교수"
export type BuildingCode = string; // 예: "공학관"
export type CourseGroupId = string; // 예: "CS101" — 분반 묶음

// ── 열거형 (Python str-Enum 값과 동일 문자열) ────────────────
export type Weekday = "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT" | "SUN";

export const WEEKDAYS: Weekday[] = [
  "MON",
  "TUE",
  "WED",
  "THU",
  "FRI",
  "SAT",
  "SUN",
];

export const WEEKDAY_LABEL: Record<Weekday, string> = {
  MON: "월",
  TUE: "화",
  WED: "수",
  THU: "목",
  FRI: "금",
  SAT: "토",
  SUN: "일",
};

/** Category — 학문 영역 분류 (Python 값은 한글 라벨 그대로). */
export type Category = "전공" | "복수전공" | "교양" | "일선";
export const CATEGORIES: Category[] = ["전공", "복수전공", "교양", "일선"];

/** Requirement — 이수 요건. Category와 직교 차원. 옵셔널. */
export type Requirement = "필수" | "선택" | "자율";
export const REQUIREMENTS: Requirement[] = ["필수", "선택", "자율"];

// ── 핵심 도메인 타입 ─────────────────────────────────────────
/** 한 강의의 한 요일·시간 구간. 분 단위(자정 기준 0–1440). */
export interface TimeSlot {
  day: Weekday;
  start_minute: number; // 0–1439
  end_minute: number; // 1–1440, start < end
}

/** 사용자가 절대 불가로 표시한 시간대(통학·알바 등). */
export interface BlackoutWindow {
  days: Weekday[];
  start_minute: number;
  end_minute: number;
  reason?: string | null;
}

/** 한 강의(분반)의 메타데이터. */
export interface Course {
  id: CourseId;
  name: string;
  times: TimeSlot[];
  credit: number; // ≥ 1
  building: BuildingCode;
  category: Category;
  requirement?: Requirement | null;
  course_group_id?: CourseGroupId | null;
  section?: string | null; // 표시용 (예: "A반", "01")
  professor?: string | null;
}

/** PreferenceVector — 알고리즘 트리가 받는 유일한 입력 형태. */
export interface PreferenceVector {
  // ① 강의 풀과 학점 한도
  courses: Course[];
  credit_min: number;
  credit_max: number;

  // ② 사용자 명시 제약
  course_importance: Record<CourseId, number>; // 1–5, 미지정 기본 3
  must_include: CourseId[]; // (Python set → 직렬화 시 배열)
  exclude: CourseId[];
  must_include_groups: CourseGroupId[];
  exclude_groups: CourseGroupId[];
  blackout_windows: BlackoutWindow[];

  // ③ 강의별 점수 가중치
  time_penalty_grid: Record<string, number>;
  category_weights: Partial<Record<Category, number>>;
  requirement_weights: Partial<Record<Requirement, number>>;
  building_penalties: Record<BuildingCode, number>;

  // ⑤ 교수별 가중치 (옵셔널)
  professor_preferences: Record<string, number>;

  // ④ 시간표 단위 후처리 가중치
  travel_time_lambda: number; // 기본 0.1
  compactness_lambda: number; // 기본 0.5
  target_active_days: number; // 1–7, 기본 5
  diversity_lambda: number; // 기본 0.0
  back_to_back_preference: number; // 기본 0.0
}

// ── 출력 (SelectionResult / Valuation) ───────────────────────
export interface ScoreBreakdown {
  core_importance: number;
  time_penalty: number;
  building_penalty: number;
  category_weight: number;
  travel_penalty: number;
  compactness_penalty: number;
  diversity_penalty: number;
  back_to_back_term: number;
}

/** 점수 분해 항목 라벨 (UI 표시 순서대로). */
export const SCORE_TERMS: { key: keyof ScoreBreakdown; label: string }[] = [
  { key: "core_importance", label: "핵심 중요도" },
  { key: "time_penalty", label: "시간대 페널티" },
  { key: "building_penalty", label: "건물 페널티" },
  { key: "category_weight", label: "카테고리 가중치" },
  { key: "travel_penalty", label: "이동시간 페널티" },
  { key: "compactness_penalty", label: "압축도 페널티" },
  { key: "diversity_penalty", label: "다양성 페널티" },
  { key: "back_to_back_term", label: "연강/공강 선호" },
];

export interface ScoredSchedule {
  courses: CourseId[]; // 보통 시작 시간 순
  used_credit: number;
  score_breakdown: ScoreBreakdown;
}

export type RationaleStatus = "included" | "excluded";

export interface Rationale {
  course_id: CourseId;
  status: RationaleStatus;
  stage_code: string; // 예: "B-3.selected_by_DP"
  detail: string;
  related_course_ids: string[];
  score_contribution?: number | null;
}

export interface DiffInfo {
  common: CourseId[];
  only_in_left: CourseId[];
  only_in_right: CourseId[];
  edit_distance?: number | null;
}

export interface SelectionResult {
  ranked_schedules: ScoredSchedule[];
  // pairwise_diff: Python의 tuple 키는 JSON에서 표현이 까다로워 잠정 생략.
  //   서버 계약 확정 시 "i-j" 문자열 키 등으로 형태 합의 필요.
  course_rationale: Record<CourseId, Rationale>;
  diversity_adjustment_applied: boolean;
  notes: string[];
}

// ── 조기 종료(불가능) 신호 ──────────────────────────────────
export interface InfeasibilityReport {
  reason: string;
  stage: string; // 예: "A-1"
  detail: string;
  resolution_hint?: string | null;
  offending_course_ids: string[];
  offending_group_ids: string[];
}

// ── 잠정 요청/응답 envelope (서버 협의 필요) ─────────────────
/** POST 본문. 잠정: PreferenceVector를 그대로 보낸다고 가정. */
export interface TimetableRequest {
  preference: PreferenceVector;
  top_n?: number; // 보여줄 후보 수 (3~5)
  explain?: boolean; // LLM 단계별 설명 동봉 여부
}

/** 응답. 잠정 envelope. */
export interface TimetableResponse {
  selection: SelectionResult;
  infeasibility?: InfeasibilityReport | null;
  explanation?: string | null; // LLM 생성 (옵셔널)
}

// 계약 미확정 표시 — 코드에서 참조해 한 곳에서만 관리.
export const CONTRACT_STATUS = "provisional" as const;
