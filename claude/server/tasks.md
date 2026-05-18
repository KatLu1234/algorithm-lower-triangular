# server/tasks.md — 서버 영역 작업 보드 (칸반)

> **이 파일의 역할**
> 서버(FastAPI) 영역에 닫혀 있는 모든 작업 카드를 관리합니다. 두 영역 이상 얽히는 카드는 [`../base/tasks.md`](../base/tasks.md)에.
> 칸반은 **TODO → DOING → DONE** 세 컬럼만. 카드 형식과 운영 규칙은 [`../base/tasks.md`](../base/tasks.md) 상단 참고.

---

## 카드 형식 (재게시)

```
- [S-NN] 작업 제목 (한 줄)
  - owner: @담당자  | priority: P0/P1/P2
  - 컨텍스트: 왜 필요한가 1줄
  - 산출물: 무엇이 끝나면 DONE인가 (구체적)
  - 관련 파일: app/api/endpoints/..., app/schemas/..., app/libs/...
  - 참고 문서: claude/server/team-guide.md §X, claude/base/...
  - 변경일: YYYY-MM-DD
```

- **scheme 접두**: `S-`. 번호는 영역 안에서 순차 증가.
- **owner 미배정** 상태로 TODO에 올려도 됩니다. DOING으로 옮길 때는 반드시 owner 지정.
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

> 진행하다 보니 frontend나 llm-include와 얽힌다고 판단되면, [`../base/tasks.md`](../base/tasks.md)로 카드를 옮기고 본 §4에 이전 사실만 한 줄 남깁니다(같은 ID 유지).

| 날짜 | ID | 이동 사유 |
| ---- | -- | --------- |
|      |    |           |

## 5. 아카이브

(분기마다 §3 DONE 카드를 여기로 이동)
