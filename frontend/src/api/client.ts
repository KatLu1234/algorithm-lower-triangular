/**
 * 서버 /api/v1 호출을 위한 얇은 fetch 래퍼.
 *
 * 규약 (claude/base/architecture.md §5.1, claude/frontend/team-guide.md §4·§6):
 *  - 모든 API는 /api/v1 접두어. JSON only.
 *  - 에러 응답 표준: { "detail": "...", "code": "LT_INVALID_SHAPE" }
 *  - ⚠️ 서버의 detail 원문을 사용자에게 그대로 노출하지 않는다.
 *    code를 친화적 한국어 메시지로 변환하고, detail은 디버그용으로만 보관.
 *  - LLM 직접 호출·시크릿 보관 금지 (서버 경유).
 */

import type {
  Course,
  PreferenceVector,
  TimetableRequest,
  TimetableResponse,
} from "../types/timetable";

/** 서버 표준 에러 바디. */
interface ApiErrorBody {
  detail?: string;
  code?: string;
}

/** 사용자에게 보여줄 친화적 에러. UI는 message만 노출, 나머지는 내부용. */
export class ApiError extends Error {
  /** 서버 code (있으면). 디버그·분기용. */
  readonly code: string | null;
  /** HTTP 상태. */
  readonly status: number | null;
  /** 서버 detail 원문 — 로그/콘솔용. UI에 그대로 출력 금지. */
  readonly rawDetail: string | null;

  constructor(
    message: string,
    opts: { code?: string | null; status?: number | null; rawDetail?: string | null } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.code = opts.code ?? null;
    this.status = opts.status ?? null;
    this.rawDetail = opts.rawDetail ?? null;
  }
}

/**
 * 서버 code → 사용자 친화 메시지.
 * 새 code가 생기면 여기 추가. 미등록 code/네트워크 오류는 기본 메시지로.
 */
const CODE_MESSAGES: Record<string, string> = {
  LT_INVALID_SHAPE: "입력한 강의 데이터 형식이 올바르지 않습니다. 시간·학점 값을 확인해 주세요.",
  VALIDATION_ERROR: "입력값에 문제가 있습니다. 강조 표시된 항목을 확인해 주세요.",
  CREDIT_RANGE_INVALID: "학점 하한이 상한보다 큽니다. 학점 범위를 다시 설정해 주세요.",
  TIMEOUT: "계산이 제한 시간을 초과했습니다. 강의 후보 수를 줄여 다시 시도해 주세요.",
  LLM_UNAVAILABLE: "자연어 변환 서비스(Upstage)에 연결할 수 없습니다. 서버에 UPSTAGE_API_KEY가 설정돼 있는지 확인해 주세요.",
  LLM_TIMEOUT: "자연어 변환이 시간 안에 응답하지 않았습니다. 잠시 후 다시 시도해 주세요.",
  LLM_BAD_RESPONSE: "자연어 변환 결과를 해석하지 못했습니다. 표현을 조금 바꿔 다시 시도해 주세요.",
};

const FALLBACK_MESSAGE =
  "요청을 처리하지 못했습니다. 잠시 후 다시 시도하거나 입력을 확인해 주세요.";
const NETWORK_MESSAGE =
  "서버에 연결하지 못했습니다. 네트워크 상태와 백엔드 실행 여부를 확인해 주세요.";

/** VITE_API_BASE_URL 이 있으면 사용, 없으면 같은 오리진의 /api/v1. */
function baseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL?.trim();
  const root = fromEnv && fromEnv.length > 0 ? fromEnv.replace(/\/$/, "") : "";
  return `${root}/api/v1`;
}

function friendlyMessage(code: string | undefined): string {
  if (code && CODE_MESSAGES[code]) return CODE_MESSAGES[code];
  return FALLBACK_MESSAGE;
}

async function postJson<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (networkErr) {
    throw new ApiError(NETWORK_MESSAGE, {
      rawDetail: networkErr instanceof Error ? networkErr.message : String(networkErr),
    });
  }

  if (!response.ok) {
    let parsed: ApiErrorBody = {};
    try {
      parsed = (await response.json()) as ApiErrorBody;
    } catch {
      // JSON이 아니면 빈 바디로 둔다.
    }
    if (parsed.detail) {
      // detail은 콘솔로만. UI 노출 금지.
      console.error(`[api ${response.status}] ${parsed.code ?? "?"}: ${parsed.detail}`);
    }
    throw new ApiError(friendlyMessage(parsed.code), {
      code: parsed.code ?? null,
      status: response.status,
      rawDetail: parsed.detail ?? null,
    });
  }

  return (await response.json()) as TRes;
}

/** 시간표 생성 요청 — POST /api/v1/timetable/solve. */
export async function requestTimetable(
  payload: TimetableRequest,
): Promise<TimetableResponse> {
  return postJson<TimetableRequest, TimetableResponse>("/timetable/solve", payload);
}

/** 서버 응답 — sample_data.csv 파싱 결과. */
export interface SampleCoursesResponse {
  courses: Course[];
  source: string;
}

/** 자연어 → PreferenceVector 부분 업데이트 요청.
 *
 *  POST /api/v1/timetable/parse-preference. LLM(Upstage Solar)이 사용자 문장을
 *  현재 PreferenceVector에 적용 가능한 delta로 변환해 반환한다. *결정자 아님* —
 *  최종 시간표는 그 다음 /solve 호출에서 알고리즘이 만든다(product.md §4.4).
 */
export interface ParsePreferenceRequest {
  text: string;
  preference: PreferenceVector;
}

export interface ParsePreferenceResponse {
  preference: PreferenceVector;
  applied: string[];     // 이해해서 적용한 항목 (한국어 라벨)
  unsupported: string[]; // 이해 못 했거나 시스템이 표현할 수 없는 항목
}

export async function parsePreference(
  payload: ParsePreferenceRequest,
): Promise<ParsePreferenceResponse> {
  return postJson<ParsePreferenceRequest, ParsePreferenceResponse>(
    "/timetable/parse-preference",
    payload,
  );
}

/** 샘플 강의 카탈로그 조회 — GET /api/v1/timetable/sample-courses.
 *
 *  국민대 sample_data.csv를 백엔드가 파싱해 반환한 Course[]. 초기 로드 시
 *  PreferenceForm의 후보 풀을 채우는 데 사용. 서버 미가용/CSV 없음이면 throw.
 */
export async function fetchSampleCourses(): Promise<SampleCoursesResponse> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}/timetable/sample-courses`, {
      method: "GET",
    });
  } catch (networkErr) {
    throw new ApiError(NETWORK_MESSAGE, {
      rawDetail: networkErr instanceof Error ? networkErr.message : String(networkErr),
    });
  }
  if (!response.ok) {
    throw new ApiError(FALLBACK_MESSAGE, { status: response.status });
  }
  return (await response.json()) as SampleCoursesResponse;
}
