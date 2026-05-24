import { useState } from "react";

import { ApiError, parsePreference } from "../api/client";
import type { PreferenceVector } from "../types/timetable";

/** 지원·미지원 항목 — UI에 항상 노출되는 *정적* 안내.
 *
 *  권위 있는 출처: `claude/llm-include/prompts/preference_extract.md`의
 *  "지원 필드" / "미지원" 절. 두 파일이 어긋나면 prompt가 진실.
 */
const SUPPORTED: { label: string; example: string }[] = [
  { label: "학점 한도", example: "12학점 이상 18학점까지" },
  { label: "필수 / 제외 강의 (이름·코드)", example: "운영체제는 꼭 듣고, 글쓰기는 빼주세요" },
  { label: "필수 / 제외 과목 그룹 (분반 무관)", example: "자료구조는 어떤 분반이라도 듣고 싶어요" },
  { label: "교수 선호", example: "조민호 교수님 강의 듣고 싶어요" },
  { label: "blackout 시간대", example: "월요일 오전, 금요일 통학으로 비워주세요" },
  { label: "카테고리 가중치 (전공/교양)", example: "전공 위주로 들을게요" },
  { label: "이수 요건 가중치 (필수/선택)", example: "필수 강의 우선" },
  { label: "건물 선호", example: "공학관 위주로" },
  { label: "활성 요일 목표", example: "주 4일만 학교 가고 싶어요" },
  { label: "연강·공강 선호", example: "공강 만들지 마세요 / 연강 싫어요" },
  { label: "이동·압축 가중치", example: "이동 부담 줄여줘 / 압축적으로" },
];

const UNSUPPORTED: { label: string; reason: string }[] = [
  { label: "강의 평가·교수 평점·인기 강의", reason: "평점 데이터를 보유하지 않습니다." },
  { label: "선수강·학년 자동 처리", reason: "이수 조건 데이터가 없습니다 — 후보 강의는 그대로 받습니다." },
  { label: "친구 시간표 매칭", reason: "다른 학생 데이터를 사용하지 않습니다." },
  { label: "다음 학기 커리큘럼 추천", reason: "단일 학기만 다룹니다." },
  { label: "오전/오후 한정 같은 슬롯 페널티", reason: "blackout으로 명시하시면 적용됩니다." },
  { label: "교양·전공 학점 비율 자동 조정", reason: "비율보다 가중치로 표현합니다 — '전공 위주' 등." },
];

interface Props {
  /** 현재 폼에 들어 있는 PreferenceVector — LLM이 컨텍스트로 사용. */
  currentPreference: PreferenceVector;
  /** LLM이 반환한 새 PreferenceVector를 상위 폼에 적용. */
  onApply: (next: PreferenceVector) => void;
}

export function NaturalLanguageInput({ currentPreference, onApply }: Props) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [applied, setApplied] = useState<string[]>([]);
  const [unsupported, setUnsupported] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [helpOpen, setHelpOpen] = useState(false);

  async function submit() {
    if (!text.trim()) return;
    setBusy(true);
    setErrorMessage("");
    setApplied([]);
    setUnsupported([]);
    try {
      const res = await parsePreference({
        text: text.trim(),
        preference: currentPreference,
      });
      onApply(res.preference);
      setApplied(res.applied);
      setUnsupported(res.unsupported);
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : "자연어 변환 요청을 처리하지 못했습니다.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-lg border border-cream-300 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-ink">자연어로 시간표 설정</h2>
        <button
          type="button"
          className="text-xs text-brand-700 underline-offset-2 hover:underline"
          onClick={() => setHelpOpen((v) => !v)}
        >
          {helpOpen ? "닫기" : "어떤 표현이 가능한가요?"}
        </button>
      </div>

      <p className="mb-2 text-xs text-ink-soft">
        예) "전공 위주로 듣고 금요일은 통학이라 비워주세요. 조민호 교수님 운영체제는 꼭 듣고
        싶어요." → 자동으로 가중치·blackout·교수 선호를 폼에 채워 줍니다.
      </p>

      <textarea
        className="block w-full resize-y rounded-md border border-cream-300 bg-cream-50 p-2 text-sm text-ink placeholder:text-ink-faint focus:border-brand-400 focus:outline-none focus:ring-1 focus:ring-brand-300"
        rows={3}
        maxLength={2000}
        placeholder="원하는 시간표를 자유롭게 적어 보세요 (한국어)"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={busy}
      />

      <div className="mt-2 flex items-center justify-between gap-3">
        <button
          type="button"
          className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm disabled:cursor-not-allowed disabled:opacity-60 hover:bg-brand-700"
          onClick={submit}
          disabled={busy || text.trim().length === 0}
        >
          {busy ? "변환 중..." : "자동 채우기"}
        </button>
        <span className="text-xs text-ink-faint">
          ⚠️ LLM이 폼만 채워 줍니다 — 시간표는 그 다음 알고리즘이 결정합니다.
        </span>
      </div>

      {/* 응답 결과 표시 */}
      {errorMessage && (
        <p className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {errorMessage}
        </p>
      )}
      {applied.length > 0 && (
        <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2">
          <h3 className="text-xs font-semibold text-emerald-900">이해해서 적용한 항목</h3>
          <ul className="mt-1 list-disc pl-5 text-sm text-emerald-900">
            {applied.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}
      {unsupported.length > 0 && (
        <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2">
          <h3 className="text-xs font-semibold text-amber-900">이해 못 했거나 지원 범위 밖</h3>
          <ul className="mt-1 list-disc pl-5 text-sm text-amber-900">
            {unsupported.map((u, i) => (
              <li key={i}>{u}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 정적 안내 패널 */}
      {helpOpen && (
        <div className="mt-3 grid gap-3 rounded-md border border-cream-300 bg-cream-50 px-3 py-3 sm:grid-cols-2">
          <div>
            <h3 className="mb-1 text-xs font-semibold text-emerald-800">✓ 가능한 표현</h3>
            <ul className="space-y-1 text-xs text-ink">
              {SUPPORTED.map((s) => (
                <li key={s.label}>
                  <span className="font-medium">{s.label}</span>
                  <span className="text-ink-soft"> — “{s.example}”</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="mb-1 text-xs font-semibold text-rose-800">✗ 불가능 / 지원 안 함</h3>
            <ul className="space-y-1 text-xs text-ink">
              {UNSUPPORTED.map((u) => (
                <li key={u.label}>
                  <span className="font-medium">{u.label}</span>
                  <span className="text-ink-soft"> — {u.reason}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
