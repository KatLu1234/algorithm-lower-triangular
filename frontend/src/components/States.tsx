/**
 * 로딩 / 에러 / 빈 상태 표현.
 *
 * 인터랙션 톤은 user-experience.md §4가 채워지면 거기 맞춰 다듬는다.
 * 그 전까지는 product.md 우선순위(설명 가능성·불가능 안내)를 근거로,
 * "무슨 일이 있었고 다음에 뭘 하면 되는지"를 차분하게 알리는 톤을 사용.
 */

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "최적 시간표를 계산하고 있어요…" }: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex h-full min-h-[24rem] flex-col items-center justify-center gap-4 text-ink-soft"
    >
      <span className="h-8 w-8 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

interface ErrorStateProps {
  /** 사용자에게 보여줄 *친화적* 메시지. 서버 detail 원문을 그대로 넣지 말 것. */
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex h-full min-h-[24rem] flex-col items-center justify-center gap-4 px-6 text-center"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 8v5m0 3h.01M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.7 3.86a2 2 0 0 0-3.42 0Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <p className="max-w-sm text-sm text-ink-soft">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
        >
          다시 시도
        </button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  variant: "initial" | "no-result";
  /** 불가능 진단이 있을 때: 어느 제약을 풀면 되는지 안내(있으면). */
  resolutionHint?: string | null;
}

export function EmptyState({ variant, resolutionHint }: EmptyStateProps) {
  const isInitial = variant === "initial";
  return (
    <div className="flex h-full min-h-[24rem] flex-col items-center justify-center gap-3 px-6 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-ink-faint">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="3" y="4" width="18" height="17" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M3 9h18M8 2v4M16 2v4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </div>
      {isInitial ? (
        <>
          <p className="text-base font-medium text-ink">아직 만든 시간표가 없어요</p>
          <p className="max-w-sm text-sm text-ink-soft">
            왼쪽에서 강의 후보와 학점·중요도를 입력하고 <b>시간표 만들기</b>를 누르면
            여기 결과가 나타납니다.
          </p>
        </>
      ) : (
        <>
          <p className="text-base font-medium text-ink">조건을 만족하는 시간표가 없어요</p>
          <p className="max-w-sm text-sm text-ink-soft">
            {resolutionHint
              ? resolutionHint
              : "제약이 서로 충돌하는 것 같아요. 학점 범위를 넓히거나 필수/제외 강의를 줄여 다시 시도해 주세요."}
          </p>
        </>
      )}
    </div>
  );
}
