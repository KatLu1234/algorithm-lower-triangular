/**
 * 입력 폼 — PreferenceVector를 조립해 onSubmit으로 넘긴다.
 *
 * UI 1차 검증만 담당하고 최종 검증은 서버가 한다(team-guide §4).
 * 강의 풀(후보) 편집 + 강의별 중요도/필수/제외 + 학점 범위 + 가중치 + blackout.
 */

import { useId, useState } from "react";
import type { Dispatch, FormEvent, ReactNode, SetStateAction } from "react";

import type {
  BlackoutWindow,
  Category,
  Course,
  PreferenceVector,
  Requirement,
  TimeSlot,
  Weekday,
} from "../types/timetable";
import {
  CATEGORIES,
  REQUIREMENTS,
  WEEKDAYS,
  WEEKDAY_LABEL,
} from "../types/timetable";
import { hhmmToMinutes, minutesToHHMM } from "../lib/time";

interface PreferenceFormProps {
  initial: PreferenceVector;
  submitting: boolean;
  onSubmit: (pref: PreferenceVector) => void;
  onPreviewSample: () => void;
}

interface DraftSlot {
  day: Weekday;
  start: string; // "HH:MM"
  end: string;
}

interface DraftCourse {
  name: string;
  credit: number;
  building: string;
  category: Category;
  requirement: Requirement | "";
  professor: string;
  section: string;
  group: string;
  slots: DraftSlot[];
}

const emptyDraft = (): DraftCourse => ({
  name: "",
  credit: 3,
  building: "",
  category: "전공",
  requirement: "",
  professor: "",
  section: "",
  group: "",
  slots: [{ day: "MON", start: "09:00", end: "10:30" }],
});

export function PreferenceForm({
  initial,
  submitting,
  onSubmit,
  onPreviewSample,
}: PreferenceFormProps) {
  const [courses, setCourses] = useState<Course[]>(initial.courses);
  const [importance, setImportance] = useState<Record<string, number>>(
    initial.course_importance,
  );
  const [mustInclude, setMustInclude] = useState<Set<string>>(
    new Set(initial.must_include),
  );
  const [exclude, setExclude] = useState<Set<string>>(new Set(initial.exclude));
  const [creditMin, setCreditMin] = useState(initial.credit_min);
  const [creditMax, setCreditMax] = useState(initial.credit_max);
  const [targetDays, setTargetDays] = useState(initial.target_active_days);
  const [travelLambda, setTravelLambda] = useState(initial.travel_time_lambda);
  const [compactLambda, setCompactLambda] = useState(initial.compactness_lambda);
  const [minBreak, setMinBreak] = useState(initial.min_break_minutes ?? 0);
  const [blackouts, setBlackouts] = useState<BlackoutWindow[]>(initial.blackout_windows);

  const [draft, setDraft] = useState<DraftCourse>(emptyDraft());
  const [adding, setAdding] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const creditInvalid = creditMin > creditMax;

  function addDraftCourse() {
    if (!draft.name.trim()) {
      setFormError("강의명을 입력해 주세요.");
      return;
    }
    if (!draft.building.trim()) {
      setFormError("건물을 입력해 주세요.");
      return;
    }
    const slots: TimeSlot[] = [];
    for (const s of draft.slots) {
      const start = hhmmToMinutes(s.start);
      const end = hhmmToMinutes(s.end);
      if (start === null || end === null || start >= end) {
        setFormError("시간 형식이 올바르지 않습니다. 시작 < 종료인지 확인해 주세요.");
        return;
      }
      slots.push({ day: s.day, start_minute: start, end_minute: end });
    }
    // 사람이 읽기 쉬운 ID 자동 생성 (충돌 시 접미사).
    const base = `${draft.name.trim()}${draft.section ? `-${draft.section}` : ""}`;
    let id = base;
    let n = 2;
    const existing = new Set(courses.map((c) => c.id));
    while (existing.has(id)) id = `${base}-${n++}`;

    const course: Course = {
      id,
      name: draft.name.trim(),
      times: slots,
      credit: draft.credit,
      building: draft.building.trim(),
      category: draft.category,
      requirement: draft.requirement || null,
      course_group_id: draft.group.trim() || null,
      section: draft.section.trim() || null,
      professor: draft.professor.trim() || null,
    };
    setCourses((prev) => [...prev, course]);
    setImportance((prev) => ({ ...prev, [id]: 3 }));
    setDraft(emptyDraft());
    setAdding(false);
    setFormError(null);
  }

  function removeCourse(id: string) {
    setCourses((prev) => prev.filter((c) => c.id !== id));
    setImportance((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
    setMustInclude((prev) => toggledOff(prev, id));
    setExclude((prev) => toggledOff(prev, id));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (courses.length === 0) {
      setFormError("강의 후보를 최소 1개 추가해 주세요.");
      return;
    }
    if (creditInvalid) {
      setFormError("학점 하한이 상한보다 큽니다.");
      return;
    }
    setFormError(null);
    const pref: PreferenceVector = {
      ...initial,
      courses,
      credit_min: creditMin,
      credit_max: creditMax,
      course_importance: importance,
      must_include: [...mustInclude],
      exclude: [...exclude],
      blackout_windows: blackouts,
      target_active_days: targetDays,
      travel_time_lambda: travelLambda,
      compactness_lambda: compactLambda,
      min_break_minutes: minBreak,
    };
    onSubmit(pref);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6" noValidate>
      {/* 강의 후보 — 스크롤 컨테이너 (긴 카탈로그 대비) */}
      <Section
        title={`강의 후보 (${courses.length}개)`}
        desc="듣고 싶은 강의를 모두 추가하세요. 시스템이 이 안에서 조합을 고릅니다."
      >
        <div
          className="max-h-[24rem] min-w-0 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50/50 p-2"
          aria-label="강의 후보 목록"
        >
          <ul className="flex min-w-0 flex-col gap-2">
            {courses.map((course) => (
              <CourseRow
                key={course.id}
                course={course}
                importance={importance[course.id] ?? 3}
                must={mustInclude.has(course.id)}
                excluded={exclude.has(course.id)}
                onImportance={(v) => setImportance((p) => ({ ...p, [course.id]: v }))}
                onToggleMust={() => {
                  setMustInclude((p) => toggle(p, course.id));
                  setExclude((p) => toggledOff(p, course.id));
                }}
                onToggleExclude={() => {
                  setExclude((p) => toggle(p, course.id));
                  setMustInclude((p) => toggledOff(p, course.id));
                }}
                onRemove={() => removeCourse(course.id)}
              />
            ))}
            {courses.length === 0 && (
              <li className="rounded-lg border border-dashed border-slate-300 px-3 py-6 text-center text-sm text-ink-faint">
                아직 추가한 강의가 없습니다.
              </li>
            )}
          </ul>
        </div>

        {adding ? (
          <CourseEditor
            draft={draft}
            setDraft={setDraft}
            onConfirm={addDraftCourse}
            onCancel={() => {
              setAdding(false);
              setDraft(emptyDraft());
              setFormError(null);
            }}
          />
        ) : (
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="mt-1 flex items-center justify-center gap-1.5 rounded-lg border border-dashed border-brand-300 bg-brand-50 px-3 py-2.5 text-sm font-medium text-brand-700 transition hover:bg-brand-100"
          >
            <span aria-hidden="true">+</span> 강의 추가
          </button>
        )}
      </Section>

      {/* 학점 범위 */}
      <Section title="학점 범위">
        <div className="flex flex-wrap items-end gap-4">
          <NumberField
            label="최소 학점"
            value={creditMin}
            min={0}
            onChange={setCreditMin}
            invalid={creditInvalid}
          />
          <span className="pb-2 text-ink-faint">~</span>
          <NumberField
            label="최대 학점"
            value={creditMax}
            min={1}
            onChange={setCreditMax}
            invalid={creditInvalid}
          />
        </div>
        {creditInvalid && (
          <p className="mt-1 text-xs text-rose-600">하한이 상한보다 큽니다.</p>
        )}
      </Section>

      {/* 가중치 — 옵션 영역. accent로 다른 섹션과 시각적으로 구분 */}
      <Section
        title="⚙️ 점수 조정 옵션"
        desc="값이 클수록 해당 항목을 더 중요하게 봅니다. 자연어 입력으로도 자동 설정됩니다."
        accent
      >
        <div className="grid gap-4 sm:grid-cols-3">
          <NumberField
            label="목표 등교 요일 수"
            value={targetDays}
            min={1}
            max={7}
            onChange={setTargetDays}
          />
          <SliderField
            label="이동시간 페널티 λ₁"
            value={travelLambda}
            min={0}
            max={1}
            step={0.1}
            onChange={setTravelLambda}
          />
          <SliderField
            label="요일 압축 페널티 λ₂"
            value={compactLambda}
            min={0}
            max={2}
            step={0.1}
            onChange={setCompactLambda}
          />
          <NumberField
            label="최소 쉬는시간(분)"
            value={minBreak}
            min={0}
            max={180}
            onChange={setMinBreak}
          />
        </div>
      </Section>

      {/* Blackout — 옵션 영역 */}
      <Section
        title="🚫 제외 시간대 (blackout)"
        desc="통학·알바 등 절대 강의를 넣지 않을 시간. 추가한 만큼 누적됩니다."
        accent
      >
        <BlackoutEditor windows={blackouts} onChange={setBlackouts} />
      </Section>

      {formError && (
        <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {formError}
        </p>
      )}

      {/* 액션 */}
      <div className="flex flex-col gap-2 border-t border-slate-200 pt-4">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? "계산 중…" : "시간표 만들기"}
        </button>
        <button
          type="button"
          onClick={onPreviewSample}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-ink-soft transition hover:bg-slate-50"
        >
          샘플 결과로 미리보기
        </button>
        <p className="text-[11px] leading-snug text-ink-faint">
          ⚠️ 시간표 생성 서버 엔드포인트는 아직 연결 전입니다. 지금은 “샘플 결과로
          미리보기”로 화면을 확인하세요.
        </p>
      </div>
    </form>
  );
}

// ── 헬퍼: 집합 토글 ───────────────────────────────────────────
function toggle(set: Set<string>, id: string): Set<string> {
  const next = new Set(set);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  return next;
}
function toggledOff(set: Set<string>, id: string): Set<string> {
  if (!set.has(id)) return set;
  const next = new Set(set);
  next.delete(id);
  return next;
}

// ── 섹션 래퍼 ─────────────────────────────────────────────────
function Section({
  title,
  desc,
  children,
  accent = false,
}: {
  title: string;
  desc?: string;
  children: ReactNode;
  /** true면 옅은 강조 배경 + 테두리 — "조정 (선택)" 같은 옵션 영역에 사용 */
  accent?: boolean;
}) {
  // fieldset은 기본 min-inline-size: min-content이라 flex/grid에서 줄어들지 않음.
  // min-w-0으로 명시 해제해야 자식의 truncate·overflow가 정상 작동.
  const baseCls = "flex min-w-0 flex-col gap-2.5";
  const accentCls = accent
    ? "rounded-xl border border-brand-200 bg-brand-50/60 px-3 py-3"
    : "";
  return (
    <fieldset className={`${baseCls} ${accentCls}`}>
      <legend
        className={
          accent
            ? "px-1 text-sm font-semibold text-brand-700"
            : "text-sm font-semibold text-ink"
        }
      >
        {title}
      </legend>
      {desc && <p className="-mt-1 text-xs text-ink-faint">{desc}</p>}
      {children}
    </fieldset>
  );
}

// ── 강의 행 ───────────────────────────────────────────────────
interface CourseRowProps {
  course: Course;
  importance: number;
  must: boolean;
  excluded: boolean;
  onImportance: (v: number) => void;
  onToggleMust: () => void;
  onToggleExclude: () => void;
  onRemove: () => void;
}

function CourseRow({
  course,
  importance,
  must,
  excluded,
  onImportance,
  onToggleMust,
  onToggleExclude,
  onRemove,
}: CourseRowProps) {
  const timeText = course.times
    .map(
      (s) =>
        `${WEEKDAY_LABEL[s.day]} ${minutesToHHMM(s.start_minute)}–${minutesToHHMM(
          s.end_minute,
        )}`,
    )
    .join(", ");

  return (
    <li
      className={`min-w-0 rounded-lg border px-3 py-2.5 transition ${
        excluded ? "border-slate-200 bg-slate-50 opacity-60" : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex min-w-0 items-start justify-between gap-2">
        {/* min-w-0 + flex-1: 부모(li)가 좁아도 텍스트가 truncate되도록 폭 제약 */}
        <div className="min-w-0 flex-1">
          <p className="break-words text-sm font-medium text-ink">
            {course.name}
            {course.section ? <span className="text-ink-faint"> · {course.section}분반</span> : null}
            <span className="ml-1.5 text-xs font-normal text-ink-faint">{course.credit}학점</span>
          </p>
          <p className="truncate text-xs text-ink-soft">{timeText}</p>
          <p className="truncate text-[11px] text-ink-faint">
            {[course.building, course.category, course.professor].filter(Boolean).join(" · ")}
          </p>
        </div>
        <button
          type="button"
          onClick={onRemove}
          aria-label={`${course.name} 삭제`}
          className="shrink-0 rounded p-1 text-ink-faint transition hover:bg-rose-50 hover:text-rose-600"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
        <label className="flex items-center gap-2 text-xs text-ink-soft">
          중요도
          <select
            value={importance}
            onChange={(e) => onImportance(Number(e.target.value))}
            disabled={excluded}
            className="rounded border border-slate-300 bg-white px-1.5 py-1 text-xs"
          >
            {[1, 2, 3, 4, 5].map((v) => (
              <option key={v} value={v}>
                {v}점
              </option>
            ))}
          </select>
        </label>
        <Toggle label="필수 포함" active={must} onClick={onToggleMust} tone="must" />
        <Toggle label="제외" active={excluded} onClick={onToggleExclude} tone="exclude" />
      </div>
    </li>
  );
}

function Toggle({
  label,
  active,
  onClick,
  tone,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  tone: "must" | "exclude";
}) {
  const activeClass =
    tone === "must" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700";
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full px-2.5 py-1 text-xs font-medium transition ${
        active ? activeClass : "bg-slate-100 text-ink-faint hover:bg-slate-200"
      }`}
    >
      {label}
    </button>
  );
}

// ── 강의 추가 에디터 ──────────────────────────────────────────
interface CourseEditorProps {
  draft: DraftCourse;
  setDraft: Dispatch<SetStateAction<DraftCourse>>;
  onConfirm: () => void;
  onCancel: () => void;
}

function CourseEditor({ draft, setDraft, onConfirm, onCancel }: CourseEditorProps) {
  const update = <K extends keyof DraftCourse>(key: K, value: DraftCourse[K]) =>
    setDraft((d) => ({ ...d, [key]: value }));

  const updateSlot = (i: number, patch: Partial<DraftSlot>) =>
    setDraft((d) => ({
      ...d,
      slots: d.slots.map((s, idx) => (idx === i ? { ...s, ...patch } : s)),
    }));

  return (
    <div className="rounded-lg border border-brand-200 bg-brand-50/40 p-3">
      <div className="grid gap-2.5 sm:grid-cols-2">
        <TextField label="강의명" value={draft.name} onChange={(v) => update("name", v)} autoFocus />
        <TextField label="건물" value={draft.building} onChange={(v) => update("building", v)} />
        <label className="flex flex-col gap-1 text-xs text-ink-soft">
          카테고리
          <select
            value={draft.category}
            onChange={(e) => update("category", e.target.value as Category)}
            className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm text-ink"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink-soft">
          이수 요건
          <select
            value={draft.requirement}
            onChange={(e) => update("requirement", e.target.value as Requirement | "")}
            className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm text-ink"
          >
            <option value="">(미지정)</option>
            {REQUIREMENTS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink-soft">
          학점
          <input
            type="number"
            min={1}
            value={draft.credit}
            onChange={(e) => update("credit", Math.max(1, Number(e.target.value)))}
            className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm text-ink"
          />
        </label>
        <TextField
          label="교수 (선택)"
          value={draft.professor}
          onChange={(v) => update("professor", v)}
        />
        <TextField
          label="분반 (선택)"
          value={draft.section}
          onChange={(v) => update("section", v)}
        />
        <TextField
          label="과목 그룹 ID (분반 묶음, 선택)"
          value={draft.group}
          onChange={(v) => update("group", v)}
        />
      </div>

      {/* 시간 슬롯 */}
      <div className="mt-3">
        <p className="mb-1 text-xs font-medium text-ink-soft">시간</p>
        <div className="flex flex-col gap-2">
          {draft.slots.map((slot, i) => (
            <div key={i} className="flex flex-wrap items-center gap-2">
              <select
                value={slot.day}
                onChange={(e) => updateSlot(i, { day: e.target.value as Weekday })}
                aria-label="요일"
                className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
              >
                {WEEKDAYS.map((d) => (
                  <option key={d} value={d}>
                    {WEEKDAY_LABEL[d]}
                  </option>
                ))}
              </select>
              <input
                type="time"
                value={slot.start}
                onChange={(e) => updateSlot(i, { start: e.target.value })}
                aria-label="시작 시간"
                className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm tabular-nums"
              />
              <span className="text-ink-faint">–</span>
              <input
                type="time"
                value={slot.end}
                onChange={(e) => updateSlot(i, { end: e.target.value })}
                aria-label="종료 시간"
                className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm tabular-nums"
              />
              {draft.slots.length > 1 && (
                <button
                  type="button"
                  onClick={() =>
                    setDraft((d) => ({ ...d, slots: d.slots.filter((_, idx) => idx !== i) }))
                  }
                  aria-label="이 시간 삭제"
                  className="rounded p-1 text-ink-faint hover:text-rose-600"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={() =>
            setDraft((d) => ({
              ...d,
              slots: [...d.slots, { day: "MON", start: "09:00", end: "10:30" }],
            }))
          }
          className="mt-1.5 text-xs font-medium text-brand-700 hover:underline"
        >
          + 시간 추가
        </button>
      </div>

      <div className="mt-3 flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg px-3 py-1.5 text-sm text-ink-soft hover:bg-slate-100"
        >
          취소
        </button>
        <button
          type="button"
          onClick={onConfirm}
          className="rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
        >
          추가
        </button>
      </div>
    </div>
  );
}

// ── Blackout 에디터 ───────────────────────────────────────────
function BlackoutEditor({
  windows,
  onChange,
}: {
  windows: BlackoutWindow[];
  onChange: (next: BlackoutWindow[]) => void;
}) {
  const [day, setDay] = useState<Weekday>("MON");
  const [start, setStart] = useState("18:00");
  const [end, setEnd] = useState("21:00");
  const [reason, setReason] = useState("");

  function add() {
    const s = hhmmToMinutes(start);
    const e = hhmmToMinutes(end);
    if (s === null || e === null || s >= e) return;
    onChange([
      ...windows,
      { days: [day], start_minute: s, end_minute: e, reason: reason.trim() || null },
    ]);
    setReason("");
  }

  return (
    <div className="flex flex-col gap-2">
      {windows.length > 0 && (
        <ul className="flex flex-wrap gap-2">
          {windows.map((w, i) => (
            <li
              key={i}
              className="flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-ink-soft"
            >
              {w.days.map((d) => WEEKDAY_LABEL[d]).join("·")} {minutesToHHMM(w.start_minute)}–
              {minutesToHHMM(w.end_minute)}
              {w.reason ? ` (${w.reason})` : ""}
              <button
                type="button"
                onClick={() => onChange(windows.filter((_, idx) => idx !== i))}
                aria-label="제외 시간대 삭제"
                className="text-ink-faint hover:text-rose-600"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={day}
          onChange={(e) => setDay(e.target.value as Weekday)}
          aria-label="요일"
          className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
        >
          {WEEKDAYS.map((d) => (
            <option key={d} value={d}>
              {WEEKDAY_LABEL[d]}
            </option>
          ))}
        </select>
        <input
          type="time"
          value={start}
          onChange={(e) => setStart(e.target.value)}
          aria-label="시작 시간"
          className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm tabular-nums"
        />
        <span className="text-ink-faint">–</span>
        <input
          type="time"
          value={end}
          onChange={(e) => setEnd(e.target.value)}
          aria-label="종료 시간"
          className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm tabular-nums"
        />
        <input
          type="text"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="사유 (선택)"
          aria-label="사유"
          className="w-24 rounded border border-slate-300 bg-white px-2 py-1.5 text-sm"
        />
        <button
          type="button"
          onClick={add}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-ink-soft hover:bg-slate-50"
        >
          추가
        </button>
      </div>
    </div>
  );
}

// ── 작은 입력 컴포넌트 ────────────────────────────────────────
function TextField({
  label,
  value,
  onChange,
  autoFocus,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  autoFocus?: boolean;
}) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex flex-col gap-1 text-xs text-ink-soft">
      {label}
      <input
        id={id}
        type="text"
        value={value}
        autoFocus={autoFocus}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-slate-300 bg-white px-2 py-1.5 text-sm text-ink"
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  invalid,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  invalid?: boolean;
}) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex flex-col gap-1 text-xs text-ink-soft">
      {label}
      <input
        id={id}
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={(e) => onChange(Number(e.target.value))}
        className={`w-24 rounded border bg-white px-2 py-1.5 text-sm text-ink ${
          invalid ? "border-rose-400" : "border-slate-300"
        }`}
      />
    </label>
  );
}

function SliderField({
  label,
  value,
  onChange,
  min,
  max,
  step,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
}) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex flex-col gap-1 text-xs text-ink-soft">
      <span className="flex justify-between">
        {label}
        <span className="tabular-nums text-ink">{value}</span>
      </span>
      <input
        id={id}
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="accent-brand-600"
      />
    </label>
  );
}
