---
doc_type: tasks-board
scope: llm-include
title: LLM 자료 영역 작업 보드 (칸반)
purpose: LLM 자료 영역(프롬프트·few-shot·도메인 자료)의 작업 카드 TODO/DOING/DONE 관리
target_reader: LLM 자료 담당 팀원 (자신의 카드 확인 + 영역 진행 상황 파악)
card_id_prefix: I-
columns: [TODO, DOING, DONE]
doing_limit_per_person: 2
authoritative_for:
  - LLM 자료 영역에 닫힌 작업 카드 (I-NN)
  - 영역 간 승격된 카드의 이동 기록
not_authoritative_for:
  - 서버 측 빌더 연결까지 얽힌 카드 → ../base/tasks.md
  - 전체 진행 요약 → ../base/tasks.md
done_definition_for_new_task:
  - (a) 프롬프트 템플릿 (prompts/<task>.md)
  - (b) Few-shot 케이스 최소 1개 (examples/<task>/case-01.json)
  - (c) 메타 헤더 (목적·기대 사용처·마지막 수정일)
related_docs:
  - { path: ../base/tasks.md, why: 전체 작업 인덱스·교차 영역 카드·운영 규칙 }
  - { path: ./team-guide.md, why: 작업 유형별 위치 매핑 (§4) }
  - { path: ../base/user-experience.md, why: LLM 응답 톤·약속의 기준 }
last_updated: 2026-05-17
---

# llm-include/tasks.md — LLM 자료 영역 작업 보드 (칸반)

## 1. 카드 형식

**PURPOSE**: 카드 등록 시 복사해 채우는 표준 템플릿.

```
- [I-NN] 작업 제목 (한 줄)
  - owner: @담당자  | priority: P0/P1/P2
  - 컨텍스트: 왜 필요한가 1줄
  - 산출물: 무엇이 끝나면 DONE인가 — 프롬프트 1개·case N개·도메인 자료 X줄 등 구체적
  - 관련 task 이름: explain_lt / solve_schedule / ... (서버 빌더 함수명과 동일)
  - 관련 파일: prompts/<task>.md, examples/<task>/case-NN.json, domain/<주제>.md
  - 참고 문서: claude/llm-include/team-guide.md §X, claude/base/user-experience.md §3
  - 변경일: YYYY-MM-DD
```

**CONSTRAINTS**:
- `scheme 접두`: `I-`. 번호는 영역 안에서 순차 증가.
- 새 task 추가 카드는 `done_definition_for_new_task`의 (a)·(b)·(c) 모두 갖춰야 DONE.
- 한 사람당 동시 DOING 카드 **최대 2개**.

---

## 2. TODO

**PURPOSE**: 아직 시작 전 카드.

- [I-01] Upstage Solar API 조사 및 도메인 자료 작성
  - owner: @TBD  | priority: P1
  - 컨텍스트: LLM 공급자 후보(Upstage Solar API)의 사용법을 Claude가 프롬프트·서버 코드 작성 시 참조할 수 있도록 `domain/`에 도메인 자료로 정리. 실제 공급자 채택 결정은 별도 base 변경(본 카드 범위 밖).
  - 산출물:
      - `claude/llm-include/domain/upstage-solar-api.md` 1개 (신규). 상단 메타 헤더 필수: `목적 · 기대 사용처 · 마지막 수정일`.
      - 본문은 LLM이 컨텍스트로 받기 좋게 **정의 → 규칙 → 예시 → 자주 틀리는 점** 순(team-guide.md §4 도메인 자료 한 줄 규칙, §5.4 재구성 프롬프트):
          1. API 개요 — 제공 모델 라인업(모델명·용도·컨텍스트 길이), 베이스 URL, 인증 방식(`Authorization: Bearer …` 등).
          2. 엔드포인트별 요청·응답 JSON 스키마 (`/chat/completions`, `/embeddings`, `/document-ai` 등 실제 존재하는 것만 — 추측 금지, 확인된 것만 기재).
          3. 주요 파라미터 — `temperature`, `max_tokens`, `top_p`, `stream` 등 기본값·허용 범위.
          4. 호출 예시 — `curl` 1개 + Python(`requests` 또는 공식 SDK) 1개. **API 키는 더미값(`YOUR_UPSTAGE_API_KEY`)만 사용**.
          5. 부가 기능 — 스트리밍/함수 호출/임베딩/문서 AI 등 지원 여부와 한계.
          6. 에러 코드 · 재시도 정책 · rate limit.
          7. 가격 · 토큰 한도 (조사 시점 명기).
          8. Claude/LLM이 자주 틀리는 점 — OpenAI API 호환 여부, 파라미터 차이, 한국어 처리 특이점 등.
      - 작성 절차: AI(Claude)가 Upstage 공식 문서(docs.upstage.ai 등)를 WebSearch/WebFetch로 조사 → 위 구조로 재구성 → 사용자 검수 후 커밋. 시크릿/실키는 어떤 형태로도 포함 금지(가공된 더미만).
      - 추측·구버전 정보는 본문에 명시적 표기.
  - 관련 task 이름: (도메인 자료 — 특정 LLM task 매핑 없음)
  - 관련 파일: `claude/llm-include/domain/upstage-solar-api.md` (신규)
  - 참고 문서: `claude/llm-include/team-guide.md` §4 도메인 자료 행 · §5.4 도메인 자료 재구성 프롬프트; `claude/base/architecture.md` §2.1 (LLM SDK TBD) · §3.3 (llm-include 데이터-온리 원칙); `claude/base/CLAUDE.md` §1 (실제 공급자 채택은 base 변경)
  - 변경일: 2026-05-19

---

## 3. DOING

**PURPOSE**: 현재 작업 중인 카드.

(여기에 카드 추가)

---

## 4. DONE

**PURPOSE**: 완료 확인된 카드. 분기마다 §6 아카이브로 이동.

(여기에 카드 추가)

---

## 5. 영역 간 작업으로 승격된 카드

**PURPOSE**: 진행 중 server·frontend와 얽힌 카드의 이동 기록.
**RULE**: `../base/tasks.md`로 카드 본체를 옮기고 본 §5에 이전 사실만 한 줄. ID는 유지.

| 날짜 | ID | 이동 사유 |
| ---- | -- | --------- |
|      |    |           |

---

## 6. 아카이브

**PURPOSE**: 지난 분기 이전 DONE 카드 보관.

(분기마다 §4 DONE 카드를 여기로 이동)
