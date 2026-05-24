# Base Architecture — `frontend ↔ server ↔ llm-include`

이 문서는 본 프로젝트의 세 영역(`frontend`, `server`, `llm-include`)을 **어떻게 조합해서 동작하게 할지**를 정의하는 베이스 설계 문서입니다.
세부 구현 규약·코드 스타일은 각 영역 폴더의 문서를 참고하고, 이 문서는 "계층 사이의 경계"에 집중합니다.

---

## 1. 전체 구조 한눈에 보기

```
  ┌─────────────┐   HTTP/JSON    ┌────────────────────────┐   prompt+context   ┌──────────────┐
  │  frontend   │ ─────────────▶ │  server (FastAPI)      │ ─────────────────▶ │  LLM API     │
  │  (브라우저) │ ◀───────────── │  app/main.py, app/api/ │ ◀───────────────── │  (외부)      │
  └─────────────┘    JSON 응답   └──────────┬─────────────┘   completion       └──────────────┘
                                            │ reads
                                            ▼
                                  ┌────────────────────┐
                                  │   llm-include      │
                                  │  프롬프트 템플릿·  │
                                  │  도메인 컨텍스트·  │
                                  │  few-shot 예시     │
                                  └────────────────────┘
```

핵심 원칙은 단방향 의존입니다.

- `frontend`는 **`server`의 HTTP API만** 알고, LLM 호출 사양이나 프롬프트는 모른다.
- `server`는 LLM 호출과 응답 정형화를 **유일하게 담당**한다. 프롬프트를 만들 때 `llm-include`에서 자료를 읽어 합친다.
- `llm-include`는 **데이터 + 템플릿**만 가진다. 코드(import 대상 Python 모듈)는 두지 않는다.

## 2. 기술 스택

각 계층이 어떤 기술로 구현되는지 정의합니다. 이 절은 **현재의 청사진(architectural intent)** 이고,
영역별 **상세 스냅샷과 변경 이력**은 `claude/<영역>/progress.md`가 권위 있는 출처입니다.
두 곳이 어긋나면 `progress.md`의 최신 항목을 사실로 간주하고, 다음 base 갱신에서 본 절을 동기화합니다.

### 2.1 계층별 스택

| 계층 | 분류 | 선택 | 비고 |
| ---- | ---- | ---- | ---- |
| `frontend/` | 언어 | TypeScript | 권위 출처 [`frontend/progress.md`](../frontend/progress.md) §1 (2026-05-21 1차 확정) |
| `frontend/` | 프레임워크 | React 18 | |
| `frontend/` | 빌드 / 번들러 | Vite 5 | SSR 불필요 |
| `frontend/` | 스타일링 | Tailwind CSS 3 | |
| `frontend/` | API 클라이언트 | fetch + 얇은 래퍼 | `src/api/client.ts`, `{detail, code}` 에러 표준 처리 |
| `server/` | 언어 | Python 3 | `.venv/` 가상환경 |
| `server/` | 웹 프레임워크 | FastAPI + Starlette | `app/main.py` |
| `server/` | ASGI 서버 | TBD (보통 `uvicorn`) | 실행 명령 확정 시 progress.md에 기록 |
| `server/` | 검증 / 모델 | Pydantic v2 | `app/schemas/` |
| `server/` | DB | Supabase | `app/db/supabase.py` |
| `server/` | LLM SDK | TBD (공급자 확정 후) | `app/libs/llm_client.py`(단일 진입점) |
| `server/` | 템플릿 엔진 | TBD (Jinja2 또는 `str.format`) | `app/libs/llm_context.py` |
| `server/` | 설정 / 시크릿 | `app/core/config.py` + `.env` | `.env`는 Git 제외 |
| `server/` | 테스트 | (계획) `pytest` | `tests/` 폴더 |
| `llm-include/` | 자료 형식 | TBD (`.md` / `.txt` / `.json`) | 프롬프트와 few-shot 포맷이 다를 수 있음 |
| `llm-include/` | 메타 헤더 | TBD (YAML front-matter 등) | 목적·기대 사용처·마지막 수정일 |
| `llm-include/` | LLM 공급자 / 모델 | TBD | 보통 `server/`의 LLM SDK 결정과 동일 시점 |

확정·변경 이력은 각 영역의 `progress.md`로:
[`server/progress.md`](../server/progress.md) · [`frontend/progress.md`](../frontend/progress.md) · [`llm-include/progress.md`](../llm-include/progress.md).

### 2.2 계층 간 통신 기술

| 경계 | 프로토콜 / 매체 | 비고 |
| ---- | --------------- | ---- |
| `frontend` ↔ `server` | HTTP/JSON over `/api/v1` | WebSocket·gRPC·멀티파트 업로드는 본 과제 범위 밖 (§5.1) |
| `server` → 외부 LLM | HTTPS API | `app/libs/llm_client.py` **한 곳에서만** 호출 (§5.3) |
| `server` ↔ `llm-include` | 파일 시스템 읽기 | 경로 기준 `app/core/config.LLM_INCLUDE_DIR` (§5.2) |

### 2.3 환경 · 운영

| 항목 | 현재 | 비고 |
| ---- | ---- | ---- |
| 가상환경 | `.venv/` | Git 제외 |
| 시크릿 보관 | `.env` | Git 제외, `app/core/config.py`만 접근 |
| 환경 분리 | 단일 환경(개발 = 운영) | 운영 분리 시 본 절에 환경 매트릭스 추가 |
| 배포 | TBD | 프론트·서버 호스팅 결정 시 기록 |
| CI | 미사용 | 도입 시 본 절·`progress.md`에 동시 기록 |

### 2.4 외부 의존 도입 절차

기술 스택에 새 항목을 추가/교체/제거하려면 다음 순서를 따른다.

1. `claude/base/CLAUDE.md` §1에 따라 base 변경으로 분류하고 사용자 승인을 받는다.
2. 영역의 `progress.md` §1(스냅샷)·§3(변경 이력)을 먼저 갱신한다.
3. 본 절의 표를 동기화한다.
4. 코드 변경(`requirements.txt`, 설정 등)을 진행한다.
5. `base/progress.md`에 `architecture.md` 변경 한 줄을 추가한다(§5.1 규칙).

## 3. 각 계층의 책임과 비책임

### 3.1 `frontend/`
- **해야 할 일**
  - 사용자 입력 폼(예: matrix 입력, 파라미터)을 받아 `server`의 `/api/v1/...` 엔드포인트로 JSON POST.
  - 응답을 사람이 읽기 쉬운 형태(표·로그·하이라이트)로 렌더링.
  - 에러 응답(`{"detail": "..."}`)을 사용자에게 그대로 노출하지 않고 친화적으로 변환.
- **하지 말아야 할 일**
  - LLM API 키를 직접 들고 있거나 LLM 엔드포인트를 직접 호출 ❌
  - 프롬프트 문자열을 만들거나 `llm-include` 파일을 읽음 ❌
  - DB(Supabase)를 직접 호출 ❌ — 반드시 `server`를 경유.

### 3.2 `server/` (FastAPI, 코드 본체는 `app/`)
- **해야 할 일**
  - `app/api/endpoints/*.py`에서 라우트 정의, 입력은 `app/schemas/`로 검증.
  - 알고리즘 실행은 `app/libs/`의 순수 함수에 위임.
  - LLM이 필요한 라우트는 다음 순서로 처리한다.
    1. `app/schemas/`에서 입력 검증
    2. `app/libs/llm_context.py`(이하 *조립기*)가 `claude/llm-include/`의 자료를 읽어 프롬프트를 조립
    3. `app/libs/llm_client.py`가 외부 LLM API를 호출
    4. 결과를 `app/schemas/` 응답 모델로 직렬화해 반환
  - 모든 외부 키(`.env`)는 `app/core/config.py`에서만 읽는다.
- **하지 말아야 할 일**
  - 라우트 함수 안에 프롬프트 문자열을 하드코딩 ❌ — 항상 `llm-include`에서 읽어 조립한다.
  - LLM 응답을 그대로 클라이언트에 흘려보내기 ❌ — 응답 스키마를 통과시켜야 한다.

### 3.3 `llm-include/`
- **해야 할 일**
  - **순수 데이터·텍스트 자료**만 보관 (`.md`, `.txt`, `.json`).
    - `prompts/` — 시스템·유저 프롬프트 템플릿
    - `examples/` — few-shot 입출력 예시
    - `domain/` — 문제 정의서, 용어집, lower-triangular 알고리즘 설명 등 LLM이 참고할 도메인 자료
  - 자료마다 상단에 메타 헤더(목적·기대 사용처·마지막 수정일)를 단다.
- **하지 말아야 할 일**
  - `.py` 모듈을 두거나 `app/`에서 import 대상이 되지 않게 한다 ❌ — 파일 시스템 경로로 읽는다.
  - 시크릿·키·개인정보 포함 ❌.

## 4. 데이터 흐름 (LLM이 끼는 요청 예)

1. **frontend** → `POST /api/v1/solve-lt` with `{"matrix": [[...]], "explain": true}`
2. **server**: `endpoints/solve_lt.py`
   1. `SolveLTRequest`(Pydantic)로 입력 검증.
   2. 순수 알고리즘 `libs.lower_triangular.solve(matrix)` 호출 → 수치 결과 획득.
   3. `explain=True`면 `libs.llm_context.build(task="explain_lt", payload=result)` 호출.
      - 조립기는 `claude/llm-include/prompts/explain_lt.md`(시스템) +
        `claude/llm-include/examples/explain_lt/*.json`(few-shot) +
        실제 `payload`를 합쳐 메시지 배열 반환.
   4. `libs.llm_client.complete(messages)` → LLM 응답 문자열.
   5. `SolveLTResponse(result=..., explanation=...)`로 직렬화해 반환.
3. **frontend**: 응답을 받아 결과 + 설명을 화면에 표시.

## 5. 인터페이스 규약(계약)

### 5.1 frontend ↔ server
- 모든 API는 `/api/v1` 접두어 (`app/main.py`에서 등록됨).
- 요청·응답은 **JSON only**. 멀티파트 업로드는 본 과제 범위 밖.
- 에러 응답 표준:
  ```json
  { "detail": "사람이 읽을 수 있는 에러 메시지", "code": "LT_INVALID_SHAPE" }
  ```
- 성공 응답은 도메인별 `*Response` Pydantic 스키마 그대로.

### 5.2 server ↔ llm-include
- 서버는 `claude/llm-include/` 파일을 **읽기 전용**으로 사용한다.
- 파일 경로는 환경변수가 아닌 **프로젝트 루트 기준 상대 경로**로 해석한다. 헬퍼: `app/core/config.LLM_INCLUDE_DIR`.
- 템플릿은 Jinja2 또는 단순 `str.format`으로 채운다(추가 라이브러리 도입 전 사용자 승인 필요).

### 5.3 server ↔ LLM API
- 호출은 `app/libs/llm_client.py` **한 곳에서만** 이뤄진다. 다른 모듈에서 SDK를 import 금지.
- 타임아웃·재시도·토큰 한도는 `app/core/config.py`에 상수로 둔다.
- 응답에 사용자 식별 정보를 로그로 남기지 않는다.

## 6. 디렉터리에 추가될 예상 파일들

```
claude/
├── CLAUDE.md                  # 최상위 지침 / 인덱스
├── base/
│   ├── CLAUDE.md              # base 레벨 Claude 작업 지침
│   ├── architecture.md        # (현재 문서) 계층 조합 설계 + 기술 스택
│   ├── product.md             # 제품 목적·기대 효과·우선순위
│   ├── user-experience.md     # 유저가 기대할 수 있는 경험
│   ├── tasks.md               # 전체 작업 칸반 인덱스 + 영역 진행 요약
│   └── progress.md            # base 문서 변경 이력 (매 변경마다)
├── frontend/
│   ├── team-guide.md          # 프론트엔드 팀원 진입 문서 (영역 큰 틀)
│   ├── tasks.md               # 프론트엔드 영역 작업 보드 (칸반)
│   ├── progress.md            # 기술 스택 변경·별도 지침 이력
│   └── (예) guide.md, components.md
├── server/
│   ├── team-guide.md          # 서버 팀원 진입 문서
│   ├── tasks.md               # 서버 영역 작업 보드 (칸반)
│   ├── progress.md            # 기술 스택 변경·별도 지침 이력
│   └── (예) endpoints.md, schemas.md, llm-flow.md
└── llm-include/
    ├── team-guide.md          # LLM 자료 담당 진입 문서
    ├── tasks.md               # LLM 자료 영역 작업 보드 (칸반)
    ├── progress.md            # 기술 스택 변경·별도 지침 이력
    ├── prompts/
    │   └── explain_lt.md
    ├── examples/
    │   └── explain_lt/case-01.json
    └── domain/
        └── lower-triangular.md

app/libs/
├── lower_triangular.py        # 순수 알고리즘
├── llm_context.py             # 프롬프트 조립기 (llm-include 읽음)
└── llm_client.py              # LLM SDK 단일 진입점
```

## 7. 변경 관리

- 본 문서는 계층 간 경계가 바뀔 때만 수정한다. 세부 구현은 각 영역 폴더의 문서에서 다룬다.
- 새 외부 연동(예: 벡터 DB, 캐시)을 도입하려면 이 문서에 한 절을 추가하고 사용자 승인을 받는다.
- 영역 간 의존이 **위 그림의 화살표 방향과 어긋나는 변경**은 곧 설계 위반이다. 발견 즉시 보고한다.
