/** 분(자정 기준) ↔ "HH:MM" 문자열 변환 및 격자 계산 헬퍼. */

import type { Course, TimeSlot, Weekday } from "../types/timetable";
import { WEEKDAYS } from "../types/timetable";

/** 분 → "HH:MM" (예: 540 → "09:00"). */
export function minutesToHHMM(minutes: number): string {
  const clamped = Math.max(0, Math.min(24 * 60, Math.round(minutes)));
  const h = Math.floor(clamped / 60);
  const m = clamped % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

/** "HH:MM" → 분. 형식이 잘못되면 null. */
export function hhmmToMinutes(value: string): number | null {
  const match = /^(\d{1,2}):(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const h = Number(match[1]);
  const m = Number(match[2]);
  if (h < 0 || h > 24 || m < 0 || m > 59) return null;
  const total = h * 60 + m;
  if (total > 24 * 60) return null;
  return total;
}

export interface GridBounds {
  startMinute: number; // 격자 상단 시각
  endMinute: number; // 격자 하단 시각
  days: Weekday[]; // 표시할 요일들
}

const DEFAULT_START = 9 * 60; // 09:00
const DEFAULT_END = 18 * 60; // 18:00

/**
 * 강의 목록에서 격자의 시간 범위와 표시 요일을 계산.
 * - 시간 범위: 데이터의 최소 시작/최대 종료를 1시간 단위로 내림/올림.
 *   최소 09:00–18:00 보장. 데이터 없으면 기본값.
 * - 요일: 월~금 기본. 데이터에 토/일이 있으면 추가.
 */
export function computeGridBounds(courses: Course[]): GridBounds {
  let minStart = DEFAULT_START;
  let maxEnd = DEFAULT_END;
  const usedDays = new Set<Weekday>();

  for (const course of courses) {
    for (const slot of course.times) {
      minStart = Math.min(minStart, slot.start_minute);
      maxEnd = Math.max(maxEnd, slot.end_minute);
      usedDays.add(slot.day);
    }
  }

  // 1시간 단위 정렬
  const startMinute = Math.floor(minStart / 60) * 60;
  const endMinute = Math.ceil(maxEnd / 60) * 60;

  // 월~금 기본 + 데이터에 등장한 토/일 추가 (요일 순서 유지)
  const base: Weekday[] = ["MON", "TUE", "WED", "THU", "FRI"];
  const days = WEEKDAYS.filter(
    (d) => base.includes(d) || usedDays.has(d),
  );

  return { startMinute, endMinute, days };
}

/** 격자 상단~하단을 1시간 간격으로 끊은 눈금(분) 배열. */
export function hourTicks(bounds: GridBounds): number[] {
  const ticks: number[] = [];
  for (let m = bounds.startMinute; m <= bounds.endMinute; m += 60) {
    ticks.push(m);
  }
  return ticks;
}

/** 같은 요일에서 두 시간 구간이 겹치는지. */
export function slotsOverlap(a: TimeSlot, b: TimeSlot): boolean {
  if (a.day !== b.day) return false;
  return a.start_minute < b.end_minute && b.start_minute < a.end_minute;
}
