# server/team-guide.md — 서버 팀원을 위한 진입 문서

> **이 문서의 역할**
> 서버(FastAPI) 영역을 맡은 팀원이 작업을 시작하기 전에 **가장 먼저** 읽는 큰 틀 문서입니다.
> "이 영역이 무엇을 책임지는가 → 어떤 기술을 쓰는가 → 무엇을 만들어야 하는가 → Claude를 어떻게 활용하는가 → 어떤 규칙을 지키는가" 순서로 한 바퀴 돕니다.
> 더 깊은 규칙·결정 근거가 필요해지면 §8 "다음에 읽을 문서"로 넘어가세요.

---

## 1. 이 영역이 책임지는 것

`claude/server/` 영역은 본 프로젝트의 **단일 백엔드**입니다. 다음 세 가지가 핵심 역할이에요.

1. 프론트엔드에서 오는 HTTP/JSON 요청을 받아 검증하고 응답한다.
2. 알고리즘 본체를 **순수 함수**로 실행한다(매트릭스·시간표 최적화 등).
3. LLM이 필요한 흐름에서 `llm-include/`의 자료로 프롬프트를 조립해 외부 LLM을 호출한다.

이 외 영역(LLM 키 보관, 프롬프트 작성, UI 렌더링)은 **여기서 하지 않습니다.** 경계 규칙은 [`../base/architecture.md`](../base/architecture.md) §3.

## 2. 시작 전 읽기 (3분 코스)

작업 종류와 무관하게 다음 순서를 따라주세요. 두 번째부터는 변경 부분만 다시 읽으면 됩니다.

1. [`../CLAUDE.md`](../CLAUDE.md) — 프로젝트 전반 관습.
2. [`../base/product.md`](../base/product.md) — **우선순위**(예: 정확성 > 응답속도)를 머리에 넣고 가세요. 코드 트레이드오프 결정의 근거가 됩니다.
3. [`../base/architecture.md`](../base/architecture.md) §2 기술 스택 + §5 인터페이스 규약.
4. [`./progress.md`](./progress.md) §1 — **현재 서버 스택의 최신 스냅샷**. 본 문서 §3과 어긋나면 progress.md가 사실.
5. [`./tasks.md`](./tasks.md) — **자기에게 주어진 카드 확인**. 전체 진행 요약은 [`../base/tasks.md`](../base/tasks.md).
6. 본 문서의 §4 "내가 하는 일" 이하.

## 3. 너가 다루는 기술

권위 있는 출처: [`./progress.md`](./progress.md) §1. 본 절은 빠른 참고용이며, 둘이 어긋나면 progress.md가 사실입니다.

- **언어**: Python 3 (`.venv/` 가상환경)
- **웹 프레임워크**: FastAPI (+ Starlette CORS) — `app/main.py`
- **ASGI 서버**: `uvicorn` (실행 명령은 `uvicorn app.main:app --reload`)
- **검증 / 모델**: Pydantic v2 — `app/schemas/`
- **DB**: Supabase 클라이언트 — `app/db/supabase.py`
- **LLM SDK 단일 진입점**: `app/libs/llm_client.py` (도입 예정)
- **프롬프트 조립기**: `app/libs/llm_context.py` ( `claude/llm-include/`를 읽음, 도입 예정)
- **설정 / 시크릿**: `app/core/config.py` + `.env` (Git 제외)
- **테스트**: `pytest` (계획) — `tests/<도메인>/test_*.py`

스택을 추가·교체·제거할 때는 [`../base/architecture.md`](../base/architecture.md) §2.4 절차 → [`./progress.md`](./progress.md) §3 기록 → [`../base/architecture.md`](../base/architecture.md) §2.1 동기화 순으로 진행합니다.

## 4. 내가 하는 일 (책임 매핑)

작업이 어디 폴더로 가야 하는지 헷갈리지 않게 해주는 표입니다.

| 작업 유형 | 가는 곳 | 한 줄 규칙 |
| --------- | ------- | ---------- |
| HTTP 라우트 정의 | `app/api/endpoints/<도메인>.py` | 비즈니스 로직은 여기 안 쓴다 — 위임만 한다. |
| 요청/응답 스키마 | `app/schemas/<도메인>.py` | Pydantic 모델. 필드 추가는 옵셔널 먼저. |
| DB 읽고 쓰기 | `app/crud/<도메인>.py` | 라우트가 직접 Supabase 호출 ❌. CRUD 함수 호출만. |
| 순수 알고리즘 | `app/libs/<모듈명>.py` | FastAPI·DB·LLM 의존 없음. 입력 → 출력만. |
| LLM 호출 흐름 | `app/libs/llm_context.py` + `app/libs/llm_client.py` | 라우트에서 `llm_client.complete(build_<task>(payload))` 패턴. |
| 환경변수·상수 | `app/core/config.py` | 매직 넘버·키 코드 안 박기. |
| 공용 의존성 | `app/api/deps.py` | DB 세션 등 라우트 공통 주입. |
| 단위 테스트 | `tests/<도메인>/test_*.py` | 알고리즘은 빈/1×1/대각/비정방형 같은 작은 케이스부터. |

전형적인 새 기능 한 사이클:
**스키마 정의 → 알고리즘 함수(`libs`) 구현 → 단위 테스트 → CRUD가 필요하면 추가 → 라우트 작성 → 통합 한 번 돌려보기.**

## 5. Claude를 이렇게 쓴다

서버 영역에서 효과가 좋았던 프롬프트 패턴입니다. 그대로 복사해 써도 되고 변형해도 됩니다.

### 5.1 새 엔드포인트 만들 때

```
컨텍스트: claude/server/team-guide.md, claude/base/architecture.md §3.2와 §5
작업: /api/v1/<도메인>/<액션> 엔드포인트를 추가해줘.
입력: <필드 설명>
출력: <필드 설명>
순서: schemas → libs(순수 함수) → tests → crud(필요 시) → endpoints.
주의: app/libs/llm_client.py 단일 진입점 원칙 유지, 라우트는 async def.
```

### 5.2 알고리즘 함수 구현·검증

```
컨텍스트: app/libs/<모듈명>.py
요청: 함수 `solve(matrix)`를 구현하고, pytest 케이스 4개(빈/1×1/대각/일반)를 함께 작성해줘.
제약: 순수 함수, 외부 IO 금지, 타입 힌트 필수, 입력 검증은 ValueError로.
```

### 5.3 스키마 변경

```
컨텍스트: app/schemas/<도메인>.py, claude/base/CLAUDE.md §3.2
요청: <필드>를 추가하고 싶어. 안전 순서대로 진행해줘 — 일단 옵셔널로 추가하고 라우트만 채우게.
프론트엔드 변경은 별도 작업으로 미뤄.
```

### 5.4 디버깅·리뷰

```
컨텍스트: <파일 경로>, 오류 메시지 또는 의심되는 부분 인용
요청: 문제 원인 가설 3개와 각각의 검증 방법을 알려줘. 코드 수정은 내가 승인한 뒤에.
```

### 5.5 Claude에게 절대 시키지 말 것

- 키·시크릿·`.env` 값을 코드/로그에 포함시키기 — 위반 시 즉시 중단 요청.
- 라우트 함수 안에 프롬프트 문자열 하드코딩 — 항상 `llm-include`+조립기 경유.
- 라이브러리 새로 추가하고 `requirements.txt`에 몰래 넣기 — 사용자 승인 먼저.
- 사용자에게 보여주지 않고 큰 파일 통째로 재작성 — 부분 편집 우선.

## 6. 지켜야 할 지침 (요약)

자세한 근거는 base 문서들에 있고, 여기는 자주 부딪히는 규칙만 모았습니다.

- **의존 방향**: `frontend → server → llm-include`. 거꾸로 import 금지. ([architecture.md](../base/architecture.md) §3)
- **단일 진입점**: 외부 LLM SDK는 `app/libs/llm_client.py` **에서만** import.
- **순수 함수**: `app/libs/`의 알고리즘 함수는 부수효과(파일 I/O, DB, print) 금지.
- **시크릿**: `.env`는 `app/core/config.py` 한 곳에서만 읽기.
- **PEP 8 + 타입 힌트 필수** (모든 함수 시그니처).
- **에러 변환**: 도메인 예외(`ValueError` 등) → 라우트에서 `HTTPException`으로 매핑.
- **스키마 안전 순서**: 옵셔널 추가 → 서버 채움 → frontend 사용 → 필요 시 필수화. ([base/CLAUDE.md](../base/CLAUDE.md) §3.2)
- **트레이드오프**: [`product.md`](../base/product.md) §4 우선순위로 결정. 결정 근거는 PR/응답에 인용.
- **progress 갱신**: 서버는 **기술 스택 변경 또는 별도 지침 추가 시에만** [`./progress.md`](./progress.md) 갱신. 일반 코드 변경은 기록 안 함. ([base/CLAUDE.md](../base/CLAUDE.md) §5.2)

## 7. 자주 발생하는 케이스 빠른 표

| 상황 | 어디 보러 가나 |
| ---- | -------------- |
| 새 엔드포인트 추가 | 본 문서 §4 매핑 표 + §5.1 프롬프트 |
| 라이브러리 도입 | [`../base/architecture.md`](../base/architecture.md) §2.4 절차 |
| LLM 호출 추가 | [`../base/CLAUDE.md`](../base/CLAUDE.md) §3.3 5단계 |
| 응답 스키마 필드 추가 | [`../base/CLAUDE.md`](../base/CLAUDE.md) §3.2 안전 순서 |
| UI 문구·에러 메시지 톤 | [`../base/user-experience.md`](../base/user-experience.md) §4 |
| 어디서 결정 근거를 인용할까 | `product.md §4` 또는 `user-experience.md §3.2` 형태로 |
| 무엇이 base 변경인가 헷갈림 | [`../base/CLAUDE.md`](../base/CLAUDE.md) §1 분류 기준 |
| 내 작업이 뭔지 모르겠음 | [`./tasks.md`](./tasks.md) DOING 컬럼에서 owner 확인. 전체 보드는 [`../base/tasks.md`](../base/tasks.md) |

## 8. 다음에 읽을 문서

- [`../base/CLAUDE.md`](../base/CLAUDE.md) — 작업 전/중/후 절차, progress 규칙, 금지 사항.
- [`../base/architecture.md`](../base/architecture.md) — 계층 책임·기술 스택·인터페이스 규약.
- [`../base/product.md`](../base/product.md) — 우선순위와 의사결정 근거.
- [`../base/user-experience.md`](../base/user-experience.md) — 에러 문구·로딩 처리·응답 톤.
- [`./progress.md`](./progress.md) — 서버 영역 스택 현황과 별도 지침 이력.
- [`./tasks.md`](./tasks.md) — 서버 영역 작업 카드(칸반). 자기에게 배정된 카드 확인.
- [`../base/tasks.md`](../base/tasks.md) — 전체 작업 인덱스·교차 영역 카드·진행 요약.

막히면 같은 영역 팀원에게 먼저 물어보고, 그래도 정답이 안 보이면 base 문서의 결정 우선순위(`product.md > user-experience.md > architecture.md`)에 따라 판단한 뒤 작업 응답에 근거를 인용하세요.
