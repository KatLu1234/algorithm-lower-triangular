/**
 * 결과 패널: 상위 N개 시간표 전환 + 주간 격자 + 점수 분해 + 포함/제외 사유.
 *
 * 설명 가능성은 product.md §4 우선순위 2위이고, §4.3.2는 "제외 사유"를 가장
 * 먼저 보여줄 자리로 못박는다 → 사유 영역에서 제외 강의를 앞에 배치.
 */

import { useState } from "react";

import type {
  Course,
  Rationale,
  ScoreBreakdown,
  SelectionResult,
} from "../types/timetable";
import { SCORE_TERMS } from "../types/timetable";
import { CategoryLegend, TimetableGrid } from "./TimetableGrid";

function sumBreakdown(b: ScoreBreakdown): number {
  return SCORE_TERMS.reduce((acc, term) => acc + b[term.key], 0);
}

function fmt(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

interface ScheduleResultProps {
  courses: Course[];
  result: SelectionResult;
  explanation?: string | null;
  /** 샘플 데이터로 렌더링 중이면 true (배지 표시). */
  isSample?: boolean;
}

export function ScheduleResult({
  courses,
  result,
  explanation,
  isSample = false,
}: ScheduleResultProps) {
  const [active, setActive] = useState(0);
  const schedules = result.ranked_schedules;
  const current = schedules[active] ?? schedules[0];
  const byId = new Map(courses.map((c) => [c.id, c]));

  const rationales = Object.values(result.course_rationale);
  const excluded = rationales.filter((r) => r.status === "excluded");
  const included = rationales.filter((r) => r.status === "included");

  return (
    <section className="flex flex-col gap-5" aria-label="추천 시간표 결과">
      {/* 헤더 + 후보 전환 탭 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-bold text-ink">추천 시간표</h2>
          {isSample && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700">
              샘플 미리보기
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="추천 후보 선택">
          {schedules.map((s, i) => {
            const isActive = i === active;
            return (
              <button
                key={i}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => setActive(i)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-brand-600 text-white"
                    : "bg-slate-100 text-ink-soft hover:bg-slate-200"
                }`}
              >
                추천 {i + 1}
                <span className={`ml-1.5 text-xs ${isActive ? "text-brand-100" : "text-ink-faint"}`}>
                  {fmt(sumBreakdown(s.score_breakdown))}점
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {isSample && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          아래 결과는 화면 디자인 확인용 <b>샘플</b>입니다. 시간표 생성 엔드포인트가
          서버에 연결되면 실제 알고리즘 결과로 바뀝니다.
        </p>
      )}

      {/* 요약 지표 */}
      <div className="flex flex-wrap gap-3">
        <SummaryStat label="총 점수" value={`${fmt(sumBreakdown(current.score_breakdown))}점`} />
        <SummaryStat label="이수 학점" value={`${current.used_credit}학점`} />
        <SummaryStat label="강의 수" value={`${current.courses.length}개`} />
      </div>

      {/* 주간 격자 */}
      <div className="flex flex-col gap-2">
        <TimetableGrid courses={courses} selectedCourseIds={current.courses} />
        <CategoryLegend />
      </div>

      {/* 점수 분해 */}
      <details className="rounded-xl border border-slate-200 bg-white" open>
        <summary className="cursor-pointer select-none px-4 py-3 text-sm font-semibold text-ink">
          점수 분해 (왜 이 점수인가)
        </summary>
        <div className="border-t border-slate-100 px-4 py-3">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-4">
            {SCORE_TERMS.map((term) => {
              const v = current.score_breakdown[term.key];
              if (v === 0) return null;
              return (
                <div key={term.key} className="flex items-baseline justify-between gap-2">
                  <dt className="text-xs text-ink-soft">{term.label}</dt>
                  <dd
                    className={`text-sm font-medium tabular-nums ${
                      v < 0 ? "text-rose-600" : "text-ink"
                    }`}
                  >
                    {v > 0 ? "+" : ""}
                    {fmt(v)}
                  </dd>
                </div>
              );
            })}
          </dl>
        </div>
      </details>

      {/* 포함 / 제외 사유 — 제외를 먼저 (product.md §4.3.2) */}
      <div className="grid gap-4 lg:grid-cols-2">
        <RationaleCard
          title="제외된 강의"
          hint="가장 궁금한 자리 — 왜 빠졌는지 먼저 봅니다."
          items={excluded}
          byId={byId}
          tone="excluded"
        />
        <RationaleCard
          title="포함된 강의"
          hint="결정 흐름의 흔적."
          items={included}
          byId={byId}
          tone="included"
        />
      </div>

      {/* LLM 단계별 설명 (있으면) */}
      {explanation && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="mb-1 text-sm font-semibold text-ink">알고리즘 단계별 설명</h3>
          <p className="whitespace-pre-line text-sm leading-relaxed text-ink-soft">
            {explanation}
          </p>
        </div>
      )}

      {/* 후보 비교 노트 */}
      {result.notes.length > 0 && (
        <ul className="space-y-1 text-xs text-ink-soft">
          {result.notes.map((note, i) => (
            <li key={i} className="flex gap-1.5">
              <span aria-hidden="true">·</span>
              {note}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3">
      <p className="text-xs text-ink-faint">{label}</p>
      <p className="mt-0.5 text-lg font-bold tabular-nums text-ink">{value}</p>
    </div>
  );
}

interface RationaleCardProps {
  title: string;
  hint: string;
  items: Rationale[];
  byId: Map<string, Course>;
  tone: "included" | "excluded";
}

function RationaleCard({ title, hint, items, byId, tone }: RationaleCardProps) {
  const dotColor = tone === "excluded" ? "bg-rose-400" : "bg-emerald-400";
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-ink">
          {title}
          <span className="ml-1.5 text-xs font-normal text-ink-faint">({items.length})</span>
        </h3>
        <p className="text-[11px] text-ink-faint">{hint}</p>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-ink-faint">해당 강의가 없습니다.</p>
      ) : (
        <ul className="space-y-2.5">
          {items.map((r) => {
            const course = byId.get(r.course_id);
            return (
              <li key={r.course_id} className="flex gap-2">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${dotColor}`} aria-hidden="true" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ink">
                    {course?.name ?? r.course_id}
                    {course?.section ? (
                      <span className="text-ink-faint"> · {course.section}분반</span>
                    ) : null}
                    <span className="ml-1.5 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-normal text-ink-faint">
                      {r.stage_code}
                    </span>
                  </p>
                  <p className="text-xs leading-snug text-ink-soft">{r.detail}</p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
