/**
 * 중앙 패널 — 위: 선택된 시간표 / 아래: 채팅.
 *
 * 사양: frontend/docs/demo-layout.md §2.2.
 * - 선택된 시간표: 우측에서 고른 후보 한 개의 주간 격자 (전체 — compact=false)
 *   + 상단 점수·학점·과목 수 요약.
 * - 채팅: 메시지 스트림(스크롤) + 입력창(하단 고정).
 *   ⚠️ §2.2 경고: 데모 채팅 응답은 스크립트/샘플. 시간표 결정은 항상 알고리즘.
 *
 * 상태 변형:
 * - candidates 없음 → SelectedTimetable 자리에 빈 안내.
 * - loading 중 → 격자 자리에 LoadingState.
 * - error → ErrorState.
 * - infeasibility → 안내 메시지 + resolution_hint.
 */

import { useEffect, useRef, useState, type FormEvent } from "react";

import type { Course, ScoredSchedule, SelectionResult } from "../../types/timetable";
import { totalScore } from "../../lib/scoring";
import { CategoryLegend, TimetableGrid } from "../TimetableGrid";
import { EmptyState, ErrorState, LoadingState } from "../States";

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  role: ChatRole;
  text: string;
  /** 시스템 안내(가입·정보성) 톤으로 렌더링할지 — assistant 와 색을 구분. */
  tone?: "info";
}

export type CenterStatus =
  | { kind: "empty" }
  | { kind: "loading" }
  | { kind: "result"; selection: SelectionResult; selectedIndex: number; isSample: boolean }
  | { kind: "infeasible"; resolutionHint: string | null }
  | { kind: "error"; message: string; onRetry?: () => void };

interface CenterPanelProps {
  status: CenterStatus;
  catalog: Course[];
  messages: ChatMessage[];
  /** 채팅 입력이 잠긴 동안(요청 중) true. */
  chatBusy: boolean;
  onSendMessage: (text: string) => void;
}

export function CenterPanel({
  status,
  catalog,
  messages,
  chatBusy,
  onSendMessage,
}: CenterPanelProps) {
  return (
    <div className="grid h-full min-h-0" style={{ gridTemplateRows: "minmax(0, 1fr) 18rem" }}>
      {/* 위: 선택된 시간표 */}
      <section className="min-h-0 overflow-y-auto border-b border-cream-300 bg-white p-4">
        <SelectedTimetable status={status} catalog={catalog} />
      </section>

      {/* 아래: 채팅 */}
      <section className="min-h-0 bg-cream-50">
        <ChatPanel messages={messages} busy={chatBusy} onSend={onSendMessage} />
      </section>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 선택된 시간표

interface SelectedTimetableProps {
  status: CenterStatus;
  catalog: Course[];
}

function SelectedTimetable({ status, catalog }: SelectedTimetableProps) {
  if (status.kind === "empty") {
    return <EmptyState variant="initial" />;
  }
  if (status.kind === "loading") {
    return <LoadingState />;
  }
  if (status.kind === "error") {
    return <ErrorState message={status.message} onRetry={status.onRetry} />;
  }
  if (status.kind === "infeasible") {
    return <EmptyState variant="no-result" resolutionHint={status.resolutionHint} />;
  }

  // kind === "result"
  const { selection, selectedIndex, isSample } = status;
  const schedule: ScoredSchedule | undefined = selection.ranked_schedules[selectedIndex];
  if (!schedule) {
    return <EmptyState variant="no-result" resolutionHint={null} />;
  }
  const score = totalScore(schedule.score_breakdown);

  return (
    <div className="space-y-3">
      <header className="flex flex-wrap items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <h2 className="text-base font-semibold text-ink">
            추천 {selectedIndex + 1} 시간표
          </h2>
          {isSample && (
            <span
              className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-800"
              title="실제 알고리즘 응답이 아닌 디자인 미리보기용 샘플입니다."
            >
              샘플
            </span>
          )}
        </div>
        <dl className="flex items-baseline gap-4 text-xs text-ink-soft">
          <div className="flex items-baseline gap-1">
            <dt className="text-ink-faint">총점</dt>
            <dd className="text-lg font-bold tabular-nums text-brand-700">{score}</dd>
          </div>
          <div className="flex items-baseline gap-1">
            <dt className="text-ink-faint">학점</dt>
            <dd className="font-medium tabular-nums">{schedule.used_credit}</dd>
          </div>
          <div className="flex items-baseline gap-1">
            <dt className="text-ink-faint">과목</dt>
            <dd className="font-medium tabular-nums">{schedule.courses.length}</dd>
          </div>
        </dl>
      </header>

      <TimetableGrid courses={catalog} selectedCourseIds={schedule.courses} />
      <CategoryLegend />

      {selection.notes.length > 0 && (
        <p className="rounded-md bg-cream-50 px-3 py-2 text-xs text-ink-soft">
          {selection.notes[0]}
        </p>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 채팅 패널

interface ChatPanelProps {
  messages: ChatMessage[];
  busy: boolean;
  onSend: (text: string) => void;
}

function ChatPanel({ messages, busy, onSend }: ChatPanelProps) {
  const [draft, setDraft] = useState("");
  const streamRef = useRef<HTMLDivElement>(null);

  // 새 메시지가 들어오면 맨 아래로 스크롤.
  useEffect(() => {
    streamRef.current?.scrollTo({ top: streamRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, busy]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    onSend(text);
    setDraft("");
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div
        ref={streamRef}
        className="min-h-0 flex-1 space-y-2 overflow-y-auto px-4 py-3"
        role="log"
        aria-live="polite"
        aria-label="채팅 메시지"
      >
        {messages.length === 0 && !busy && (
          <p className="rounded-md bg-white/60 px-3 py-2 text-xs text-ink-faint">
            예) "월 공강, 전공 위주 15학점" / "이동 시간 줄여줘"
          </p>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        {busy && (
          <div className="flex items-center gap-2 text-xs text-ink-faint">
            <span className="h-2 w-2 animate-pulse rounded-full bg-brand-300" />
            응답 작성 중…
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex shrink-0 items-center gap-2 border-t border-cream-300 bg-white px-3 py-2"
      >
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={busy}
          placeholder="자연어로 조건을 적어 보세요 — 예: 월요일 공강"
          aria-label="채팅 메시지 입력"
          className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200 disabled:bg-cream-50"
        />
        <button
          type="submit"
          disabled={busy || !draft.trim()}
          className="shrink-0 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          보내기
        </button>
      </form>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-brand-600 px-3 py-2 text-sm text-white shadow-sm">
          {message.text}
        </div>
      </div>
    );
  }
  // assistant
  const tone =
    message.tone === "info"
      ? "bg-cream-100 text-ink-soft"
      : "bg-white text-ink";
  return (
    <div className="flex justify-start">
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-bl-sm px-3 py-2 text-sm shadow-sm ${tone}`}
      >
        {message.text}
      </div>
    </div>
  );
}
