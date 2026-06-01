/**
 * 앱 진입점.
 *
 * 흐름: 인증 게이트(로그인 안 됨 → Login) → DemoApp(3-column 데모 페이지).
 * 데모 페이지 사양: frontend/docs/demo-layout.md.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { fetchMe, getToken, logout, type UserPublic } from "./api/auth";
import { ApiError, fetchSampleCourses, parsePreference, requestTimetable } from "./api/client";
import { Login } from "./components/Login";
import { LoadingState } from "./components/States";
import { CenterPanel, type CenterStatus, type ChatMessage } from "./components/demo/CenterPanel";
import { DemoLayout } from "./components/demo/DemoLayout";
import { LeftSidebar } from "./components/demo/LeftSidebar";
import { ScheduleList } from "./components/demo/ScheduleList";
import {
  buildPreferenceFromCourses,
  buildSamplePreference,
  buildSampleResult,
} from "./lib/sampleData";
import type {
  Course,
  CourseId,
  PreferenceVector,
  SelectionResult,
} from "./types/timetable";

type AuthStatus = "checking" | "anonymous" | "authenticated";

export default function App() {
  // 인증 상태. 초기 마운트 시 localStorage 의 토큰으로 /auth/me 한번 검증.
  const [authStatus, setAuthStatus] = useState<AuthStatus>(() =>
    getToken() ? "checking" : "anonymous",
  );
  const [currentUser, setCurrentUser] = useState<UserPublic | null>(null);
  const [welcome, setWelcome] = useState<string | null>(null);

  useEffect(() => {
    if (authStatus !== "checking") return;
    let aborted = false;
    fetchMe()
      .then((user) => {
        if (aborted) return;
        if (user) {
          setCurrentUser(user);
          setAuthStatus("authenticated");
        } else {
          setAuthStatus("anonymous");
        }
      })
      .catch(() => {
        if (!aborted) setAuthStatus("anonymous");
      });
    return () => {
      aborted = true;
    };
  }, [authStatus]);

  async function handleLogout() {
    await logout();
    setCurrentUser(null);
    setAuthStatus("anonymous");
  }

  if (authStatus === "checking") {
    return (
      <div className="flex min-h-full items-center justify-center bg-cream-100">
        <LoadingState message="세션을 확인하는 중…" />
      </div>
    );
  }

  if (authStatus === "anonymous") {
    return (
      <Login
        onAuthenticated={(user, mode) => {
          setCurrentUser(user);
          setAuthStatus("authenticated");
          if (mode === "signup") {
            setWelcome(
              `환영합니다, ${user.display_name || user.email}님! 계정이 만들어졌어요.`,
            );
          }
        }}
      />
    );
  }

  return (
    <DemoApp
      currentUser={currentUser!}
      onLogout={handleLogout}
      welcome={welcome}
      onDismissWelcome={() => setWelcome(null)}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 데모 페이지 — 3-column

interface DemoAppProps {
  currentUser: UserPublic;
  onLogout: () => void;
  welcome: string | null;
  onDismissWelcome: () => void;
}

function DemoApp({ currentUser, onLogout, welcome, onDismissWelcome }: DemoAppProps) {
  // 강의 카탈로그(전체 풀) — 서버에서 받거나 fallback 으로 내장 샘플 사용.
  const [catalog, setCatalog] = useState<Course[]>(() => buildSamplePreference().courses);
  // 사용자가 저장한 강의(= PreferenceVector.courses 원천).
  const [savedIds, setSavedIds] = useState<CourseId[]>(() =>
    buildSamplePreference().courses.map((c) => c.id),
  );
  // 현재 선호(자연어 채팅으로 누적 갱신). 카탈로그가 바뀌면 동기화.
  const [preference, setPreference] = useState<PreferenceVector>(() => buildSamplePreference());

  // 결과·상태.
  const [result, setResult] = useState<SelectionResult | null>(() => buildSampleResult());
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isSample, setIsSample] = useState(true); // 초기엔 샘플
  const [centerKind, setCenterKind] = useState<
    "result" | "loading" | "empty" | "infeasible" | "error"
  >("result");
  const [errorMessage, setErrorMessage] = useState("");
  const [resolutionHint, setResolutionHint] = useState<string | null>(null);

  // 채팅.
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      role: "assistant",
      tone: "info",
      text:
        "안녕하세요! 자연어로 조건을 입력하면 시간표를 다시 만들어 드려요.\n예: '월 공강, 전공 위주 15학점' / '이동 시간 줄여줘'.\n현재 화면은 디자인 미리보기용 샘플 결과입니다.",
    },
  ]);
  const [chatBusy, setChatBusy] = useState(false);

  // 마지막으로 적용된 preference 추적 (재시도/로그용).
  const lastPrefRef = useRef<PreferenceVector | null>(null);

  // 초기 로드 — 서버에서 강의 풀을 받아 카탈로그·저장 목록을 교체.
  useEffect(() => {
    let aborted = false;
    fetchSampleCourses()
      .then(({ courses }) => {
        if (aborted || courses.length === 0) return;
        const pref = buildPreferenceFromCourses(courses);
        setCatalog(courses);
        setSavedIds(courses.map((c) => c.id));
        setPreference(pref);
      })
      .catch(() => {
        console.warn(
          "[sample-courses] 서버에서 강의 풀을 받지 못해 내장 샘플을 사용합니다.",
        );
      });
    return () => {
      aborted = true;
    };
  }, []);

  // 저장 강의 변경 → preference.courses 동기화.
  useEffect(() => {
    setPreference((prev) => {
      const idSet = new Set(savedIds);
      const next = catalog.filter((c) => idSet.has(c.id));
      // 강의가 같으면 참조 그대로(불필요한 리렌더 방지).
      if (
        prev.courses.length === next.length &&
        prev.courses.every((c, i) => c.id === next[i]?.id)
      ) {
        return prev;
      }
      return { ...prev, courses: next };
    });
  }, [savedIds, catalog]);

  const toggleSaved = useCallback((id: CourseId) => {
    setSavedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  function startNewConversation() {
    setMessages([
      {
        role: "assistant",
        tone: "info",
        text: "새 대화를 시작했어요. 어떤 시간표가 필요하세요?",
      },
    ]);
    setResult(buildSampleResult());
    setIsSample(true);
    setSelectedIndex(0);
    setCenterKind("result");
  }

  async function runSolve(pref: PreferenceVector): Promise<void> {
    lastPrefRef.current = pref;
    setCenterKind("loading");
    try {
      const res = await requestTimetable({ preference: pref, top_n: 3, explain: false });
      if (res.infeasibility) {
        setResolutionHint(res.infeasibility.resolution_hint ?? res.infeasibility.detail);
        setCenterKind("infeasible");
        appendAssistant(
          res.infeasibility.resolution_hint ?? res.infeasibility.detail,
          "info",
        );
        return;
      }
      if (!res.selection || res.selection.ranked_schedules.length === 0) {
        setResolutionHint(null);
        setCenterKind("infeasible");
        appendAssistant("조건을 만족하는 후보를 찾지 못했어요.", "info");
        return;
      }
      setResult(res.selection);
      setIsSample(false);
      setSelectedIndex(0);
      setCenterKind("result");
      appendAssistant(summarizeResult(res.selection));
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.message
          : "예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.";
      setErrorMessage(msg);
      setCenterKind("error");
      appendAssistant(msg, "info");
    }
  }

  function appendAssistant(text: string, tone?: "info") {
    setMessages((prev) => [...prev, { role: "assistant", text, ...(tone ? { tone } : {}) }]);
  }

  async function handleSendMessage(text: string) {
    setMessages((prev) => [...prev, { role: "user", text }]);
    setChatBusy(true);

    // 1) 자연어 → preference delta. LLM 미가용이면 graceful fallback.
    let nextPref = preference;
    try {
      const parsed = await parsePreference({ text, preference });
      nextPref = parsed.preference;
      setPreference(nextPref);
      // 이해 못 한 항목이 있으면 한 줄로 알림.
      if (parsed.applied.length > 0) {
        appendAssistant(`적용했어요: ${parsed.applied.join(", ")}`);
      }
      if (parsed.unsupported.length > 0) {
        appendAssistant(
          `이건 아직 처리하지 못했어요: ${parsed.unsupported.join(", ")}`,
          "info",
        );
      }
    } catch (err) {
      // LLM 비활성/타임아웃 — 현재 preference 그대로 알고리즘만 돌린다.
      const reason =
        err instanceof ApiError ? err.message : "자연어 변환을 사용할 수 없었어요.";
      appendAssistant(
        `${reason} 현재 저장된 조건으로 계산해 볼게요.`,
        "info",
      );
    }

    // 2) 알고리즘 호출.
    await runSolve(nextPref);
    setChatBusy(false);
  }

  // CenterStatus 조립.
  const centerStatus: CenterStatus = useMemo(() => {
    if (centerKind === "loading") return { kind: "loading" };
    if (centerKind === "empty") return { kind: "empty" };
    if (centerKind === "infeasible")
      return { kind: "infeasible", resolutionHint };
    if (centerKind === "error")
      return {
        kind: "error",
        message: errorMessage,
        onRetry: lastPrefRef.current
          ? () => void runSolve(lastPrefRef.current!)
          : undefined,
      };
    if (result) {
      return { kind: "result", selection: result, selectedIndex, isSample };
    }
    return { kind: "empty" };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [centerKind, result, selectedIndex, isSample, errorMessage, resolutionHint]);

  return (
    <DemoLayout
      currentUser={currentUser}
      onLogout={onLogout}
      welcome={welcome}
      onDismissWelcome={onDismissWelcome}
      left={
        <LeftSidebar
          currentUser={currentUser}
          catalog={catalog}
          savedIds={savedIds}
          onToggleSaved={toggleSaved}
          onNewConversation={startNewConversation}
        />
      }
      center={
        <CenterPanel
          status={centerStatus}
          catalog={catalog}
          messages={messages}
          chatBusy={chatBusy}
          onSendMessage={handleSendMessage}
        />
      }
      right={
        <ScheduleList
          candidates={result?.ranked_schedules ?? []}
          catalog={catalog}
          selectedIndex={selectedIndex}
          onSelect={(i) => {
            setSelectedIndex(i);
            setCenterKind("result");
          }}
          isSample={isSample}
        />
      }
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 결과 요약 (채팅에 표시할 한 줄).

function summarizeResult(sel: SelectionResult): string {
  const top = sel.ranked_schedules[0];
  if (!top) return "후보를 찾지 못했어요.";
  const count = sel.ranked_schedules.length;
  return `${count}개 후보를 찾았어요. 추천 1번은 ${top.used_credit}학점·${top.courses.length}과목입니다.`;
}
