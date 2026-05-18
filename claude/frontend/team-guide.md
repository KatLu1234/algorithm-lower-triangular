# frontend/team-guide.md — 프론트엔드 팀원을 위한 진입 문서

> **이 문서의 역할**
> 프론트엔드 영역을 맡은 팀원이 작업을 시작하기 전에 **가장 먼저** 읽는 큰 틀 문서입니다.
> "이 영역이 무엇을 책임지는가 → 어떤 기술을 쓰는가 → 무엇을 만들어야 하는가 → Claude를 어떻게 활용하는가 → 어떤 규칙을 지키는가" 순서로 한 바퀴 돕니다.
> 더 깊은 규칙·결정 근거가 필요해지면 §8 "다음에 읽을 문서"로 넘어가세요.

---

## 1. 이 영역이 책임지는 것

`claude/frontend/` 영역은 사용자가 직접 마주하는 화면 전부를 책임집니다.

1. 사용자 입력(과목 선호도, 동선 가중치, 시간 제약 등)을 받아 **서버 `/api/v1`** 으로 JSON POST.
2. 서버 응답을 사람이 읽기 좋은 형태(시간표 격자·동선 지도·설명 텍스트)로 렌더링.
3. 에러·로딩·빈 상태를 [`../base/user-experience.md`](../base/user-experience.md) §4 인터랙션 원칙에 맞게 처리.

이 외 영역은 **여기서 하지 않습니다.**
- LLM 호출·키 보관 ❌ (서버가 단독으로 함)
- 프롬프트 작성·`llm-include` 읽기 ❌
- DB(Supabase) 직접 호출 ❌

계층 경계는 [`../base/architecture.md`](../base/architecture.md) §3.1.

## 2. 시작 전 읽기 (3분 코스)

1. [`../CLAUDE.md`](../CLAUDE.md) — 프로젝트 전반 관습.
2. [`../base/product.md`](../base/product.md) — **우선순위**(예: 정확성 > 응답속도, 단순함 > 기능 수)를 머리에 넣고 가세요.
3. [`../base/user-experience.md`](../base/user-experience.md) — 페르소나·핵심 여정·UX 비-목표. 이게 화면 결정의 기준선입니다.
4. [`../base/architecture.md`](../base/architecture.md) §2 기술 스택 + §5.1 frontend ↔ server 계약.
5. [`./progress.md`](./progress.md) §1 — **현재 프론트엔드 스택의 최신 스냅샷**. 본 문서 §3과 어긋나면 progress.md가 사실.
6. [`./tasks.md`](./tasks.md) — **자기에게 주어진 카드 확인**. 전체 진행 요약은 [`../base/tasks.md`](../base/tasks.md).
7. 본 문서의 §4 "내가 하는 일" 이하.

## 3. 너가 다루는 기술

> 본 프로젝트의 프론트엔드 스택은 **아직 확정되지 않았습니다.** 결정 전까지는 본 절을 가이드/체크리스트로 사용하세요. 확정된 값은 [`./progress.md`](./progress.md) §1에 기록됩니다.

스택을 정할 때 고려할 분류:

| 분류 | 후보 | 선택 시 체크할 점 |
| ---- | ---- | ----------------- |
| 언어 | TypeScript / JavaScript | 시간표/동선 데이터는 구조가 복잡 → 타입 추천 |
| 프레임워크 | React / Vue / Svelte / 정적 HTML | 학습 비용 vs 상태 관리 복잡도 |
| 빌드·번들러 | Vite / Next.js / Astro | SSR 불필요하면 Vite로 충분 |
| 스타일링 | Tailwind / CSS Modules | UI 컴포넌트 라이브러리 도입 여부와 함께 결정 |
| API 클라이언트 | fetch / axios / TanStack Query | 캐시·재시도·로딩 상태가 필요하면 Query 계열 |
| 차트·시각화 | (TBD) | 시간표 격자·캠퍼스 지도 표현 방식 |
| 배포 | (TBD) | 정적 호스팅이면 단순 |

스택을 추가·교체·제거하기 전에 [`../base/architecture.md`](../base/architecture.md) §2.4 절차를 따라 사용자 승인을 받고 [`./progress.md`](./progress.md) §1/§3을 갱신하세요.

## 4. 내가 하는 일 (책임 매핑)

스택 확정 전이라도 책임 분류는 동일합니다.

| 작업 유형 | 한 줄 규칙 |
| --------- | ---------- |
| 입력 폼 (과목 선택, 가중치 슬라이더 등) | 입력 검증은 UI 레벨에서 1차로 — 최종 검증은 서버가. |
| API 호출 | `/api/v1/...`로 JSON POST/GET. 에러 응답 `{detail, code}` 표준을 가정. |
| 결과 렌더링 | 시간표 격자·동선·설명 텍스트. 표현 결정의 근거는 `user-experience.md` §3. |
| 로딩·에러 UI | `user-experience.md` §4 인터랙션 원칙. 본인 취향으로 톤 바꾸지 말 것. |
| 빈 상태 (Empty state) | 처음 진입 / 결과 없음 / 데이터 없음 → 세 케이스 모두 디자인. |
| 접근성 (키보드·색 대비) | `user-experience.md` §5 기대치 만족. |
| 환경변수 | 서버 URL 같은 비-비밀 값만. **LLM 키나 시크릿은 절대 두지 않는다.** |

전형적인 새 화면 한 사이클:
**UX 결정(`user-experience.md` 인용) → 컴포넌트 스케치 → API 계약 확인(`architecture.md` §5.1) → 구현 → 에러·로딩·빈 상태 처리 → 접근성 점검.**

## 5. Claude를 이렇게 쓴다

프론트엔드 영역에서 효과가 좋았던 프롬프트 패턴입니다.

### 5.1 새 화면 만들 때

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

### 5.5 Claude에게 절대 시키지 말 것

- LLM API를 프론트에서 직접 호출 — 위반 시 즉시 중단.
- API 키·Supabase 시크릿을 프론트 코드/`.env`에 두기.
- `user-experience.md`에 없는 톤·문구 스타일을 본인 취향으로 도입.
- 서버 응답 스키마를 본인 판단으로 변경 요청(서버 팀과 [`../base/CLAUDE.md`](../base/CLAUDE.md) §3.2 안전 순서 협의 필요).

## 6. 지켜야 할 지침 (요약)

- **의존 방향**: `frontend → server`. LLM·DB는 서버 경유. ([architecture.md](../base/architecture.md) §3.1)
- **에러 응답**: `{detail, code}` 표준만 가정. `detail`은 사용자에게 그대로 노출 ❌ — 친화적으로 변환.
- **인터랙션 원칙**: 응답성·되돌리기·로딩·에러·빈 상태 다섯 종 모두 [`user-experience.md`](../base/user-experience.md) §4에 정의된 톤대로.
- **접근성**: 키보드 접근·색 대비·언어 처리 — [`user-experience.md`](../base/user-experience.md) §5 표 기준.
- **트레이드오프**: [`product.md`](../base/product.md) §4 우선순위로 결정. 결정 근거는 PR/응답에 인용.
- **progress 갱신**: 프론트는 **기술 스택 변경 또는 별도 지침 추가 시에만** [`./progress.md`](./progress.md) 갱신. 컴포넌트 추가·스타일 손질은 기록 안 함. ([base/CLAUDE.md](../base/CLAUDE.md) §5.2)

## 7. 자주 발생하는 케이스 빠른 표

| 상황 | 어디 보러 가나 |
| ---- | -------------- |
| 새 화면 추가 | 본 문서 §4 매핑 + §5.1 프롬프트 + `user-experience.md` §2 여정 |
| 스택 도입·교체 | [`../base/architecture.md`](../base/architecture.md) §2.4 절차 |
| 에러 문구 작성 | [`../base/user-experience.md`](../base/user-experience.md) §4 |
| 빈 상태 디자인 | [`../base/user-experience.md`](../base/user-experience.md) §4 (Empty state) |
| 서버 응답 형태가 헷갈림 | [`../base/architecture.md`](../base/architecture.md) §5.1 |
| 페르소나·사용 맥락 확인 | [`../base/user-experience.md`](../base/user-experience.md) §1 |
| 무엇이 base 변경인가 헷갈림 | [`../base/CLAUDE.md`](../base/CLAUDE.md) §1 분류 기준 |
| 내 작업이 뭔지 모르겠음 | [`./tasks.md`](./tasks.md) DOING 컬럼에서 owner 확인. 전체 보드는 [`../base/tasks.md`](../base/tasks.md) |

## 8. 다음에 읽을 문서

- [`../base/CLAUDE.md`](../base/CLAUDE.md) — 작업 전/중/후 절차, progress 규칙, 금지 사항.
- [`../base/user-experience.md`](../base/user-experience.md) — 프론트 결정의 가장 가까운 기준선.
- [`../base/product.md`](../base/product.md) — 트레이드오프 우선순위.
- [`../base/architecture.md`](../base/architecture.md) §3.1, §5.1 — 프론트 책임과 frontend ↔ server 계약.
- [`./progress.md`](./progress.md) — 프론트엔드 스택 현황·이력.
- [`./tasks.md`](./tasks.md) — 프론트엔드 영역 작업 카드(칸반). 자기에게 배정된 카드 확인.
- [`../base/tasks.md`](../base/tasks.md) — 전체 작업 인덱스·교차 영역 카드·진행 요약.

스택 확정 같은 큰 결정은 사용자(또는 팀 리드)에게 먼저 확인하고, 일상 결정은 base 문서의 우선순위(`product.md > user-experience.md > architecture.md`)에 따라 판단한 뒤 작업 응답에 근거를 인용하세요.
