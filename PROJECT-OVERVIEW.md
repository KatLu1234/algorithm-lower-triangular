# PROJECT-OVERVIEW.md — algorithm-lower-triangular 전체 개요

> **살아있는 개요 문서** — `claude/` 문서 구조 + `app/` 코드 진행도를 한 장에.
> 특정 시점의 동결 스냅샷은 `project-status-YYYY-MM-DD.md`, 살아있는 시각 구조도는 `claude/base/structure-overview.md`.
> 권위 있는 출처는 항상 `claude/base/` 안의 해당 문서.
> 마지막 갱신: 2026-05-19

---

## 1. 프로젝트 한 줄

고려대 학생이 강의 후보를 입력하면 **이동 시간·학점·중요도를 고려한 최적 시간표**를 받고,
**왜 그 결과가 나왔는지를 알고리즘 단위로** 확인·이해할 수 있게 해주는 학습 겸용 도구 (균형 모델 = 후보 C).

---

## 2. 진행 단계와 현재 위치

| 단계 | 영역 | 상태 |
| ---- | ---- | ---- |
| Phase 1 | 문제 정의 (product.md) | ✓ 완료 |
| Phase 2 | 알고리즘 구조 (drafts/algorithm-tree.md §9) | ✓ 확정 |
| Phase 3 | 웹 구조 (architecture.md) | ◐ §1-3 ✓ / §4.1 흡수 대기 |
| Phase 4 | 코딩 (app/) | ◐ 알고리즘 코어 완성 / API·DB·LLM 미연결 |

**현재 위치**: 알고리즘 코어(스키마 + 트리 A·B·C + 11개 모듈)는 ~90% 완성. **API·DB·LLM·프론트는 미착수.**

---

## 3. claude/ 문서 구조 맵

```
claude/
├── CLAUDE.md                 최상위 작업 지침 / 인덱스
│
├── base/                     ★ 의사결정 문서 (권위 있는 출처)
│   ├── CLAUDE.md             base 레벨 작업 절차·progress 규칙
│   ├── product.md            ✓ 제품 우선순위 10개·LLM 불변항·범위 (균형 모델)
│   ├── user-experience.md    ⏳ 빈 템플릿 (다음 단계)
│   ├── architecture.md       ◐ 계층 조합 + 기술 스택 (§4.1 트리 흡수 대기)
│   ├── algorithms.md         ✓ 참조 — 4+ 알고리즘 요건
│   ├── tasks.md              전체 작업 칸반 인덱스
│   ├── progress.md           base 문서 변경 이력 (매 변경 기록)
│   ├── structure-overview.md ✓ 현재 계획 한 장 시각 구조도 (SVG)
│   └── drafts/
│       └── algorithm-tree.md ✓ 확정 §9 — A·B·C 트리 + 분반·교수·요건 차원
│
├── server/                   서버(FastAPI) 영역 — Gemini-친화 형식
│   ├── team-guide.md         진입 문서
│   ├── tasks.md              영역 칸반
│   └── progress.md           스택·지침 이력
│
├── frontend/                 프론트엔드 영역 — Gemini-친화 형식 (스택 미정)
│   ├── team-guide.md
│   ├── tasks.md
│   └── progress.md
│
└── llm-include/              LLM 자료 영역 — Gemini-친화 형식
    ├── team-guide.md
    ├── tasks.md              [I-01] Upstage Solar API 조사 카드 (TODO)
    └── progress.md
```

**문서 읽는 순서**: `CLAUDE.md` → `base/product.md` (§4 우선순위) → `base/architecture.md` → 영역별 `team-guide.md`.
**시각 요약**: `base/structure-overview.md`.

---

## 4. app/ 코드 진행도

```
app/
├── main.py                   ✓ FastAPI 인스턴스·CORS·라우터
├── api/
│   ├── api.py · deps.py       ✓ 골격
│   └── endpoints/
│       ├── items.py · utils.py  ◐ 샘플
│       └── (timetable.py)        ❌ recommend() 호출 라우트 미작성
├── core/config.py            ✓ 골격 (건물 거리 상수·교시표 추가 예정)
├── crud/
│   ├── item.py                ◐ 샘플
│   └── (course.py · building.py) ❌ DB↔Pydantic 변환 미작성
├── db/supabase.py            ✓ Supabase 클라이언트 (테이블 미생성)
├── models/                   (빈)
│
├── schemas/                  ✓ 알고리즘 계약 6개 (100%)
│   ├── common.py             ✓ Weekday·Category·Requirement·TimeSlot·BlackoutWindow·Course·Infeasibility*
│   ├── preferences.py        ✓ PreferenceVector (강의·그룹·교수·요건 차원 + 검증)
│   ├── feasibility.py        ✓ FeasibilityResult (A→B 계약)
│   ├── valuation.py          ✓ ScoreBreakdown·ScoredSchedule·ValuationResult (B→C 계약)
│   ├── selection.py          ✓ Rationale·DiffInfo·SelectionResult·StageCode (C→응답 계약)
│   └── __init__.py           ✓ 24개 타입 노출
│
└── libs/                     ✓ 알고리즘 트리 (~90%)
    ├── timetable.py          ✓ 루트 recommend() — A→B→C + infeasibility 조기 종료
    ├── feasibility.py        ✓ A 노드 (A-1 풀 정제 · A-2 충돌·그룹 양립 · A-3 가지치기)
    ├── valuation.py          ✓ B 노드 (B-1 v(c) · B-2 이동 룩업 · B-3 백트래킹+배낭)
    ├── selection.py          ✓ C 노드 (C-1 정렬·다양성 · C-2 LCS · C-3 사유 색인)
    ├── activity_selection.py ✓ 탐욕 (A-3)
    ├── binary_search.py      ✓ 이진 탐색 (B-1, 시연용)
    ├── floyd_warshall.py     ✓ 플로이드-워셜 (B-2)
    ├── knapsack.py           ✓ 0-1 배낭 (B-3 상한)
    ├── lcs.py                ✓ LCS (C-2)
    ├── merge_sort.py         ✓ 안정 합병 정렬 (C-1)
    └── matrix_path_dp.py     ⚠️ 작성됐으나 미사용 (B-3 명세-구현 불일치)

tests/                        ◐ 스키마 테스트만
├── conftest.py · test_schemas.py  ✓ 11개 테스트
└── (test_timetable.py)            ❌ 알고리즘 통합 테스트 미작성
```

---

## 5. 영역별 진행률

| 영역 | 진행률 | 비고 |
| ---- | ------ | ---- |
| 스키마 (계약 4 + 도메인 타입) | 100% | 그룹·교수·요건 차원 모두 반영 |
| 알고리즘 모듈 (algorithms.md) | ~90% | 6개 사용 / matrix_path_dp 미사용 |
| 트리 A·B·C 통합 | ~95% | 진입점 recommend()까지 완성 |
| 스키마 테스트 | ~80% | 11개 |
| 알고리즘 통합 테스트 | 0% | ★ 최우선 — 런타임 미검증 |
| API 엔드포인트 | 0% | recommend() 라우트 미연결 |
| DB 연결 (crud + Supabase 테이블) | 0% | buildings·courses 등 미생성 |
| LLM 통합 (LLM-A/B) | 0% | 공급자 TBD (Upstage 조사 I-01) |
| 입력 어댑터 (교시 변환 등) | 0% | 미착수 |
| 프론트엔드 | 0% | 스택 미정 |

**MVP 기준(알고리즘+API+테스트)**: ~65% · **전체 시스템 기준**: ~40%

---

## 6. 미결정 항목 (TBD)

1. 프론트엔드 스택 (React/Vue/Svelte/HTML) — architecture.md §2.1
2. LLM 공급자·모델 — Upstage Solar API 조사 후 (I-01)
3. 자유 텍스트 LLM-A 도입 여부 — product.md §5.2 보류
4. 인증·`auth.users`·`profiles` 도입 시점
5. 강의 데이터 적재 방법 (직접/CSV/포털)
6. 건물 거리: DB(`building_distances`) vs config 상수
7. matrix_path_dp 명세 정합 — (가) 명세를 백트래킹+배낭으로 갱신 vs (나) DP 통합
8. 교시 표현(월5,6) 입력 어댑터 도입
9. ScoreBreakdown에 교수·요건 항 분리 여부 (설명력 vs 단순성)

---

## 7. 다음 단계 (우선순위)

1. **★ 알고리즘 통합 테스트** — `tests/test_timetable.py`, 김민지 시나리오로 `recommend()` end-to-end. 사용자 머신에서 실행 (런타임 검증 미완).
2. **API 엔드포인트** — `app/api/endpoints/timetable.py` + 라우트 등록.
3. **명세 정합** — matrix_path_dp 이슈 결정 + algorithm-tree.md §9.3 동기화.
4. **DB 1단계** — `buildings`·`building_distances` (또는 config 상수) → `crud/building.py`.
5. **DB 2단계** — `courses`·`course_times` → `crud/course.py`.
6. **user-experience.md 작성** — Phase 3 진입 (사용자 명시 작업 순서).

---

## 8. 핵심 결정 요약 (인용 가능)

- **균형 모델 (후보 C)** — 정확성 > 설명가능성 > 중요도 충실도 > … (product.md §4)
- **LLM 불변항** — 결정은 알고리즘, LLM은 번역가(입구)·변호인(출구). 결정자 아님.
- **점수 식** — 단일 레벨 선형 합산. `v(c) = 중요도×학점 + 시간/건물/카테고리/요건/교수 가중치`, 시간표 단위 후처리(이동·압축·다양성).
- **알고리즘 트리** — A 가능성 → B 가치 → C 선택. 12 알고리즘, algorithms.md 5 카테고리 횡단.
- **분반·교수 차원** — 같은 `course_group_id` 분반은 상호 배타 (그룹당 1개), 교수 가중치로 분반 선호.
- **시간 복잡도** — T = O(V³ + N² + N·C + Ñ²·L²) ≈ 1 ms (알고리즘). 응답 지배항은 LLM.

---

## 9. 본 문서의 성격

- 본 파일은 **살아있는 개요** — claude/ 구조나 코드 진행이 바뀌면 갱신.
- base 문서가 **아님** — 갱신 시 `claude/base/progress.md`를 손대지 않음.
- 동결 스냅샷이 필요하면 `project-status-YYYY-MM-DD.md`로 별도 생성.
