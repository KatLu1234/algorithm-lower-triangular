/**
 * 로그인 / 회원가입 화면.
 *
 * 같은 컴포넌트에서 mode 토글로 두 모드를 처리한다 (프로토타입 UX).
 * - 회원가입 모드: 비밀번호 확인 필드 + 강도 미터 + 표시 이름(선택).
 * - 필드별 인라인 검증 — 사용자가 한 번 touch 한 필드에 한해 에러 표시
 *   (typing 도중 매번 빨간 글씨가 깜빡이지 않도록).
 *
 * 성공 시 onAuthenticated(user, mode) — App 이 mode 로 환영 토스트 분기.
 */

import { useMemo, useState, type FormEvent } from "react";

import { ApiError } from "../api/client";
import { login, signup, type UserPublic } from "../api/auth";
import { gradePassword, isEmailLike, type PasswordStrength } from "../lib/validation";

type Mode = "login" | "signup";

export type AuthOutcomeMode = Mode;

interface LoginProps {
  onAuthenticated: (user: UserPublic, mode: AuthOutcomeMode) => void;
}

interface FieldErrors {
  email?: string;
  password?: string;
  confirm?: string;
  displayName?: string;
}

interface Touched {
  email: boolean;
  password: boolean;
  confirm: boolean;
  displayName: boolean;
}

const PW_MIN = 4;
const PW_MAX = 128;
const NAME_MAX = 64;

function validate(
  mode: Mode,
  email: string,
  password: string,
  confirm: string,
  displayName: string,
): FieldErrors {
  const errs: FieldErrors = {};

  if (!email.trim()) errs.email = "이메일을 입력해 주세요.";
  else if (!isEmailLike(email)) errs.email = "이메일 형식이 올바르지 않습니다.";

  if (!password) errs.password = "비밀번호를 입력해 주세요.";
  else if (password.length < PW_MIN)
    errs.password = `비밀번호는 ${PW_MIN}자 이상이어야 합니다.`;
  else if (password.length > PW_MAX)
    errs.password = `비밀번호는 ${PW_MAX}자 이하여야 합니다.`;

  if (mode === "signup") {
    if (!confirm) errs.confirm = "비밀번호를 한 번 더 입력해 주세요.";
    else if (confirm !== password) errs.confirm = "비밀번호가 일치하지 않습니다.";

    if (displayName.length > NAME_MAX)
      errs.displayName = `표시 이름은 ${NAME_MAX}자 이하여야 합니다.`;
  }
  return errs;
}

/** 강도 미터 색·라벨 색 매핑. */
const TONE_BAR: Record<PasswordStrength["tone"], string> = {
  muted: "bg-slate-200",
  weak: "bg-brand-400",
  fair: "bg-amber-400",
  good: "bg-lime-500",
  strong: "bg-emerald-600",
};
const TONE_TEXT: Record<PasswordStrength["tone"], string> = {
  muted: "text-ink-faint",
  weak: "text-brand-600",
  fair: "text-amber-700",
  good: "text-lime-700",
  strong: "text-emerald-700",
};

export function Login({ onAuthenticated }: LoginProps) {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [displayName, setDisplayName] = useState("");

  const [touched, setTouched] = useState<Touched>({
    email: false,
    password: false,
    confirm: false,
    displayName: false,
  });

  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // 매 렌더마다 재검증 — 비용 적음. 빈 객체면 통과.
  const errors = useMemo(
    () => validate(mode, email, password, confirm, displayName),
    [mode, email, password, confirm, displayName],
  );
  const hasErrors = Object.keys(errors).length > 0;
  const strength = useMemo(() => gradePassword(password), [password]);

  function resetMode(next: Mode) {
    setMode(next);
    setFormError(null);
    setConfirm("");
    setTouched({ email: false, password: false, confirm: false, displayName: false });
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    // 전 필드를 touched 로 올려서 미입력 에러도 노출.
    setTouched({ email: true, password: true, confirm: true, displayName: true });
    if (hasErrors) return;

    setFormError(null);
    setSubmitting(true);
    try {
      const res =
        mode === "login"
          ? await login(email, password)
          : await signup(email, password, displayName.trim() || undefined);
      onAuthenticated(res.user, mode);
    } catch (err) {
      setFormError(
        err instanceof ApiError
          ? err.message
          : "예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  // 인라인 에러 보여줄지 — touched 이거나 submit 시도 후.
  const showErr = (k: keyof Touched) => touched[k] && errors[k];

  return (
    <div className="min-h-full bg-cream-100">
      <div className="mx-auto flex max-w-md flex-col gap-6 px-6 py-12">
        <header className="space-y-1 text-center">
          <h1 className="text-2xl font-bold text-brand-700">시간표 만들기</h1>
          <p className="text-sm text-ink-soft">
            {mode === "login"
              ? "이메일과 비밀번호로 로그인하세요."
              : "이메일과 비밀번호로 새 계정을 만드세요."}
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          noValidate
        >
          {/* 이메일 */}
          <div className="space-y-1">
            <label htmlFor="email" className="text-sm font-medium text-ink">
              이메일
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, email: true }))}
              aria-invalid={showErr("email") ? true : undefined}
              aria-describedby={showErr("email") ? "email-err" : undefined}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
                showErr("email")
                  ? "border-brand-500 focus:border-brand-500 focus:ring-brand-200"
                  : "border-slate-300 focus:border-brand-500 focus:ring-brand-200"
              }`}
              placeholder="name@example.com"
            />
            {showErr("email") && (
              <p id="email-err" className="text-xs text-brand-600">
                {errors.email}
              </p>
            )}
          </div>

          {/* 비밀번호 */}
          <div className="space-y-1">
            <label htmlFor="password" className="text-sm font-medium text-ink">
              비밀번호
            </label>
            <input
              id="password"
              type="password"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
              minLength={PW_MIN}
              maxLength={PW_MAX}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, password: true }))}
              aria-invalid={showErr("password") ? true : undefined}
              aria-describedby={
                showErr("password")
                  ? "password-err"
                  : mode === "signup"
                    ? "password-strength"
                    : undefined
              }
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
                showErr("password")
                  ? "border-brand-500 focus:border-brand-500 focus:ring-brand-200"
                  : "border-slate-300 focus:border-brand-500 focus:ring-brand-200"
              }`}
              placeholder={mode === "signup" ? `${PW_MIN}자 이상` : ""}
            />
            {showErr("password") && (
              <p id="password-err" className="text-xs text-brand-600">
                {errors.password}
              </p>
            )}

            {/* 강도 미터 — 회원가입 모드 + 입력 시작 후. */}
            {mode === "signup" && password.length > 0 && (
              <div id="password-strength" className="space-y-1 pt-1">
                <div
                  className="flex h-1.5 gap-1"
                  role="meter"
                  aria-valuemin={0}
                  aria-valuemax={4}
                  aria-valuenow={strength.score}
                  aria-label="비밀번호 강도"
                >
                  {[1, 2, 3, 4].map((seg) => (
                    <span
                      key={seg}
                      className={`h-full flex-1 rounded ${
                        seg <= strength.score ? TONE_BAR[strength.tone] : "bg-slate-200"
                      }`}
                    />
                  ))}
                </div>
                <p className={`text-xs ${TONE_TEXT[strength.tone]}`}>
                  강도: {strength.label}
                  {strength.score < 3 && (
                    <span className="ml-1 text-ink-faint">
                      · 길이·대소문자·숫자·특수문자를 섞으면 더 안전해요.
                    </span>
                  )}
                </p>
              </div>
            )}
          </div>

          {/* 비밀번호 확인 — signup 만 */}
          {mode === "signup" && (
            <div className="space-y-1">
              <label htmlFor="confirm" className="text-sm font-medium text-ink">
                비밀번호 확인
              </label>
              <input
                id="confirm"
                type="password"
                autoComplete="new-password"
                required
                minLength={PW_MIN}
                maxLength={PW_MAX}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                onBlur={() => setTouched((t) => ({ ...t, confirm: true }))}
                aria-invalid={showErr("confirm") ? true : undefined}
                aria-describedby={showErr("confirm") ? "confirm-err" : undefined}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
                  showErr("confirm")
                    ? "border-brand-500 focus:border-brand-500 focus:ring-brand-200"
                    : "border-slate-300 focus:border-brand-500 focus:ring-brand-200"
                }`}
                placeholder="위와 동일하게 입력"
              />
              {showErr("confirm") && (
                <p id="confirm-err" className="text-xs text-brand-600">
                  {errors.confirm}
                </p>
              )}
            </div>
          )}

          {/* 표시 이름 — signup 만 */}
          {mode === "signup" && (
            <div className="space-y-1">
              <label htmlFor="display-name" className="text-sm font-medium text-ink">
                표시 이름 <span className="text-ink-faint">(선택)</span>
              </label>
              <input
                id="display-name"
                type="text"
                autoComplete="nickname"
                maxLength={NAME_MAX}
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                onBlur={() => setTouched((t) => ({ ...t, displayName: true }))}
                aria-invalid={showErr("displayName") ? true : undefined}
                aria-describedby={showErr("displayName") ? "name-err" : undefined}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 ${
                  showErr("displayName")
                    ? "border-brand-500 focus:border-brand-500 focus:ring-brand-200"
                    : "border-slate-300 focus:border-brand-500 focus:ring-brand-200"
                }`}
                placeholder="홍길동"
              />
              {showErr("displayName") && (
                <p id="name-err" className="text-xs text-brand-600">
                  {errors.displayName}
                </p>
              )}
            </div>
          )}

          {/* 서버 측 또는 네트워크 오류 */}
          {formError && (
            <p
              role="alert"
              className="rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-sm text-brand-700"
            >
              {formError}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting
              ? mode === "login"
                ? "로그인 중…"
                : "가입 중…"
              : mode === "login"
                ? "로그인"
                : "회원가입"}
          </button>

          <div className="text-center text-sm text-ink-soft">
            {mode === "login" ? (
              <>
                아직 계정이 없으신가요?{" "}
                <button
                  type="button"
                  onClick={() => resetMode("signup")}
                  className="font-semibold text-brand-600 hover:underline"
                >
                  회원가입
                </button>
              </>
            ) : (
              <>
                이미 계정이 있으신가요?{" "}
                <button
                  type="button"
                  onClick={() => resetMode("login")}
                  className="font-semibold text-brand-600 hover:underline"
                >
                  로그인
                </button>
              </>
            )}
          </div>
        </form>

        <p className="text-center text-xs text-ink-faint">
          ⓘ 프로토타입 단계 — 계정 정보는 서버 로컬 파일에 저장됩니다(외부 인증 서비스
          미사용).
        </p>
      </div>
    </div>
  );
}
