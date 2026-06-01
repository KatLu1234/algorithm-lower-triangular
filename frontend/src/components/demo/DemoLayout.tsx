/**
 * 클로드형 3-column 데모 레이아웃 셸.
 *
 * 사양: frontend/docs/demo-layout.md §1.
 * - 좌 280px(고정) / 중앙(가변, 최소 ~480px) / 우 340px(스크롤).
 * - 세 영역은 각자 독립 스크롤.
 * - 상단 헤더는 로고/타이틀과 사용자명·로그아웃만 (얇게).
 * - 최소 보장 폭 ~1100px (좁아질 때 우측 접기/좌측 토글은 후속).
 */

import type { ReactNode } from "react";

import type { UserPublic } from "../../api/auth";

interface DemoLayoutProps {
  currentUser: UserPublic;
  onLogout: () => void;
  /** 가입 직후 헤더 아래에 잠시 떴다 사라지는 환영 토스트. null 이면 안 보임. */
  welcome: string | null;
  onDismissWelcome: () => void;
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
}

export function DemoLayout({
  currentUser,
  onLogout,
  welcome,
  onDismissWelcome,
  left,
  center,
  right,
}: DemoLayoutProps) {
  return (
    <div className="flex h-screen min-h-0 flex-col bg-cream-100 text-ink">
      {/* 헤더 — 얇게. 좌측 상단 타이틀 + 우측 사용자명·로그아웃. */}
      <header className="shrink-0 border-b border-cream-300 bg-cream-50">
        <div className="flex items-center justify-between gap-4 px-5 py-3">
          <div className="flex items-baseline gap-2">
            <span className="text-base font-bold text-brand-700">시간표 만들기</span>
            <span className="text-xs text-ink-faint">데모</span>
          </div>
          <div className="flex shrink-0 items-center gap-3 text-sm">
            <span className="text-ink-soft" title={currentUser.email}>
              {currentUser.display_name || currentUser.email}
            </span>
            <button
              type="button"
              onClick={onLogout}
              className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-ink-soft transition hover:border-brand-400 hover:text-brand-700"
            >
              로그아웃
            </button>
          </div>
        </div>
        {welcome && (
          <div role="status" aria-live="polite" className="px-5 pb-2">
            <div className="flex items-center justify-between gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-sm text-emerald-800">
              <span>{welcome}</span>
              <button
                type="button"
                onClick={onDismissWelcome}
                className="text-xs text-emerald-700 hover:underline"
                aria-label="환영 메시지 닫기"
              >
                닫기
              </button>
            </div>
          </div>
        )}
      </header>

      {/* 본문 3-column. 각 영역 내부에서 자체 overflow-y-auto. */}
      <div
        className="grid min-h-0 flex-1"
        style={{ gridTemplateColumns: "280px minmax(480px, 1fr) 340px" }}
      >
        <aside className="min-h-0 overflow-y-auto border-r border-cream-300 bg-cream-50">
          {left}
        </aside>
        <main className="min-h-0 overflow-hidden">{center}</main>
        <aside className="min-h-0 overflow-y-auto border-l border-cream-300 bg-cream-50">
          {right}
        </aside>
      </div>
    </div>
  );
}
