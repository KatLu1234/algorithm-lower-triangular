/**
 * 인증 API 클라이언트 — /api/v1/auth/*.
 *
 * 토큰은 localStorage 에 보관. 모든 요청은 client.ts 의 에러 처리 규약을
 * 그대로 따르되, code → 친화 메시지는 여기서 보강한다.
 */

import { ApiError } from "./client";

const TOKEN_KEY = "lt.auth.token";

export interface UserPublic {
  id: string;
  email: string;
  display_name: string | null;
}

export interface AuthResponse {
  token: string;
  user: UserPublic;
}

interface ApiErrorBody {
  detail?: string;
  code?: string;
}

const CODE_MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: "이메일 또는 비밀번호가 올바르지 않습니다.",
  EMAIL_TAKEN: "이미 등록된 이메일입니다.",
  AUTH_REQUIRED: "로그인이 필요합니다.",
  AUTH_INVALID: "세션이 만료되었습니다. 다시 로그인해 주세요.",
  VALIDATION_ERROR: "입력값을 확인해 주세요.",
};

const FALLBACK = "요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.";
const NETWORK = "서버에 연결하지 못했습니다. 네트워크를 확인해 주세요.";

function baseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL?.trim();
  const root = fromEnv && fromEnv.length > 0 ? fromEnv.replace(/\/$/, "") : "";
  return `${root}/api/v1`;
}

function friendly(code: string | undefined): string {
  if (code && CODE_MESSAGES[code]) return CODE_MESSAGES[code];
  return FALLBACK;
}

async function request<TRes>(
  path: string,
  init: RequestInit & { auth?: boolean } = {},
): Promise<TRes> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (init.auth) {
    const tok = getToken();
    if (tok) headers["Authorization"] = `Bearer ${tok}`;
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, { ...init, headers });
  } catch (networkErr) {
    throw new ApiError(NETWORK, {
      rawDetail: networkErr instanceof Error ? networkErr.message : String(networkErr),
    });
  }

  if (!response.ok) {
    let parsed: ApiErrorBody = {};
    try {
      parsed = (await response.json()) as ApiErrorBody;
    } catch {
      /* empty */
    }
    if (parsed.detail) {
      console.error(`[auth ${response.status}] ${parsed.code ?? "?"}: ${parsed.detail}`);
    }
    throw new ApiError(friendly(parsed.code), {
      code: parsed.code ?? null,
      status: response.status,
      rawDetail: parsed.detail ?? null,
    });
  }
  return (await response.json()) as TRes;
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* private mode 등 — 무시 */
  }
}

export async function signup(
  email: string,
  password: string,
  displayName?: string,
): Promise<AuthResponse> {
  const res = await request<AuthResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      display_name: displayName || null,
    }),
  });
  setToken(res.token);
  return res;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(res.token);
  return res;
}

export async function fetchMe(): Promise<UserPublic | null> {
  if (!getToken()) return null;
  try {
    return await request<UserPublic>("/auth/me", { method: "GET", auth: true });
  } catch (err) {
    // 토큰이 무효(서버 재시작 등)면 조용히 로그아웃 처리.
    if (err instanceof ApiError && (err.code === "AUTH_INVALID" || err.code === "AUTH_REQUIRED")) {
      setToken(null);
      return null;
    }
    throw err;
  }
}

export async function logout(): Promise<void> {
  try {
    await request<{ ok: boolean }>("/auth/logout", { method: "POST", auth: true });
  } catch {
    // 서버 실패해도 로컬은 비운다.
  } finally {
    setToken(null);
  }
}
