---
doc_type: tasks-board
scope: server
title: 서버 영역 작업 보드 (칸반)
purpose: 서버 영역에 닫혀 있는 작업 카드의 TODO/DOING/DONE 관리
target_reader: 서버 팀원 (자신의 카드 확인 + 영역 진행 상황 파악)
card_id_prefix: S-
columns: [TODO, DOING, DONE]
doing_limit_per_person: 2
authoritative_for:
  - 서버 영역에 닫힌 작업 카드 (S-NN)
  - 영역 간 승격된 카드의 이동 기록
not_authoritative_for:
  - 두 영역 이상 얽힌 카드 → ../base/tasks.md
  - 전체 진행 요약 → ../base/tasks.md
related_docs:
  - { path: ../base/tasks.md, why: 전체 작업 인덱스·교차 영역 카드·운영 규칙 }
  - { path: ./team-guide.md, why: 작업 유형별 책임 매핑 (§4) }
last_updated: 2026-05-17
---

# server/tasks.md — 서버 영역 작업 보드 (칸반)

## 1. 카드 형식

**PURPOSE**: 카드 등록 시 복사해 채우는 표준 템플릿.

```
- [S-NN] 작업 제목 (한 줄)
  - owner: @담당자  | priority: P0/P1/P2
  - 컨텍스트: 왜 필요한가 1줄
  - 산출물: 무엇이 끝나면 DONE인가 (구체적)
  - 관련 파일: app/api/endpoints/..., app/schemas/..., app/libs/...
  - 참고 문서: claude/server/team-guide.md §X, claude/base/...
  - 변경일: YYYY-MM-DD
```

**CONSTRAINTS**:
- `scheme 접두`: `S-`. 번호는 영역 안에서 순차 증가.
- `owner 미배정` 상태로 TODO에 올려도 됨. DOING으로 옮길 때는 반드시 owner 지정.
- 한 사람당 동시 DOING 카드 **최대 2개**.

---

## 2. TODO

**PURPOSE**: 아직 시작 전 카드.

(여기에 카드 추가)

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

**PURPOSE**: 진행 중 frontend·llm-include와 얽힌 카드의 이동 기록.
**RULE**: `../base/tasks.md`로 카드 본체를 옮기고 본 §5에 이전 사실만 한 줄. ID는 유지.

| 날짜 | ID | 이동 사유 |
| ---- | -- | --------- |
|      |    |           |

---

## 6. 아카이브

**PURPOSE**: 지난 분기 이전 DONE 카드 보관.

(분기마다 §4 DONE 카드를 여기로 이동)
