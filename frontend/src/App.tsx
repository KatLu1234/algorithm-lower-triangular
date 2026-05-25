import { useEffect, useRef, useState } from "react";

import { ApiError, fetchSampleCourses, requestTimetable } from "./api/client";
import { NaturalLanguageInput } from "./components/NaturalLanguageInput";
import { PreferenceForm } from "./components/PreferenceForm";
import { ScheduleResult } from "./components/ScheduleResult";
import { EmptyState, ErrorState, LoadingState } from "./components/States";
import {
  buildPreferenceFromCourses,
  buildSamplePreference,
  buildSampleResult,
} from "./lib/sampleData";
import type { Course, PreferenceVector, SelectionResult } from "./types/timetable";

type Status = "initial" | "loading" | "result" | "empty" | "error";

export default function App() {
  // 폼 초기값 = 내장 샘플 선호 (서버 연결 전 fallback).
  // 마운트 직후 서버에서 sample_data.csv 파싱본을 받아 교체한다.
  const [samplePreference, setSamplePreference] = useState<PreferenceVector>(
    () => buildSamplePreference(),
  );

  const [status, setStatus] = useState<Status>("initial");
  const [result, setResult] = useState<SelectionResult | null>(null);
  const [poolCourses, setPoolCourses] = useState<Course[]>(samplePreference.courses);
  const [errorMessage, setErrorMessage] = useState("");
  const [resolutionHint, setResolutionHint] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [isSample, setIsSample] = useState(false);
  // PreferenceForm은 initial을 mount 시점에만 읽으므로, LLM이 새 preference를
  // 적용했을 때 강제로 remount하려고 key용 카운터를 둠.
  const [formVersion, setFormVersion] = useState(0);

  const lastPref = useRef<PreferenceVector | null>(null);

  // 초기 로드: 서버에서 국민대 sample_data.csv 파싱본을 받아 후보 풀로 채움.
  // 실패(서버 미가용·CSV 없음) 시 내장 샘플을 그대로 사용 — 화면은 계속 떠 있음.
  useEffect(() => {
    let aborted = false;
    fetchSampleCourses()
      .then(({ courses }) => {
        if (aborted || courses.length === 0) return;
        const pref = buildPreferenceFromCourses(courses);
        setSamplePreference(pref);
        setPoolCourses(courses);
      })
      .catch(() => {
        // 서버 미가용 — 내장 샘플 유지. 콘솔로만 알린다.
        console.warn("[sample-courses] 서버에서 강의 풀을 받지 못해 내장 샘플을 사용합니다.");
      });
    return () => {
      aborted = true;
    };
  }, []);

  async function runSolve(pref: PreferenceVector) {
    lastPref.current = pref;
    setIsSample(false);
    setPoolCourses(pref.courses);
    setStatus("loading");
    try {
      const res = await requestTimetable({ preference: pref, top_n: 3, explain: false });
      if (res.infeasibility) {
        setResolutionHint(res.infeasibility.resolution_hint ?? res.infeasibility.detail);
        setStatus("empty");
        return;
      }
      if (!res.selection || res.selection.ranked_schedules.length === 0) {
        setResolutionHint(null);
        setStatus("empty");
        return;
      }
      setResult(res.selection);
      setExplanation(res.explanation ?? null);
      setStatus("result");
    } catch (err) {
      setErrorMessage(
        err instanceof ApiError
          ? err.message
          : "예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
      );
      setStatus("error");
    }
  }

  function previewSample() {
    setIsSample(true);
    setPoolCourses(samplePreference.courses);
    setResult(buildSampleResult());
    setExplanation(null);
    setStatus("result");
  }

  return (
    <div className="min-h-full">
      {/* 헤더 */}
      <header className="border-b border-cream-300 bg-cream-50">
        <div className="mx-auto flex max-w-7xl flex-col gap-1 px-6 py-5">
          <h1 className="text-xl font-bold text-brand-700">시간표 만들기</h1>
          <p className="text-sm text-ink-soft">
            강의 후보를 입력하면 시간 충돌·학점·이동시간·중요도를 함께 고려한 최적
            시간표를 추천하고, <b>왜 그 결과가 나왔는지</b>를 강의 단위로 설명합니다.
          </p>
        </div>
      </header>

      {/* 본문: 좌 입력 / 우 결과 (PC 우선 — product.md §2.3) */}
      <main className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[380px_minmax(0,1fr)]">
        {/* 입력 폼. min-w-0이 빠지면 grid item이 자식의 intrinsic width로 자라
            380px 트랙을 깨뜨림 — 자식의 truncate/overflow 효과가 안 먹음 */}
        <div className="lg:sticky lg:top-6 lg:self-start space-y-4 min-w-0">
          {/* 자연어 입력 — LLM-A가 PreferenceVector로 변환해 폼을 채움 */}
          <NaturalLanguageInput
            currentPreference={samplePreference}
            onApply={(next) => {
              setSamplePreference(next);
              setPoolCourses(next.courses);
              setFormVersion((v) => v + 1);
            }}
          />
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <PreferenceForm
              key={formVersion}
              initial={samplePreference}
              submitting={status === "loading"}
              onSubmit={runSolve}
              onPreviewSample={previewSample}
            />
          </div>
        </div>

        {/* 결과 */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:min-h-[32rem]">
          {status === "initial" && <EmptyState variant="initial" />}
          {status === "loading" && <LoadingState />}
          {status === "empty" && (
            <EmptyState variant="no-result" resolutionHint={resolutionHint} />
          )}
          {status === "error" && (
            <ErrorState
              message={errorMessage}
              onRetry={() => {
                if (lastPref.current) void runSolve(lastPref.current);
                else setStatus("initial");
              }}
            />
          )}
          {status === "result" && result && (
            <ScheduleResult
              courses={poolCourses}
              result={result}
              explanation={explanation}
              isSample={isSample}
            />
          )}
        </div>
      </main>
    </div>
  );
}
