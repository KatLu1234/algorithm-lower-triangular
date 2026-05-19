# 프로젝트 현재 상태 — 2026-05-19

> **algorithm-lower-triangular** · 국민대 알고리즘 수업 과제
> 본 문서는 **날짜 박힌 스냅샷**입니다. 권위 있는 출처는 항상 `claude/base/` 안의 해당 문서.
> 살아 있는 구조도는 [`claude/base/structure-overview.md`](claude/base/structure-overview.md) 참고.

---

## 한 줄 요약

**4단계 진행 흐름(문제 정의 → 알고리즘 구조 → 웹 구조 → 코딩) 중 `2단계 ↔ 3단계 사이`에 위치.**
알고리즘 구조는 **확정(locked)** 됐고, 웹 구조 흡수와 UX 정의가 다음 단계.

---

## 1. 비전 — 균형 모델 (후보 C)

> 국민대 학생이 강의 후보를 입력하면 이동 시간·학점·중요도를 고려한 최적 시간표를 받고,
> **어떻게 그 결과가 나왔는지를 알고리즘 단위로 확인·이해할 수 있도록** 해주는 학습 겸용 도구.

출처: [`claude/base/product.md`](claude/base/product.md) §1. **✓ 결정 완료**.

---

## 2. 진행 단계와 현재 위치

| 단계 | 영역 | 상태 | 산출물 |
| ---- | ---- | ---- | ------ |
| **Phase 1** | 문제 정의 | ✓ 완료 | product.md §1~§5 |
| **Phase 2** | 알고리즘 구조 (MVP) | ✓ 완료 | drafts/algorithm-tree.md §9 (확정) |
| **Phase 3** | 웹 구조 | ◐ 진행 전 | architecture.md §1-3 ✓ / §4.1 흡수 ⏳ |
| **Phase 4** | 코딩 (app/) | ⏳ 대기 | app/ 골격만 ✓, 나머지 ⏳ |

**⭐ 현재 위치**: `Phase 2 ↔ Phase 3 사이`. 알고리즘 구조 확정 직후, UX 정의 진입 직전.

---

## 3. 확정된 결정 (인용 가능)

### 3.1 제품 우선순위 (10개)

권위 있는 출처: [`claude/base/product.md`](claude/base/product.md) §4.

```
1. (최우선) 정확성              제약 위반 0건
2.          설명 가능성        알고리즘 단위 추적 가능
3.          유저 중요도 반영    사용자 매긴 점수 그대로
4.          모순·불가능 입력 안내
5.          검증 가능성
6.          응답 속도            ≤ 3초
7.          결과 다양성
8.          이동 부담 최소화
9.          사용자 제어권       (본 과제 후순위)
10. (가장 낮음) 결과 안정성     (본 과제 후순위)
```

### 3.2 LLM 시스템 불변항

> **시간표 결정은 항상 알고리즘이 한다.**
> LLM은 (a) 입력 자유 텍스트의 수치화(선택) 또는 (b) 결과 설명(필수)에만 관여.
> LLM이 산출한 어떤 값도 알고리즘 검증 없이는 결과에 반영되지 않는다.

출처: `product.md` §4.4. **트리 외부 두 자리(입구·출구)에만 LLM 등장.**

### 3.3 알고리즘 트리 (A·B·C)

권위 있는 출처: [`claude/base/drafts/algorithm-tree.md`](claude/base/drafts/algorithm-tree.md) §9 (**✓ 확정 locked**).

```
[루트] 최적 시간표 추천
 ├── [A] 가능성 분석   (어떤 조합이 통과하는가)
 │    ├── A-1 강의 풀 정제 (per-course)     → 해시 탐색
 │    ├── A-2 충돌 관계 산출 (per-pair)     → 정렬, 이진 탐색
 │    └── A-3 후보 공간 가지치기 (per-subset) → 활동 선택
 ├── [B] 가치 평가     (얼마나 좋은가)
 │    ├── B-1 강의 단위 v(c)              → 해시·이진 탐색
 │    ├── B-2 전이 비용 전계산             → 플로이드-워셜
 │    └── B-3 누적 점수 DP + top-K        → 행렬경로 DP + 0-1 배낭
 └── [C] 선택과 비교  (어떻게 보여줄 것인가)
      ├── C-1 상위 N개 정렬·동률            → 합병 정렬
      ├── C-2 후보 쌍 비교                 → LCS
      └── C-3 강의별 사유 색인              → 해시 탐색
```

**필수 9개 + 옵션 3개 = 12 알고리즘 · algorithms.md 5 카테고리 모두 횡단.**

### 3.4 점수 식

단일 레벨 선형 합산 (계층적 가중치 없음):

```
score(S) = Σ_c [중요도(c) × 학점(c) + 시간/건물/카테고리 페널티]
        − λ₁·총_이동시간(S)
        − λ₂·압축_페널티(S)
        − λ₃·건물_다양성(S)
        − ∞  (hard 제약 위반)
```

### 3.5 시간 복잡도

```
T = O(V³ + N² + N·C + Ñ²·L²)
```

현실 입력 (N=30, V=20, C=21, Ñ=5, L=6): **약 11,000 연산 ≈ 1 ms**.
응답 시간 지배항은 알고리즘이 아니라 LLM-B 호출 (~1초).

---

## 4. 작업 상태 — 파일별 인벤토리

### 4.1 base/ — 의사결정 문서 (claude/base/)

| 파일 | 상태 | 비고 |
| ---- | ---- | ---- |
| `CLAUDE.md` | ✓ | base 레벨 Claude 작업 지침 |
| `architecture.md` | ◐ | §1-3 ✓ / §4.1 알고리즘 트리 흡수 ⏳ |
| `product.md` | ✓ | §1~§5 모두 채움 (균형 모델 후보 C) |
| `user-experience.md` | ⏳ | **★ 다음 단계** — 빈 템플릿 |
| `algorithms.md` | ✓ | 참조용 (4+ 알고리즘 요건) |
| `tasks.md` | ⏳ | 전체 칸반 (빈 보드) |
| `progress.md` | ✓ | 변경 이력 운영 중 |
| `structure-overview.md` | ✓ | SVG 구조도 + 위치 매핑 |
| `drafts/algorithm-tree.md` | ✓ 확정 | §9 시간표 도메인 트리 locked. §1~§8 폐기 대기 |

### 4.2 영역 문서 — claude/{server, frontend, llm-include}/

| 파일 | 상태 |
| ---- | ---- |
| `server/team-guide.md` | ✓ Gemini-친화 형식 |
| `server/tasks.md` | ✓ Gemini-친화 형식 (빈 보드) |
| `server/progress.md` | ✓ Gemini-친화 형식 |
| `frontend/team-guide.md` | ✓ Gemini-친화 형식 (스택 미정) |
| `frontend/tasks.md` | ✓ Gemini-친화 형식 (빈 보드) |
| `frontend/progress.md` | ✓ Gemini-친화 형식 (스택 미정) |
| `llm-include/team-guide.md` | ✓ Gemini-친화 형식 |
| `llm-include/tasks.md` | ✓ Gemini-친화 형식 — `[I-01]` Upstage Solar API 조사 카드 |
| `llm-include/progress.md` | ✓ Gemini-친화 형식 |

### 4.3 구현 — app/

| 위치 | 상태 | 비고 |
| ---- | ---- | ---- |
| `app/main.py` | ✓ | FastAPI 골격 |
| `app/api/` | ✓ | 라우터 골격 |
| `app/crud/` | ✓ | CRUD 골격 |
| `app/schemas/` | ✓ 골격 | ⏳ `PreferenceVector`·`FeasibilityResult`·`ValuationResult`·`SelectionResult` 미정의 |
| `app/db/supabase.py` | ✓ | Supabase 클라이언트 |
| `app/libs/` | ⏳ | A·B·C 노드 + 12 알고리즘 미구현 |
| `app/api/v1/solve-schedule` | ⏳ | 엔드포인트 미작성 |
| `app/libs/llm_context.py` | ⏳ | 프롬프트 조립기 미작성 |
| `app/libs/llm_client.py` | ⏳ | LLM SDK 단일 진입점 미작성 |
| `app/core/config.py` | ✓ 골격 | 설정·시크릿 로딩 |
| `tests/` | ⏳ | 폴더 없음 |

### 4.4 산출물 — 워크스페이스 루트

| 파일 | 용도 |
| ---- | ---- |
| `project-status-2026-05-19.pptx` | 발표용 PPT (15 슬라이드) |
| `project-status-2026-05-19.md` | (현재 문서) 텍스트 스냅샷 |

---

## 5. 미결정 항목 (TBD)

UX 및 architecture 단계 진입 시 자연스럽게 결정될 항목들.

| # | 항목 | 결정 시점 | 영향 |
| - | ---- | --------- | ---- |
| 1 | 프론트엔드 스택 (React/Vue/Svelte/HTML) | architecture.md §2.1 작성 시 | frontend/progress.md |
| 2 | LLM 공급자·모델 | architecture.md §2.1 작성 시 | server·llm-include 동시 결정 |
| 3 | 자유 텍스트 LLM-A 도입 여부 | UX 단계에서 결정 | product.md §5.2 보류 — 단순화 우선 |
| 4 | 인증·`users` 테이블 도입 여부 | UX 단계에서 결정 | DB 스키마 |
| 5 | 강의 데이터 입력 방식 | UX 단계에서 결정 | 직접 입력 / CSV / 크롤링 |
| 6 | 저장 시간표 공유 (URL 공유) | UX 단계에서 결정 | DB 스키마 |
| 7 | 다양성 5% 양보 한도 외 휴리스틱 파라미터 | 구현 시점 | C-1 후처리 |
| 8 | 옵션 알고리즘 채택 (다익스트라·위상정렬·편집거리) | `app/libs/` 구현 시점 | 알고리즘 시연 다양성 |
| 9 | Top-K K값과 K-best 완전성 | `app/libs/` 구현 시점 | B-3 백트래킹 방식 |

---

## 6. 다음 즉시 작업 (우선순위)

사용자가 명시한 작업 순서(`목적성 → 유저 경험 → 아키텍처`)를 따라:

1. **★ user-experience.md 작성** — 페르소나·핵심 여정·핵심 약속·인터랙션 원칙. (2단계 진입)
2. **architecture.md §4.1 추가** — 알고리즘 분해 트리를 정식 base 문서로 흡수. (3단계 진입)
3. **`app/schemas/` 4개 Pydantic 정의** — `PreferenceVector`·`FeasibilityResult`·`ValuationResult`·`SelectionResult`. (4단계 진입)
4. **`app/libs/` 알고리즘 노드 구현** — A·B·C 9개 노드 + 12 알고리즘. 순수 함수.
5. **`app/api/v1/solve-schedule` 엔드포인트 + 통합 테스트**.

각 단계 사이에 *결정 보류 항목*(§5)이 자연스럽게 풀립니다.

---

## 7. 변경 이력 요약 (2026-05-17 ~ 2026-05-19)

권위 있는 출처: [`claude/base/progress.md`](claude/base/progress.md) §2.

**2026-05-17 (초기 셋업 + 의사결정)**
- `claude/base/` 폴더 신설 (CLAUDE.md, architecture.md, product.md, user-experience.md, tasks.md, progress.md).
- `drafts/algorithm-tree.md` 신설 → §9 시간표 도메인 상세 트리 추가(반영률 60%) → **확정 (locked)** 처리.
- `product.md` 빈 템플릿 → §1~§5 전 항목 입력 (균형 모델 후보 C, 우선순위 10, LLM 불변항).
- 영역 9개 문서(server·frontend·llm-include × team-guide·tasks·progress) **Gemini-친화 형식** 일괄 변환.

**2026-05-19 (스냅샷 + 시각화 + Upstage 카드)**
- `structure-overview.md` 신설 — SVG 구조도 + 위치 매핑 + 갱신 규칙.
- `llm-include/tasks.md` §2 TODO에 `[I-01] Upstage Solar API 조사 및 도메인 자료 작성` 카드 추가.
- `base/tasks.md` §4 영역별 진행 요약 표 동기화 (`llm-include` TODO 0 → 1).
- `project-status-2026-05-19.pptx` 생성 (15 슬라이드 발표 자료).
- `project-status-2026-05-19.md` 생성 (현재 문서).

---

## 8. 참고 문서 인덱스

본 스냅샷에서 인용된 권위 있는 출처:

- [`claude/base/product.md`](claude/base/product.md) — 제품 우선순위·LLM 불변항·범위.
- [`claude/base/drafts/algorithm-tree.md`](claude/base/drafts/algorithm-tree.md) §9 — 알고리즘 분해 트리 (확정).
- [`claude/base/structure-overview.md`](claude/base/structure-overview.md) — 현재 계획 시각 구조도.
- [`claude/base/architecture.md`](claude/base/architecture.md) — 계층 조합 + 기술 스택.
- [`claude/base/progress.md`](claude/base/progress.md) — base 문서 변경 이력.
- [`claude/llm-include/tasks.md`](claude/llm-include/tasks.md) — Upstage Solar API 카드 (I-01).
- [`project-status-2026-05-19.pptx`](project-status-2026-05-19.pptx) — 발표용 PPT.

---

## 9. 본 문서의 수명

- 본 파일은 **2026-05-19 시점의 스냅샷**. 이후 변경은 본 문서에 반영하지 않습니다.
- 다음 스냅샷이 필요해지면 `project-status-YYYY-MM-DD.md` 새 파일로 생성.
- 살아 있는 상태는 `claude/base/structure-overview.md`와 `claude/base/progress.md`가 권위 있는 출처.
- 본 파일은 base 문서가 **아닙니다** — 갱신 시 `progress.md`를 손대지 않습니다.
