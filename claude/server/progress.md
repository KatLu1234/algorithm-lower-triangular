---
doc_type: progress-log
scope: server
title: 서버 영역 진행 이력
purpose: 서버 영역의 기술 스택 스냅샷과 별도 지침 변경 이력
target_reader: 서버 팀원 + base 작업자 (기술 변경 시)
update_rules:
  - 사용 기술 변경 시 (프레임워크·DB·LLM SDK·검증 라이브러리 교체/추가/제거)
  - 영역 한정 별도 지침 추가 시 (base 일반 규칙으로 안 풀리는 결정)
do_not_update_for:
  - 라우트 추가, 알고리즘 구현, 버그 수정, 일반적 리팩터링
  - 모두 git 커밋으로 충분
authoritative_for:
  - 서버 영역의 현재 기술 스택 (§1)
  - 서버 영역 한정 별도 지침 (§2)
not_authoritative_for:
  - 계층 경계·인터페이스 규약 → ../base/architecture.md
last_updated: 2026-06-01
---

# server/progress.md — 서버 영역 진행 이력

## 1. 현재 사용 기술 스택 (스냅샷)

**PURPOSE**: 영역의 권위 있는 기술 스택 상태.
**AUTHORITATIVE**: 본 절이 `team-guide.md` §3과 어긋나면 **본 절이 사실**.

| 분류 | 선택 | 비고 |
| ---- | ---- | ---- |
| 언어 | Python 3 | `.venv/` 가상환경 사용 |
| 웹 프레임워크 | FastAPI | `app/main.py` 진입점 |
| ASGI 서버 | (TBD, 보통 `uvicorn`) | 실행 명령 확정 시 기록 |
| 검증 / 모델 | Pydantic v2 | `app/schemas/` |
| 미들웨어 | Starlette CORS | `allow_origins=["*"]` (개발용) |
| DB | Supabase | `app/db/supabase.py` |
| 인증 | 로컬 SQLite (stdlib `sqlite3`, PBKDF2-SHA256) | `app/libs/auth_store.py`. DB 파일은 `settings.AUTH_DB_PATH` (기본 `data/auth.db`). Supabase Auth 미사용 — `auth.users` 트리거·RLS 정책은 카탈로그/결과 데이터에만 적용될 예정 |
| LLM 호출 단일 진입점 | (계획) `app/libs/llm_client.py` | 공급자 확정 시 기록 |
| LLM 프롬프트 조립 | (계획) `app/libs/llm_context.py` | `claude/llm-include/` 자료를 읽음 |
| 설정 / 시크릿 | `app/core/config.py` + `.env` | `.env`는 Git 제외 |
| 테스트 프레임워크 | (계획) `pytest` | `tests/` 폴더는 아직 없음 |

---

## 2. 별도 지침 (server 한정)

**PURPOSE**: `claude/base/` 일반 규칙으로 안 풀리는 서버 한정 결정 기록.
**INPUT**: 영역에 한정된 결정이 새로 굳어진 시점.
**OUTPUT**: 한 줄 결정 + 결정일 + 사유.

| 항목 | 결정 | 결정일 | 사유 |
| ---- | ---- | ------ | ---- |
| (예) 라우트 함수 시그니처 | 모든 라우트는 비동기(`async def`) | TBD | LLM 호출이 IO-bound이므로 |
|      |      |        |      |

---

## 3. 변경 이력

**PURPOSE**: 기술 스택 또는 별도 지침 변경의 시간 순 이력.
**RULE**: 가장 최근이 맨 위. 일반 코드 변경은 기재하지 않음.

| 날짜 | 항목 | 변경 | 사유 / 트리거 |
| ---- | ---- | ---- | ------------- |
| 2026-06-02 | 스택 추가 | **TLS 종단 + Let's Encrypt** 도입 (`docker-compose.yml` 에 certbot 서비스, nginx 80/443 분리, `frontend/nginx.conf` HTTP→HTTPS 리다이렉트+ACME webroot+TLS 서버, `init-letsencrypt.sh` 부트스트랩, `lt-auth-data` 볼륨으로 SQLite 영속화). nginx 6h reload·certbot 12h renew 루프 | 운영 토폴로지에 HTTPS 복원 — "다시 nginx 와 https 를 사용할 수 있도록" 사용자 지시 |
| 2026-06-01 | 스택 교체 | 인증 저장소를 **Supabase Auth → 로컬 SQLite**(`app/libs/auth_store.py` 영속화). `app/db/supabase_auth.py`·`SUPABASE_ANON_KEY` 제거, `AUTH_DB_PATH` 신설. 라우트 응답 모양·프론트 코드는 그대로 | 프로토타입은 외부 인증 의존 없이 단독 실행 가능해야 함(사용자 요청). Supabase 자체는 카탈로그/결과용 데이터 레이어로 계속 유지 |
| 2026-06-01 | 스택 추가 | Supabase Auth REST 연동 (`app/db/supabase_auth.py`, `SUPABASE_ANON_KEY` 설정). 비활성 시 인메모리 fallback(`app/libs/auth_store.py`). signup/login/me/logout 라우트 응답 모양은 두 모드 동일 | `server/db/auth-and-rls.md` 설계 적용 — 인증 주체를 `auth.users` 로, 프로필은 `handle_new_user` 트리거가 담당 |
| 2026-05-17 | 지침 추가 | `server/tasks.md` 신설 — 서버 영역 작업 칸반(TODO/DOING/DONE) + 카드 형식 + 영역 간 승격 기록. `team-guide.md` §2/§7/§8에 진입점 연결 | 팀원 작업 확인 보드 도입 |
| 2026-05-17 | 지침 추가 | `server/team-guide.md` 신설 — 서버 팀원 영역 진입 문서(책임·기술 스택 인용·할 일 매핑·Claude 사용 패턴·지침 요약·빠른 참조) | 영역 팀원 온보딩 통일 |
| 2026-05-17 | 진행 파일 | `server/progress.md` 신설, 현재 스택 스냅샷 기록 | "각 scheme에 진행상황 파일" 지시 |
| (2026-05-07 추정) | DB | Supabase 클라이언트(`app/db/supabase.py`) 도입 | 코드 히스토리상 추정 — 정확 일자/사유는 채울 것 |
| (2026-05-05 추정) | 골격 | FastAPI 골격(`app/main.py`, `api/`, `crud/`, `schemas/`) 생성 | 프로젝트 초기 셋업 |

---

## 4. 변경 유형 분류

**PURPOSE**: §3 변경 이력의 "항목" 컬럼 표준화 카테고리.

| 유형 | 의미 |
| ---- | ---- |
| 스택 추가 | 새 라이브러리·서비스 도입 |
| 스택 교체 | 기존 선택을 다른 것으로 변경 |
| 스택 제거 | 의존성 제거 |
| 지침 추가 | server 한정 규칙이 새로 굳어짐 |
| 지침 폐기 | 더 이상 적용되지 않는 규칙 제거 |
