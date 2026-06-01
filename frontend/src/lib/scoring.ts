/**
 * ScoreBreakdown 요약 헬퍼.
 *
 * 알고리즘 트리의 가치 함수는 "10개 항의 합" 이므로 (`types/timetable.ts` SCORE_TERMS),
 * 카드 표시용 총점은 단순 누계로 충분하다. 음수 페널티 항이 음수 값을 가지므로
 * 그대로 더하면 됨.
 */

import type { ScoreBreakdown } from "../types/timetable";
import { SCORE_TERMS } from "../types/timetable";

/** ScoreBreakdown 의 10개 항을 단순 합산한 총점. 정수 반올림. */
export function totalScore(breakdown: ScoreBreakdown): number {
  let sum = 0;
  for (const t of SCORE_TERMS) sum += breakdown[t.key] ?? 0;
  return Math.round(sum);
}
