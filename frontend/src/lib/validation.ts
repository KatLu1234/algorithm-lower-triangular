/**
 * 회원가입/로그인 폼의 클라이언트 측 검증 유틸.
 *
 * 서버가 최종 검증을 담당하지만(team-guide.md §4), 폼이 제출되기 전에
 * 사용자에게 "어디가 문제인지"를 보여줘 왕복을 줄이는 1차 가드.
 */

/** 이메일 형식 가벼운 검사 — 백엔드와 동일하게 `@` 포함 + 최소 길이만. */
export function isEmailLike(value: string): boolean {
  const v = value.trim();
  if (v.length < 3 || v.length > 254) return false;
  const at = v.indexOf("@");
  if (at <= 0 || at === v.length - 1) return false;
  // 도메인 쪽에 점 한 개라도 있어야 사람이 보기에 자연스러움 (선택).
  return v.slice(at + 1).includes(".");
}

export interface PasswordStrength {
  /** 0~4. 0=빈값/너무 짧음, 4=강함. UI 미터의 채움 칸 수. */
  score: 0 | 1 | 2 | 3 | 4;
  /** 사람이 읽는 라벨. */
  label: "너무 짧음" | "약함" | "보통" | "양호" | "강함";
  /** 미터 색 — tailwind 클래스 직접 사용 가능하도록 매핑된 키. */
  tone: "muted" | "weak" | "fair" | "good" | "strong";
}

/**
 * 매우 단순한 점수 계산 — 보안적으로 엄밀하진 않지만 사용자에게 "더 길고
 * 다양하게 쓰세요" 신호를 주는 용도.
 *
 * +1 길이 ≥ 8, +1 길이 ≥ 12, +1 대·소문자 혼합, +1 숫자 포함, +1 특수문자.
 * 단, 4자 미만은 무조건 score=0 ("너무 짧음").
 */
export function gradePassword(pw: string): PasswordStrength {
  if (pw.length < 4) {
    return { score: 0, label: "너무 짧음", tone: "muted" };
  }
  let raw = 0;
  if (pw.length >= 8) raw += 1;
  if (pw.length >= 12) raw += 1;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) raw += 1;
  if (/\d/.test(pw)) raw += 1;
  if (/[^A-Za-z0-9]/.test(pw)) raw += 1;
  const score = Math.min(4, Math.max(1, raw)) as 1 | 2 | 3 | 4;
  const labels: Record<1 | 2 | 3 | 4, PasswordStrength["label"]> = {
    1: "약함",
    2: "보통",
    3: "양호",
    4: "강함",
  };
  const tones: Record<1 | 2 | 3 | 4, PasswordStrength["tone"]> = {
    1: "weak",
    2: "fair",
    3: "good",
    4: "strong",
  };
  return { score, label: labels[score], tone: tones[score] };
}
