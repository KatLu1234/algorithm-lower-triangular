# 페이지: `/timetable` — 시간표 짜기

> 페이지 설계 문서 — 한 페이지당 한 파일. 전체 목록·라우팅은 [`index.md`](./index.md).
> 공통 작성 항목은 `index.md` §8.

## 1. 목적

사용자가 모은 **내 풀(`Course[]`)** 을 입력으로 받아, 학점·시간 충돌·이동시간·중요도를 같이 고려한 **추천 시간표 N개**를 보여주고, *왜* 그 결과가 나왔는지를 강의 단위로 설명한다.

product 우선순위와의 매핑:
- 1순위 **정확성** — 결과는 항상 알고리즘이 결정한다. LLM은 자연어→PreferenceVector delta 추출에만 관여(`product.md` §4.4 LLM 불변항).
- 2순위 **설명 가능성** — `SelectionResult.course_rationale` 의 stage_code·detail을 시각화.
- 3순위 **불가능 안내** — `InfeasibilityReport.resolution_hint` 그대로 표시.

## 2. 진입 경로

- URL: `/timetable`
- 인증 필요: 예 (`<ProtectedRoute>`)
- 어디서 오는가: 메인 "시간표 짜기" 카드, 강의 검색 페이지의 "시간표 짜러 가기" 버튼

## 3. 레이아웃

데스크톱 우선 2-단(현재 `App.tsx` 의 TimetableApp 구조 계승):

```
┌────────────────────────────────────────────────────────────────────┐
│ [로고] 시간표 짜기                       사용자명  [로그아웃]          │
├────────────────────────────────────────────────────────────────────┤
│  ┌──────── 좌 (380px) ─────────┐  ┌────────── 우 (가변) ──────────┐  │
│  │  [자연어 입력 박스]            │  │   결과 영역                  │  │
│  │   "월 공강, 전공 위주 15학점"   │  │   - 초기: EmptyState         │  │
│  │   → 폼을 LLM이 채움            │  │   - 로딩: LoadingState        │  │
│  │                              │  │   - 결과: ScheduleResult      │  │
│  │  [PreferenceForm]            │  │     · 상단 ranked_schedules    │  │
│  │   · 학점 범위·이동가중치 등      │  │       카드 N개 (총점·미니격자) │  │
│  │   · 내 풀이 후보 강의로 들어옴   │  │     · 선택 카드의 주간 격자     │  │
│  │   · [추천 받기] 버튼          │  │     · 강의별 사유(course_rationale)│  │
│  │   · [샘플 미리보기]            │  │   - 불가능/빈: EmptyState     │  │
│  │                              │  │     + resolution_hint         │  │
│  │  내 풀: 12 강의               │  │   - 에러: ErrorState + 재시도  │  │
│  │  (편집은 강의 검색에서)         │  │                              │  │
│  └──────────────────────────────┘  └──────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

- 좌측은 `lg:sticky lg:top-6` 으로 스크롤 따라옴(현재 코드 유지).
- "내 풀 편집은 강의 검색에서"로 안내 — 페이지 책임을 좁힌다.

## 4. 상태(state)

페이지 로컬:
- `status: "initial" | "loading" | "result" | "empty" | "error"` (현재 App.tsx 그대로)
- `preference: PreferenceVector` — 폼 현재 값
- `result: SelectionResult | null`
- `explanation: string | null` (현재는 LLM 미연결로 항상 null)
- `errorMessage: string`, `resolutionHint: string | null`
- `isSample: boolean` — "샘플 미리보기"로 채워졌는지 (가짜를 진짜처럼 위조하지 않도록 배지)
- `formVersion: number` — LLM이 폼을 갈아끼울 때 PreferenceForm을 강제 remount 하기 위한 키

페이지 진입 시 초기 후보 풀:
1. 전역 컨텍스트의 `myPool: Course[]` 이 있으면 그것으로 폼 초기화.
2. 없으면 `GET /timetable/sample-courses` 로 서버의 sample_data.csv 파싱본을 받아 채움(현재 `App.tsx` 동작 그대로).
3. 둘 다 실패하면 `buildSamplePreference()` 내장 샘플.

## 5. 사용 API

| 메서드 | 경로 | 요청 | 응답 | 출처 |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/timetable/sample-courses` | — | `SampleCoursesResponse { courses, source }` | `app/api/endpoints/timetable.py` |
| POST | `/api/v1/timetable/parse-preference` | `ParsePreferenceRequest { text, preference }` | `ParsePreferenceResponse { preference, applied, unsupported }` | 동상 |
| POST | `/api/v1/timetable/solve` | `TimetableRequest { preference, top_n, explain }` | `TimetableResponse { selection?, infeasibility?, explanation? }` | 동상 |

에러 코드 매핑 (본 페이지에서 표시할 친화 메시지):

| code | HTTP | 친화 메시지 |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | "입력값을 확인해 주세요. (학점·시간 등)" |
| `LLM_UNAVAILABLE` | 503 | "자연어 입력은 잠시 사용할 수 없어요. 폼으로 직접 입력해 주세요." (자연어 박스만 비활성, 폼은 계속 동작) |
| `LLM_TIMEOUT` | 504 | "자연어 해석이 지연됐어요. 잠시 후 다시 시도해 주세요." |
| `LLM_BAD_RESPONSE` | 502 | "자연어 해석 결과를 알아볼 수 없어요. 폼으로 입력해 주세요." |
| `INTERNAL` | 500 | "예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해 주세요." + 재시도 |

> `infeasibility` 가 와도 HTTP는 200이라는 점을 잊지 말 것 (`base/architecture.md` §5.1). 에러가 아닌 정상 분기로 다룬다.

## 6. 컴포넌트 분해

```
<TimetablePage>
├─ <Header />                        // 공통 셸
└─ <TwoColumn>
   ├─ <LeftPane>
   │   ├─ <NaturalLanguageInput      // 기존 컴포넌트 재사용
   │   │     currentPreference
   │   │     onApply />              // LLM-A 결과 → setPreference, formVersion++
   │   ├─ <PreferenceForm            // 기존
   │   │     key={formVersion}
   │   │     initial={preference}
   │   │     submitting
   │   │     onSubmit={runSolve}
   │   │     onPreviewSample={previewSample} />
   │   └─ <PoolSummary count={pool.length} editHref="/courses" />
   └─ <RightPane>
       ├─ status==='initial' → <EmptyState variant='initial' />
       ├─ status==='loading' → <LoadingState />
       ├─ status==='empty'   → <EmptyState variant='no-result' resolutionHint />
       ├─ status==='error'   → <ErrorState message onRetry />
       └─ status==='result'  → <ScheduleResult courses result explanation isSample />
```

재사용 자산(현재 코드에 이미 있음): `NaturalLanguageInput`, `PreferenceForm`, `ScheduleResult`, `TimetableGrid`, `States`(Empty/Loading/Error), `src/api/client.ts`, `src/lib/sampleData.ts`, `src/lib/time.ts`. 신규 필요: `<PoolSummary>` (작은 요약 + 강의 검색으로 가는 링크).

## 7. 인터랙션 (Happy Path)

1. 진입 시 후보 풀 결정(§4 §5의 초기 풀 선택 절차).
2. 사용자가 자연어 박스에 입력(예: "월요일 공강, 전공 위주 15학점") → `POST /parse-preference` → 응답의 `preference` 로 폼 갱신(`formVersion++` 로 remount), `applied`·`unsupported` 라벨을 자연어 박스 아래 칩으로 표시.
3. 사용자가 폼에서 학점·가중치 등을 미세 조정 후 "추천 받기".
4. `POST /solve` 호출, `status="loading"`.
5. 응답 분기:
   - `infeasibility` → `status="empty"`, `resolutionHint = infeasibility.resolution_hint ?? infeasibility.detail`
   - `selection.ranked_schedules.length === 0` → `status="empty"`, hint=null
   - 그 외 → `status="result"`, `result = selection`, `explanation = response.explanation ?? null`
6. 결과 영역에서 사용자는 후보 카드 클릭 → 주간 격자가 그 후보로 갱신. 카드 옆 "왜 X는 빠졌나요?" 같은 액션은 `course_rationale[id].detail` 노출.
7. 다시 조정하고 싶으면 좌측 폼/자연어로 돌아가 재호출.

## 8. 상태 — 로딩 / 에러 / 빈

- **초기(빈)**: "왼쪽에서 조건을 정하고 추천 받기를 눌러 보세요." 빈 풀이면 "먼저 [강의 검색](/courses)에서 강의를 모아 주세요." 안내 1줄 추가.
- **로딩**: 결과 영역에 LoadingState. 폼은 비활성(`submitting=true`), 더블 클릭 방지.
- **빈(결과 없음/불가능)**: `resolutionHint` 가 있으면 그대로 노출(서버 detail 가공 X — 이미 친화 톤). 풀이 작거나 must_include 강한 경우의 힌트를 그대로 신뢰.
- **에러**: `{detail, code}` 의 detail을 노출하지 않고 §5 표의 친화 메시지로. ErrorState에 재시도 버튼.
- **샘플 미리보기**: `isSample=true` 면 결과 위에 "샘플" 배지 — 가짜 결과를 진짜처럼 위조하지 않기 위함(`base/CLAUDE.md` §3.5).

## 9. 나가는 길

| 액션 | 도착 |
| --- | --- |
| 헤더의 "메인" | `/` |
| 좌측 "내 풀 편집" | `/courses` |
| 로그아웃 | `/login` |
| 결과의 "공유 링크 만들기" (향후) | (DB Phase 3에서 `solve_runs` 저장 후 활성) |

## 10. 열린 항목 / 향후

- **explain=true 활성화**: 현재 서버가 항상 `explanation=null` 반환(MVP). LLM-B(설명 생성) 도입 시 결과 영역에 별도 섹션. 본 페이지의 컴포넌트 분해에는 자리만 비워 두기.
- **결과 저장**: DB Phase 3 (`scheduled_results`·`course_rationales`) 도입 후 "내 시간표 저장"/"히스토리" 버튼. 현재는 인라인 응답만.
- **풀 영속화**: 현재 풀은 전역 컨텍스트 + localStorage. DB Phase 2 (`preference_sets`/`preference_courses`) 후엔 서버 라운드트립으로 교체 — *프론트 페이지 책임은 그대로*고, `src/api/`만 손댄다.
- **must_include 충돌 안내**: 사용자가 must_include로 고정한 강의가 불가능 원인일 때, 결과 영역에서 그 강의를 강조해서 표시. 현재 `SelectionResult.diff_info`/`course_rationale` 로 가능.
