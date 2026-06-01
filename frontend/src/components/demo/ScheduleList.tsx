/**
 * 우측 후보 리스트 — 순위 카드 N개.
 *
 * 사양: frontend/docs/demo-layout.md §2.3.
 * - SelectionResult.ranked_schedules 를 점수 내림차순 카드로 나열.
 * - 각 카드: 순위 배지·총점·학점·미니 격자·핵심 한 줄.
 * - 클릭 → 중앙 "선택된 시간표" 가 그 후보로 갱신, 현재 선택 카드 하이라이트.
 * - 키보드: ↑/↓ 로 이동, Enter 로 확정(이미 포커스 행은 클릭).
 * - 데모는 항상 "샘플" 배지 노출(isSample=true 시).
 */

import { useEffect, useRef } from "react";

import type { Course, ScoredSchedule } from "../../types/timetable";
import { totalScore } from "../../lib/scoring";
import { TimetableGrid } from "../TimetableGrid";

interface ScheduleListProps {
  candidates: ScoredSchedule[];
  catalog: Course[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  isSample: boolean;
}

export function ScheduleList({
  candidates,
  catalog,
  selectedIndex,
  onSelect,
  isSample,
}: ScheduleListProps) {
  const listRef = useRef<HTMLUListElement>(null);

  // ↑/↓ 키로 카드 간 이동. 리스트에 포커스가 있을 때만 작동.
  function handleKeyDown(e: React.KeyboardEvent<HTMLUListElement>) {
    if (candidates.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      onSelect((selectedIndex + 1) % candidates.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      onSelect((selectedIndex - 1 + candidates.length) % candidates.length);
    }
  }

  // 선택된 카드를 시야 안으로 스크롤.
  useEffect(() => {
    const node = listRef.current?.querySelector<HTMLElement>(
      `[data-card-index="${selectedIndex}"]`,
    );
    node?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selectedIndex]);

  return (
    <div className="flex flex-col gap-3 px-4 py-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-ink-faint">
          추천 후보 <span className="font-normal">({candidates.length})</span>
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

      {candidates.length === 0 ? (
        <p className="rounded-lg bg-white p-3 text-xs text-ink-faint shadow-sm">
          왼쪽에서 과목을 모으거나 아래 채팅으로 시작하세요.
        </p>
      ) : (
        <ul
          ref={listRef}
          tabIndex={0}
          onKeyDown={handleKeyDown}
          aria-label="추천 시간표 후보"
          className="space-y-2 outline-none"
        >
          {candidates.map((schedule, i) => (
            <li key={i} data-card-index={i}>
              <ScheduleCard
                rank={i + 1}
                schedule={schedule}
                catalog={catalog}
                selected={i === selectedIndex}
                onClick={() => onSelect(i)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

interface ScheduleCardProps {
  rank: number;
  schedule: ScoredSchedule;
  catalog: Course[];
  selected: boolean;
  onClick: () => void;
}

function ScheduleCard({ rank, schedule, catalog, selected, onClick }: ScheduleCardProps) {
  const score = totalScore(schedule.score_breakdown);
  const byId = new Map(catalog.map((c) => [c.id, c]));

  // 핵심 한 줄 — 첫 강의 + 카테고리 분포 요약.
  const headlineCourse = schedule.courses.map((id) => byId.get(id)).find(Boolean);
  const categoryCounts = schedule.courses.reduce<Record<string, number>>((acc, id) => {
    const c = byId.get(id);
    if (!c) return acc;
    acc[c.category] = (acc[c.category] ?? 0) + 1;
    return acc;
  }, {});
  const topCategory = Object.entries(categoryCounts).sort(([, a], [, b]) => b - a)[0]?.[0];
  const headline = headlineCourse
    ? `${headlineCourse.name}${headlineCourse.section ? ` ${headlineCourse.section}분반` : ""}${
        topCategory ? ` · ${topCategory} 위주` : ""
      }`
    : "";

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      aria-label={`추천 ${rank} — 총점 ${score}, ${schedule.used_credit}학점`}
      className={`block w-full rounded-xl border bg-white p-3 text-left shadow-sm transition focus:outline-none focus:ring-2 focus:ring-brand-200 ${
        selected
          ? "border-brand-500 ring-2 ring-brand-100"
          : "border-slate-200 hover:border-brand-300"
      }`}
    >
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <span className={`text-xs font-semibold ${selected ? "text-brand-700" : "text-ink-soft"}`}>
          추천 {rank}
        </span>
        <div className="flex items-baseline gap-2">
          <span className="text-base font-bold tabular-nums text-brand-700">{score}</span>
          <span className="text-[10px] text-ink-faint">총점</span>
        </div>
      </div>

      {/* 미니 격자 — compact 모드 */}
      <div className="mb-2 max-h-44 overflow-hidden rounded-md">
        <TimetableGrid courses={catalog} selectedCourseIds={schedule.courses} compact />
      </div>

      <div className="flex items-center justify-between gap-2 text-[11px] text-ink-soft">
        <span className="truncate" title={headline}>
          {headline}
        </span>
        <span className="shrink-0 tabular-nums text-ink-faint">
          {schedule.used_credit}학점 · {schedule.courses.length}과목
        </span>
      </div>
    </button>
  );
}
