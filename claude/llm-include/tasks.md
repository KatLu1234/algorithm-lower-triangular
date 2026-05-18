# llm-include/tasks.md — LLM 자료 영역 작업 보드 (칸반)

> **이 파일의 역할**
> LLM 자료 영역(프롬프트·few-shot·도메인 자료)의 모든 작업 카드를 관리합니다.
> 서버 측 빌더(`app/libs/llm_context.py`) 연결까지 얽히면 [`../base/tasks.md`](../base/tasks.md)로 이동.
> 칸반은 **TODO → DOING → DONE** 세 컬럼만. 카드 형식과 운영 규칙은 [`../base/tasks.md`](../base/tasks.md) 상단 참고.

---

## 카드 형식 (재게시)

```
- [I-NN] 작업 제목 (한 줄)
  - owner: @담당자  | priority: P0/P1/P2
  - 컨텍스트: 왜 필요한가 1줄
  - 산출물: 무엇이 끝나면 DONE인가 — 프롬프트 1개·case N개·도메인 자료 X줄 등 구체적으로
  - 관련 task 이름: explain_lt / solve_schedule / ... (서버 빌더 함수명과 동일)
  - 관련 파일: prompts/<task>.md, examples/<task>/case-NN.json, domain/<주제>.md
  - 참고 문서: claude/llm-include/team-guide.md §X, claude/base/user-experience.md §3
  - 변경일: YYYY-MM-DD
```

- **scheme 접두**: `I-`. 번호는 영역 안에서 순차 증가.
- 새 task 추가 카드라면 산출물에 **(a) 프롬프트 템플릿 (b) few-shot 케이스 최소 1개 (c) 메타 헤더**가 모두 포함돼야 DONE.
- 한 사람당 동시 DOING 카드 **최대 2개**.

---

## 1. TODO

> 아직 시작 전 카드.

(여기에 카드 추가)

## 2. DOING

> 현재 작업 중인 카드.

(여기에 카드 추가)

## 3. DONE

> 완료 확인된 카드. 분기마다 §5 아카이브로 이동.

(여기에 카드 추가)

---

## 4. 영역 간 작업으로 승격된 카드

> 진행하다 보니 server나 frontend와 얽힌다고 판단되면, [`../base/tasks.md`](../base/tasks.md)로 카드를 옮기고 본 §4에 이전 사실만 한 줄 남깁니다(같은 ID 유지).

| 날짜 | ID | 이동 사유 |
| ---- | -- | --------- |
|      |    |           |

## 5. 아카이브

(분기마다 §3 DONE 카드를 여기로 이동)
