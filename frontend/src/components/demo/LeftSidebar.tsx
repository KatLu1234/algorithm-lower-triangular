/**
 * 좌측 사이드바 — 계정 상태 / 저장한 과목 / 새 대화 / 지난 대화.
 *
 * 사양: frontend/docs/demo-layout.md §2.1.
 * - "저장한 과목" 이 `PreferenceVector.courses` 원천. 여기서 추가·제거하면
 *   중앙·우측이 재계산된다.
 * - 데모는 메모리 상태 — DB 영속화는 후속(§8.3).
 * - 계정 영역은 currentUser 기반(이미 로그인된 상태가 가정).
 * - 지난 대화는 더미 placeholder.
 */

import type { Course, CourseId } from "../../types/timetable";
import type { UserPublic } from "../../api/auth";

interface LeftSidebarProps {
  currentUser: UserPublic;
  /** 풀에 들어 있는 모든 강의 (검색·추가 드롭다운에서 사용). */
  catalog: Course[];
  /** 사용자가 모아둔 저장된 강의 id 목록 — PreferenceVector.courses 의 원천. */
  savedIds: CourseId[];
  onToggleSaved: (id: CourseId) => void;
  /** "새 대화" — 현재 채팅·결과 초기화. */
  onNewConversation: () => void;
}

export function LeftSidebar({
  currentUser,
  catalog,
  savedIds,
  onToggleSaved,
  onNewConversation,
}: LeftSidebarProps) {
  const savedSet = new Set(savedIds);
  const saved = catalog.filter((c) => savedSet.has(c.id));
  const unsaved = catalog.filter((c) => !savedSet.has(c.id));

  const initial = (currentUser.display_name || currentUser.email).trim().charAt(0).toUpperCase();

  return (
    <div className="flex flex-col gap-5 px-4 py-4 text-sm">
      {/* 계정 상태 */}
      <section aria-label="계정">
        <div className="flex items-center gap-3 rounded-lg bg-white p-3 shadow-sm">
          <span
            aria-hidden="true"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white"
          >
            {initial}
          </span>
          <div className="min-w-0 leading-tight">
            <p className="truncate font-medium text-ink" title={currentUser.email}>
              {currentUser.display_name || currentUser.email}
            </p>
            <p className="truncate text-xs text-ink-faint">고려대 · 2026-1학기</p>
          </div>
        </div>
      </section>

      {/* 새 대화 */}
      <section>
        <button
          type="button"
          onClick={onNewConversation}
          className="w-full rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-left text-sm font-medium text-brand-700 transition hover:bg-brand-100"
        >
          + 새 대화 시작
        </button>
      </section>

      {/* 저장한 과목 */}
      <section aria-label="저장한 과목">
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">
          저장한 과목 <span className="font-normal text-ink-faint/80">({saved.length})</span>
        </h2>
        {saved.length === 0 ? (
          <p className="rounded-md bg-white px-3 py-2 text-xs text-ink-faint">
            오른쪽 채팅으로 시작하거나 아래 후보 중에서 골라 보세요.
          </p>
        ) : (
          <ul className="space-y-1">
            {saved.map((c) => (
              <li key={c.id}>
                <CoursePill course={c} saved onClick={() => onToggleSaved(c.id)} />
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* 후보 (저장 안 한 강의) — 칩 클릭으로 저장에 추가 */}
      {unsaved.length > 0 && (
        <section aria-label="후보 강의">
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">
            후보 강의 <span className="font-normal text-ink-faint/80">({unsaved.length})</span>
          </h2>
          <ul className="space-y-1">
            {unsaved.slice(0, 12).map((c) => (
              <li key={c.id}>
                <CoursePill course={c} saved={false} onClick={() => onToggleSaved(c.id)} />
              </li>
            ))}
          </ul>
          {unsaved.length > 12 && (
            <p className="mt-1 text-[11px] text-ink-faint">
              +{unsaved.length - 12}개 더 — 검색은 후속
            </p>
          )}
        </section>
      )}

      {/* 지난 대화 — 더미 (사양서 §0 — 데모 한정 placeholder) */}
      <section aria-label="지난 대화">
        <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-faint">
          지난 대화
        </h2>
        <ul className="space-y-1 text-xs text-ink-soft">
          <li className="truncate rounded-md px-2 py-1.5 hover:bg-cream-200" title="더미">
            전공 위주 15학점 (어제)
          </li>
          <li className="truncate rounded-md px-2 py-1.5 hover:bg-cream-200" title="더미">
            월요일 공강 만들기 (지난주)
          </li>
        </ul>
        <p className="mt-1 text-[11px] text-ink-faint">
          ⓘ 데모용 더미. 영속화는 후속.
        </p>
      </section>
    </div>
  );
}

interface CoursePillProps {
  course: Course;
  saved: boolean;
  onClick: () => void;
}

function CoursePill({ course, saved, onClick }: CoursePillProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={saved}
      title={
        saved
          ? `${course.name} 저장 해제`
          : `${course.name} 저장에 추가`
      }
      className={`flex w-full items-center justify-between gap-2 rounded-md px-2.5 py-1.5 text-left text-xs transition ${
        saved
          ? "bg-white text-ink shadow-sm hover:bg-cream-50"
          : "bg-cream-100 text-ink-soft hover:bg-white"
      }`}
    >
      <span className="min-w-0 flex-1 truncate">
        <span className="font-medium text-ink">{course.name}</span>
        {course.section && (
          <span className="text-ink-faint"> · {course.section}분반</span>
        )}
        <span className="text-ink-faint"> · {course.credit}학점</span>
      </span>
      <span
        aria-hidden="true"
        className={`shrink-0 text-base leading-none ${saved ? "text-brand-600" : "text-ink-faint"}`}
      >
        {saved ? "−" : "+"}
      </span>
    </button>
  );
}
