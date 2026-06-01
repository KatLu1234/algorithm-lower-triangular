/**
 * 주간 격자 (요일 × 시간). 선택된 강의들을 시간 위치에 블록으로 배치.
 *
 * 입력: 강의 풀(coursesById 조회용) + 선택된 강의 ID 목록.
 * - SelectionResult.ranked_schedules[i].courses 는 ID만 담으므로, 화면은
 *   사용자가 보낸 강의 풀과 조인해 시간/건물/교수 메타를 얻는다.
 */

import type { Category, Course, CourseId, Weekday } from "../types/timetable";
import { WEEKDAY_LABEL } from "../types/timetable";
import { computeGridBounds, hourTicks, minutesToHHMM } from "../lib/time";

const ROW_HEIGHT = 60; // 시간(1h)당 픽셀 (기본)
const COMPACT_ROW_HEIGHT = 18; // 미니 격자(1h당) — ScheduleCard 미리보기용

interface CategoryStyle {
  block: string; // 블록 배경/테두리/글자
  bar: string; // 좌측 강조 바
}

// 주 카테고리(전공)는 브랜드 마룬으로. 나머지는 구분을 위해 별도 색 유지하되
// 크림/마룬 톤과 어울리는 따뜻한 계열로.
const CATEGORY_STYLE: Record<Category, CategoryStyle> = {
  전공: { block: "bg-brand-50 border-brand-200 text-brand-900", bar: "bg-brand-600" },
  복수전공: { block: "bg-rose-50 border-rose-200 text-rose-900", bar: "bg-rose-400" },
  교양: { block: "bg-amber-50 border-amber-200 text-amber-900", bar: "bg-amber-500" },
  일선: { block: "bg-stone-100 border-stone-300 text-stone-800", bar: "bg-stone-500" },
};

interface PlacedBlock {
  course: Course;
  day: Weekday;
  startMinute: number;
  endMinute: number;
}

interface TimetableGridProps {
  courses: Course[]; // 강의 풀 (조회용)
  selectedCourseIds: CourseId[];
  /** 미니 격자 모드 — ScheduleCard 미리보기 등. 행 높이·라벨·텍스트를 축소한다.
   *  기본 false(전체 격자). */
  compact?: boolean;
}

export function TimetableGrid({
  courses,
  selectedCourseIds,
  compact = false,
}: TimetableGridProps) {
  const byId = new Map(courses.map((c) => [c.id, c]));
  const selected = selectedCourseIds
    .map((id) => byId.get(id))
    .filter((c): c is Course => Boolean(c));

  const bounds = computeGridBounds(selected.length > 0 ? selected : courses);
  const ticks = hourTicks(bounds);
  const rowHeight = compact ? COMPACT_ROW_HEIGHT : ROW_HEIGHT;
  const pxPerMinute = rowHeight / 60;
  const bodyHeight = (bounds.endMinute - bounds.startMinute) * pxPerMinute;

  const blocks: PlacedBlock[] = [];
  for (const course of selected) {
    for (const slot of course.times) {
      if (!bounds.days.includes(slot.day)) continue;
      blocks.push({
        course,
        day: slot.day,
        startMinute: slot.start_minute,
        endMinute: slot.end_minute,
      });
    }
  }

  // compact 모드는 시간 축 컬럼을 좁힘. 라벨도 두 시간 간격으로만 표시.
  const timeColWidth = compact ? "1.25rem" : "3.5rem";
  const gridTemplateColumns = `${timeColWidth} repeat(${bounds.days.length}, minmax(0, 1fr))`;
  const topFor = (minute: number) => (minute - bounds.startMinute) * pxPerMinute;

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      {/* 요일 헤더 */}
      <div className="grid border-b border-slate-200 bg-slate-50" style={{ gridTemplateColumns }}>
        <div aria-hidden="true" />
        {bounds.days.map((day) => (
          <div
            key={day}
            className={
              compact
                ? "py-0.5 text-center text-[10px] font-semibold text-ink-soft"
                : "py-2 text-center text-sm font-semibold text-ink-soft"
            }
          >
            {WEEKDAY_LABEL[day]}
          </div>
        ))}
      </div>

      {/* 본문: 시간 축 + 요일 컬럼 */}
      <div className="grid" style={{ gridTemplateColumns }}>
        {/* 시간 축 — compact 모드에선 2시간 간격으로만, "9", "11"처럼 시(hour)만 */}
        <div className="relative" style={{ height: bodyHeight }}>
          {ticks
            .filter((tick) => !compact || (tick / 60) % 2 === 0)
            .map((tick) => (
              <div
                key={tick}
                className={
                  compact
                    ? "absolute right-0.5 -translate-y-1/2 text-[8px] tabular-nums text-ink-faint"
                    : "absolute right-1.5 -translate-y-1/2 text-[11px] tabular-nums text-ink-faint"
                }
                style={{ top: topFor(tick) }}
              >
                {compact ? String(tick / 60) : minutesToHHMM(tick)}
              </div>
            ))}
        </div>

        {/* 요일별 컬럼 */}
        {bounds.days.map((day) => (
          <div
            key={day}
            className="relative border-l border-slate-100"
            style={{ height: bodyHeight }}
          >
            {/* 시간 눈금선 */}
            {ticks.map((tick) => (
              <div
                key={tick}
                className="absolute inset-x-0 border-t border-slate-100"
                style={{ top: topFor(tick) }}
                aria-hidden="true"
              />
            ))}

            {/* 강의 블록 */}
            {blocks
              .filter((b) => b.day === day)
              .map((b) => {
                const style = CATEGORY_STYLE[b.course.category];
                const top = topFor(b.startMinute);
                const height = (b.endMinute - b.startMinute) * pxPerMinute;
                const meta = [b.course.building, b.course.professor]
                  .filter(Boolean)
                  .join(" · ");
                if (compact) {
                  // 미니: 색상 블록만 — 이름은 title 로만 노출.
                  return (
                    <div
                      key={`${b.course.id}-${b.day}-${b.startMinute}`}
                      className={`absolute inset-x-[1px] overflow-hidden rounded-sm border-l-2 ${style.block} ${style.bar.replace("bg-", "border-l-")}`}
                      style={{ top: top + 0.5, height: Math.max(height - 1, 6) }}
                      title={`${b.course.name} (${minutesToHHMM(b.startMinute)}–${minutesToHHMM(
                        b.endMinute,
                      )})`}
                      aria-label={b.course.name}
                    />
                  );
                }
                return (
                  <div
                    key={`${b.course.id}-${b.day}-${b.startMinute}`}
                    className={`absolute inset-x-1 flex overflow-hidden rounded-md border text-left shadow-sm ${style.block}`}
                    style={{ top: top + 1, height: Math.max(height - 2, 18) }}
                    title={`${b.course.name} (${minutesToHHMM(b.startMinute)}–${minutesToHHMM(
                      b.endMinute,
                    )})`}
                  >
                    <span className={`w-1 shrink-0 ${style.bar}`} aria-hidden="true" />
                    <div className="min-w-0 px-2 py-1">
                      <p className="truncate text-xs font-semibold leading-tight">
                        {b.course.name}
                        {b.course.section ? (
                          <span className="font-normal opacity-70"> · {b.course.section}분반</span>
                        ) : null}
                      </p>
                      <p className="truncate text-[11px] leading-tight opacity-80">
                        {minutesToHHMM(b.startMinute)}–{minutesToHHMM(b.endMinute)}
                      </p>
                      {meta && height >= 46 ? (
                        <p className="truncate text-[11px] leading-tight opacity-70">{meta}</p>
                      ) : null}
                    </div>
                  </div>
                );
              })}
          </div>
        ))}
      </div>
    </div>
  );
}

/** 카테고리 색상 범례 (격자 아래에 표시). */
export function CategoryLegend() {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-ink-soft">
      {(Object.keys(CATEGORY_STYLE) as Category[]).map((cat) => (
        <li key={cat} className="flex items-center gap-1.5">
          <span className={`h-2.5 w-2.5 rounded-sm ${CATEGORY_STYLE[cat].bar}`} aria-hidden="true" />
          {cat}
        </li>
      ))}
    </ul>
  );
}
