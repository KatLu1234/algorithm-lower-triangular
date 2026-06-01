---
doc_type: team-guide
scope: frontend
title: 프론트엔드 영역 진입 문서
purpose: 프론트엔드 영역 팀원이 작업 전 가장 먼저 읽는 큰 틀 문서
target_reader: 프론트엔드 팀원 (UI·API 클라이언트·UX 구현 담당)
stack_status: 미확정 (결정 시 ./progress.md §1에 기록)
authoritative_for:
  - 프론트엔드 영역의 책임 범위와 비-책임
  - 작업 유형별 한 줄 규칙
  - Claude 사용 프롬프트 패턴 (프론트엔드 특화)
  - 자주 발생 케이스 빠른 참조표
not_authoritative_for:
  - 현재 기술 스택 스냅샷 → ./progress.md §1
  - 영역 내 작업 카드 → ./tasks.md
  - UX 결정 기준 → ../base/user-experience.md
  - 영역 경계 → ../base/architecture.md
priority_reading_order:
  - ../CLAUDE.md
  - ../base/product.md (§4 우선순위)
  - ../base/user-experience.md (페르소나·여정·UX 비-목표)
  - ../base/architecture.md (§2 + §5.1)
  - ./progress.md (§1 스냅샷)
  - ./tasks.md
  - 본 문서 §4 이하
related_docs:
  - { path: ../base/CLAUDE.md, why: 작업 절차·금지 사항 }
  - { path: ../base/user-experience.md, why: 프론트 결정의 가장 가까운 기준선 }
  - { path: ../base/product.md, why: 트레이드오프 우선순위 }
  - { path: ../base/architecture.md, why: 프론트 책임과 frontend ↔ server 계약 }
  - { path: ./progress.md, why: 프론트엔드 스택 현황·이력 }
  - { path: ./tasks.md, why: 프론트엔드 영역 작업 카드 }
  - { path: ../base/tasks.md, why: 전체 작업 인덱스·교차 영역 카드 }
last_updated: 2026-05-17
---

# frontend/team-guide.md — 프론트엔드 팀원을 위한 진입 문서

## 1. 이 영역이 책임지는 것

**PURPOSE**: 프론트엔드 영역의 단일 책임 정의.
**OUTPUT**: "이 작업이 프론트엔드 일인가?"의 빠른 판단 기준.

`claude/frontend/`는 사용자가 직접 마주하는 화면 전부를 책임집니다.

**책임**
1. 사용자 입력(과목 선호도, 동선 가중치, 시간 제약 등)을 받아 서버 `/api/v1`으로 JSON POST.
2. 서버 응답을 사람이 읽기 좋은 형태(시간표 격자·동선·설명 텍스트)로 렌더링.
3. 에러·로딩·빈 상태를 `../base/user-experience.md` §4 인터랙션 원칙에 맞게 처리.

**비-책임 (여기서 하지 않음)**
- LLM 호출·키 보관 ❌ (서버 단독)
- 프롬프트 작성·`llm-include` 읽기 ❌
- DB(Supabase) 직접 호출 ❌

계층 경계: `../base/architecture.md` §3.1.

---

## 2. 시작 전 읽기 (3분 코스)

**PURPOSE**: 새 작업 시작 전 머리에 박아야 할 컨텍스트.

1. `../CLAUDE.md` — 프로젝트 전반 관습.
2. `../base/product.md` — §4 우선순위(예: 정확성 > 응답속도, 단순함 > 기능 수).
3. `../base/user-experience.md` — 페르소나·핵심 여정·UX 비-목표. **화면 결정의 기준선**.
4. `../base/architecture.md` — §2 기술 스택 + §5.1 frontend ↔ server 계약.
5. `./progress.md` §1 — 현재 프론트엔드 스택의 권위 있는 스냅샷.
6. `./tasks.md` — 자기에게 주어진 카드 확인.
7. 본 문서 §4 이하.

---

## 3. 다루는 기술 스택

**PURPOSE**: 본 영역에서 사용되는/사용될 기술의 결정 체크리스트.
**STATUS**: **아직 확정되지 않음.** 본 절은 결정 시 체크리스트로 사용. 확정된 값은 `./progress.md` §1에 기록.

| 분류 | 후보 | 선택 시 체크할 점 |
| ---- | ---- | ----------------- |
| 언어 | TypeScript / JavaScript | 시간표·동선 데이터 구조가 복잡 → 타입 추천 |
| 프레임워크 | React / Vue / Svelte / 정적 HTML | 학습 비용 vs 상태 관리 복잡도 |
| 빌드·번들러 | Vite / Next.js / Astro | SSR 불필요하면 Vite로 충분 |
| 스타일링 | Tailwind / CSS Modules | UI 컴포넌트 라이브러리 도입 여부와 함께 결정 |
| API 클라이언트 | fetch / axios / TanStack Query | 캐시·재시도·로딩 상태 필요하면 Query 계열 |
| 차트·시각화 | (TBD) | 시간표 격자·캠퍼스 지도 표현 방식 |
| 배포 | (TBD) | 정적 호스팅이면 단순 |

**스택 변경 절차**: `../base/architecture.md` §2.4 → `./progress.md` §1/§3 갱신.

---

## 4. 책임 매핑 (작업 유형별 한 줄 규칙)

**PURPOSE**: 작업 유형에 대한 책임 규칙 룩업. 스택 확정 전이라도 책임 분류는 동일.

| 작업 유형 | 한 줄 규칙 |
| --------- | ---------- |
| 입력 폼 (과목 선택, 가중치 슬라이더 등) | 입력 검증은 UI 레벨에서 1차로 — 최종 검증은 서버가. |
| API 호출 | `/api/v1/...`로 JSON POST/GET. 에러 응답 `{detail, code}` 표준 가정. |
| 결과 렌더링 | 시간표 격자·동선·설명 텍스트. 표현 결정 근거는 `user-experience.md` §3. |
| 로딩·에러 UI | `user-experience.md` §4 인터랙션 원칙. 본인 취향으로 톤 바꾸지 말 것. |
| 빈 상태 (Empty state) | 처음 진입 / 결과 없음 / 데이터 없음 — 세 케이스 모두 디자인. |
| 접근성 (키보드·색 대비) | `user-experience.md` §5 기대치 만족. |
| 환경변수 | 서버 URL 같은 비-비밀 값만. **LLM 키나 시크릿은 절대 두지 않는다.** |

**전형적 새 화면 사이클**: `UX 결정(user-experience.md 인용) → 컴포넌트 스케치 → API 계약 확인(architecture.md §5.1) → 구현 → 에러·로딩·빈 상태 처리 → 접근성 점검`.

---

## 5. Claude 사용 패턴

**PURPOSE**: 프론트엔드 영역에서 효과가 좋은 프롬프트 템플릿.

### 5.1 새 화면 만들기

```
컨텍스트: claude/frontend/team-guide.md, claude/base/user-experience.md §3·§4
작업: <기능>을 위한 화면을 만들어줘.
입력 폼: <필드들>
결과 표시: <형태>
에러·로딩 처리: user-experience.md §4 원칙대로.
스택: <progress.md §1에서 확정된 것 명시>
주의: LLM 호출 금지(서버 경유), .env에 시크릿 금지.
```

### 5.2 컴포넌트 단위 작업

```
컨텍스트: <컴포넌트 파일 경로>
요청: <Prop 시그니처>를 받아 <표현>을 그리는 컴포넌트를 작성해줘.
상태: <로컬 상태 / 상위에서 주입>
접근성: 키보드 포커스 처리·aria-* 포함.
```

### 5.3 API 클라이언트 작성

```
컨텍스트: claude/base/architecture.md §5.1 (frontend ↔ server 계약)
요청: <엔드포인트>를 호출하는 함수를 작성해줘.
타입: 응답은 <스키마>. 에러 응답은 {detail, code} 표준.
로딩·에러 상태는 호출 측이 처리할 수 있게 반환.
```

### 5.4 디버깅·리뷰

```
컨텍스트: <파일 경로>, 콘솔 오류 또는 스크린샷
요청: 의심 원인 가설 3개와 각각의 검증법을 제시해줘. 수정은 내 승인 후에.
```

### 5.5 Claude에게 시키지 말 것

- LLM API를 프론트에서 직접 호출 ❌ (위반 시 즉시 중단)
- API 키·Supabase 시크릿을 프론트 코드/`.env`에 두기 ❌
- `user-experience.md`에 없는 톤·문구 스타일을 본인 취향으로 도입 ❌
- 서버 응답 스키마를 본인 판단으로 변경 요청 ❌ (서버 팀과 `../base/CLAUDE.md` §3.2 안전 순서 협의 필요)

---

## 6. 지켜야 할 지침 (요약)

**PURPOSE**: 자주 부딪히는 규칙의 빠른 참조.

- **의존 방향**: `frontend → server`. LLM·DB는 서버 경유. (`../base/architecture.md` §3.1)
- **에러 응답**: `{detail, code}` 표준만 가정. `detail`은 사용자에게 그대로 노출 ❌ — 친화적으로 변환.
- **인터랙션 원칙**: 응답성·되돌리기·로딩·에러·빈 상태 다섯 종 모두 `user-experience.md` §4 톤대로.
- **접근성**: 키보드·색 대비·언어 — `user-experience.md` §5 표 기준.
- **트레이드오프**: `../base/product.md` §4 우선순위로 결정. 결정 근거는 PR/응답에 인용.
- **progress 갱신**: 프론트는 **기술 스택 변경 또는 별도 지침 추가 시에만** `./progress.md` 갱신. 컴포넌트 추가·스타일 손질은 기록 안 함. (`../base/CLAUDE.md` §5.2)

---

## 7. 빠른 참조표 (상황 → 문서)

**PURPOSE**: 자주 발생하는 상황에 대한 진입점 룩업.

| 상황 | 어디 보러 가나 |
| ---- | -------------- |
| 새 화면 추가 | [`pages/index.md`](./pages/index.md) §7 절차 + 본 문서 §4 매핑 + `user-experience.md` §2 여정 |
| 페이지·라우팅 구조 확인 | [`pages/index.md`](./pages/index.md) §1·§2 (URL → 페이지 → 인증 가드 매핑) |
| 페이지별 상세 (입력/API/상태) | `pages/<slug>.md` — login·main·timetable·course-search 한 페이지당 한 파일 |
| 스택 도입·교체 | `../base/architecture.md` §2.4 절차 |
| 에러 문구 작성 | `../base/user-experience.md` §4 |
| 빈 상태 디자인 | `../base/user-experience.md` §4 (Empty state) |
| 서버 응답 형태가 헷갈림 | `../base/architecture.md` §5.1 |
| 페르소나·사용 맥락 확인 | `../base/user-experience.md` §1 |
| 무엇이 base 변경인가 헷갈림 | `../base/CLAUDE.md` §1 분류 기준 |
| 내 작업이 뭔지 모르겠음 | `./tasks.md` DOING 컬럼에서 owner 확인. 전체 보드는 `../base/tasks.md` |

---

## 8. 다음에 읽을 문서

**PURPOSE**: 본 진입 문서를 다 읽은 뒤의 후속 자료 인덱스.

- `../base/CLAUDE.md` — 작업 절차·금지 사항.
- `../base/user-experience.md` — 프론트 결정의 가장 가까운 기준선.
- `../base/product.md` — 트레이드오프 우선순위.
- `../base/architecture.md` — §3.1, §5.1 — 프론트 책임과 frontend ↔ server 계약.
- `./progress.md` — 프론트엔드 스택 현황·이력.
- `./tasks.md` — 프론트엔드 영역 작업 카드.
- `../base/tasks.md` — 전체 작업 인덱스·교차 영역 카드·진행 요약.

**막혔을 때**: 스택 확정 같은 큰 결정은 사용자(또는 팀 리드)에게 먼저 확인. 일상 결정은 base 문서 우선순위(`product.md > user-experience.md > architecture.md`)에 따라 판단한 뒤 작업 응답에 근거를 인용.
