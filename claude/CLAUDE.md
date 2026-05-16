# CLAUDE.md — `algorithm-lower-triangular` 프로젝트 작업 지침

이 문서는 본 저장소에서 Claude(또는 사람 협업자)가 코드를 작성·수정할 때 따라야 할 **계획과 규칙**을 정의합니다.
새 작업을 시작하기 전에 반드시 이 문서를 먼저 읽고, 그다음 작업 영역에 맞춰 `claude/server/`, `claude/frontend/`, `claude/llm-include/` 하위 문서를 참고하세요.

---

## 1. 프로젝트 개요

- **이름**: `algorithm-lower-triangular`
- **목적**: 국민대학교 알고리즘 수업 과제 — Lower Triangular 관련 알고리즘을 학습·구현하고, 이를 FastAPI 백엔드 서비스 형태로 노출한다.
- **기술 스택**
  - 언어: Python 3 (`.venv/` 가상환경 사용)
  - 웹 프레임워크: FastAPI + Starlette + Pydantic v2
  - DB: Supabase (`app/db/supabase.py`)
  - 의존성: `requirements.txt`
- **엔트리포인트**: `app/main.py` → `uvicorn app.main:app`

## 2. 폴더 구조

```
algorithm-lower-triangular/
├── app/                  # 실제 코드 (FastAPI 애플리케이션)
│   ├── main.py           #   - FastAPI 인스턴스, CORS, 라우터 등록
│   ├── api/              #   - 라우팅 계층
│   │   ├── api.py        #     · 최상위 api_router
│   │   ├── deps.py       #     · 공용 의존성 (DB 세션 등)
│   │   └── endpoints/    #     · 도메인별 엔드포인트 모듈
│   ├── core/             #   - 설정 (config.py, 환경변수 로딩)
│   ├── crud/             #   - DB CRUD 함수 (도메인 단위 파일)
│   ├── db/               #   - DB 클라이언트 (supabase.py 등)
│   ├── libs/             #   - 알고리즘 본체·유틸 (lower-triangular 구현 등)
│   ├── models/           #   - ORM/도메인 모델
│   └── schemas/          #   - Pydantic 입출력 스키마
├── claude/               # 본 문서들이 위치하는 작업 지침 디렉터리
│   ├── CLAUDE.md         #   - (현재 문서) 최상위 지침 / 인덱스
│   ├── base/             #   - 제품·UX·계층 조합 등 베이스 결정 문서
│   │   ├── CLAUDE.md        #     · base 레벨 변경 시 Claude 작업 지침 (인덱스)
│   │   ├── product.md       #     · 제품 목적·기대 효과·우선순위
│   │   ├── user-experience.md  # · 유저가 기대할 수 있는 경험
│   │   ├── architecture.md  #     · 계층(frontend·server·llm-include) 조합·인터페이스
│   │   └── progress.md      #     · base 문서 변경 이력 (매 변경마다 갱신)
│   ├── server/           #   - 서버(FastAPI) 영역 세부 지침
│   │   └── progress.md      #     · 기술 스택·별도 지침 변경 시에만 갱신
│   ├── frontend/         #   - 프론트엔드 영역 세부 지침
│   │   └── progress.md      #     · 기술 스택·별도 지침 변경 시에만 갱신
│   └── llm-include/      #   - LLM 프롬프트/컨텍스트에 포함할 자료
│       └── progress.md      #     · 기술 스택·별도 지침 변경 시에만 갱신
├── requirements.txt
├── README.md
├── .env                  # ❗ 절대 커밋 금지 (.gitignore 등록됨)
└── .gitignore
```

### 새 파일을 어디에 둘지 결정하는 규칙

- **HTTP 라우트가 추가될 때** → `app/api/endpoints/<도메인>.py`에 라우터 작성 후 `app/api/api.py`에서 `include_router` 한다.
- **요청/응답 형태(Pydantic)** → `app/schemas/<도메인>.py`.
- **DB에서 읽고 쓰는 함수** → `app/crud/<도메인>.py`. 라우트 함수 안에 SQL/Supabase 호출을 직접 쓰지 않는다.
- **순수 알고리즘 / 자료구조** → `app/libs/<모듈명>.py`. FastAPI·DB에 의존하지 않는 **순수 함수**로 유지해 단위 테스트가 쉽도록 한다.
- **환경설정·상수** → `app/core/config.py`. 매직넘버를 코드에 박지 않는다.

## 3. Python 코드 스타일 / 네이밍 규칙

기본은 **PEP 8**과 FastAPI 공식 예제 컨벤션을 따릅니다.

### 네이밍

| 종류                | 규칙                | 예시                              |
| ------------------- | ------------------- | --------------------------------- |
| 모듈/파일           | `snake_case.py`     | `lower_triangular.py`, `item.py`  |
| 패키지(디렉터리)    | `snake_case` 또는 짧은 단어 | `crud`, `schemas`, `endpoints` |
| 함수/변수           | `snake_case`        | `solve_lower_triangular(matrix)`  |
| 상수                | `UPPER_SNAKE_CASE`  | `MAX_MATRIX_SIZE = 1024`          |
| 클래스 / Pydantic   | `PascalCase`        | `ItemCreate`, `LowerTriSolution`  |
| 비공개(모듈 내부)   | `_leading_underscore` | `_validate_matrix(...)`         |

### 작성 규칙

- 한 줄 길이는 100자 이내(필요 시 88도 허용 — `black` 기본값).
- 들여쓰기는 **스페이스 4칸**. 탭 금지.
- import 순서: ① 표준 라이브러리 → ② 서드파티 → ③ `app.*` 내부 모듈. 각 블록 사이 빈 줄 한 개.
- 함수 시그니처에는 **타입 힌트를 반드시** 단다. 반환값이 없으면 `-> None`.
- 도메인 로직(`app/libs`) 함수는 입력·출력을 명확히 한 **순수 함수**로 작성한다. 부수효과(파일 I/O, DB, print) 금지.
- 예외 처리: 상위 라우트 계층에서 `HTTPException`으로 변환, 하위 계층은 도메인 예외(또는 `ValueError`)를 던진다.
- 주석은 한국어 또는 영어 중 한 모듈 내에서 **일관되게** 작성. "왜"를 설명하고, "무엇"은 코드가 말하게 한다.
- 모든 새 파일 끝에는 개행 한 줄(빈 줄) 유지.

### 테스트 / 검증

- 알고리즘 함수는 가능하면 **작은 단위 케이스**(빈 입력, 1×1, 대각, 비정방형 등)로 검증한다.
- 단위 테스트는 `tests/`(없으면 새로 생성)에 `test_<모듈명>.py`로 둔다. 프레임워크는 `pytest`.

## 4. Claude와의 작업 방식

Claude가 본 저장소에서 코드를 생성·수정할 때 지켜야 하는 절차입니다.

### 4.1 작업 전

1. **먼저 이 `CLAUDE.md`를 읽는다.** 그다음 작업 영역에 맞춰 다음 중 하나 이상을 더 읽는다.
   - 계층 경계 변경(스키마·LLM 흐름·새 엔드포인트 계약 등) → `claude/base/architecture.md` 와 `claude/base/CLAUDE.md`
   - 서버/API 변경 → `claude/server/`
   - 프론트엔드 변경 → `claude/frontend/`
   - LLM에 넘길 컨텍스트 정리 → `claude/llm-include/`
2. **요구사항이 모호하면 추측하지 말고 사용자에게 질문**한다. 특히:
   - 입력 형식(매트릭스 표현, 인덱스 0/1-기준 등)
   - 반환 형식(JSON 구조, 에러 코드)
   - 성능 제약(허용 시간, 입력 크기 상한)
3. **변경 범위를 먼저 짧게 요약**해 보여주고, 큰 리팩터링이면 사용자 승인을 받은 뒤 진행한다.

### 4.2 작업 중

- **작은 변경 단위**로 편집한다. 한 번에 여러 파일을 광범위하게 수정하지 않는다.
- 기존 코드 스타일과 네이밍을 그대로 따른다. "내 취향대로" 리네이밍 금지.
- 새 외부 라이브러리는 **반드시 사용자 확인 후** `requirements.txt`에 추가한다.
- `.env`, API 키, Supabase 시크릿은 **출력·로그·커밋 어디에도 노출 금지**.
- 데이터베이스 스키마 변경은 자체적으로 진행하지 않는다. 변경이 필요해 보이면 제안만 한다.

### 4.3 작업 후

- 변경한 파일 목록과 **무엇이/왜** 바뀌었는지 1–3줄로 요약한다.
- 단위 케이스 한두 개로 동작을 빠르게 확인하고, 결과를 보고한다.
- 다음에 사용자가 확인해야 할 항목(예: `.env` 값, 수동 마이그레이션)이 있으면 체크리스트로 남긴다.
- **`progress.md` 갱신을 잊지 않는다** — 규칙은 영역마다 다르다.
  - `claude/base/` 안의 문서를 한 줄이라도 손댔다면 → 같은 응답에서 `base/progress.md` §2에 한 줄 추가 (예외 없음).
  - 서버·프론트·LLM 영역에서 **기술 스택을 바꾸거나 영역별 별도 지침이 새로 굳어졌다면** → 해당 `<영역>/progress.md` §1/§3 갱신. 일반 코드 변경(라우트 추가, 컴포넌트 작업, 버그 수정, 프롬프트 문구 다듬기 등)은 기록하지 않는다.
  - 자세한 규칙은 [`claude/base/CLAUDE.md`](./base/CLAUDE.md) §5.

### 4.4 하지 말아야 할 것

- 사용자가 명시하지 않은 기능을 임의로 추가하지 않는다.
- 임의로 새로운 디렉터리·아키텍처 패턴을 도입하지 않는다(섹션 2 구조 유지).
- 알고리즘 풀이 본체를 `app/api/endpoints/` 안에 직접 작성하지 않는다 — `app/libs/`로 분리한다.
- 사용자에게 보여주지 않은 채 큰 파일을 통째로 새로 쓰지 않는다(부분 편집을 우선).

---

## 5. 하위 문서 인덱스

- [`base/CLAUDE.md`](./base/CLAUDE.md) — base 폴더의 인덱스. 어느 문서를 언제 읽고, 결정 우선순위가 어떻게 되는지 정의.
- [`base/product.md`](./base/product.md) — 제품 목적성·기대 효과·트레이드오프 우선순위.
- [`base/user-experience.md`](./base/user-experience.md) — 타깃 사용자·핵심 여정·인터랙션 원칙·UX 비-목표.
- [`base/architecture.md`](./base/architecture.md) — `frontend ↔ server ↔ llm-include` 조합 설계, 데이터 흐름, 인터페이스 규약.
- [`base/progress.md`](./base/progress.md) — base 문서 변경 이력 (모든 base 편집 시 함께 갱신).
- [`server/progress.md`](./server/progress.md), [`frontend/progress.md`](./frontend/progress.md), [`llm-include/progress.md`](./llm-include/progress.md) — 영역별 기술 스택 스냅샷과 별도 지침 이력 (기술 변경·별도 지침 추가 시에만 갱신).
- [`server/`](./server/) — FastAPI 라우터·CRUD·DB 작업 시 세부 규칙 (앞으로 작성).
- [`frontend/`](./frontend/) — 프론트엔드 작업 시 세부 규칙 (스택 확정 후 작성).
- [`llm-include/`](./llm-include/) — LLM에 넘길 프롬프트 템플릿·few-shot·도메인 자료 (앞으로 작성).

각 하위 폴더에 `README.md` 또는 `guide.md`를 두고, 본 `CLAUDE.md`에 링크를 추가하면서 점진적으로 확장합니다.
