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

- [S-01] 카테고리별 강의 개수 제약 (전공 N개 등) — B-3 하드 제약
  - owner: 미배정  | priority: P2
  - 컨텍스트: 학점 *합* 제약(credit_min/max)은 있으나 "전공 3개" 같은 카테고리 *개수* 제약이 없음 (사용자 요청 기능 3). 추천 난이도 순서상 기능 2(쉬는시간, 완료) 다음으로 쉬움.
  - 산출물 (DONE 기준):
    1. `PreferenceVector`에 옵셔널 필드 `category_count_min: dict[Category,int]`·`category_count_max: dict[Category,int]` (기본 빈 dict) 추가 + `_check_consistency`에 검증(카테고리별 min≤max, 값 ≥0). 기본값=빈 dict 이므로 하위호환.
    2. `valuation._enumerate_feasible_subsets`의 `record()`에 카테고리 개수 검사 추가 (credit_min·must_groups 옆). `Counter(by_id[cid].category for cid in chosen)`로 카운트 후 min/max 위반 시 reject. `knapsack_01` 상한 가지치기는 카테고리를 무시하므로 여전히 유효한 상한(정답성 유지).
    3. (선택) A-3 도달성 사전검증 + `InfeasibilityReason.CATEGORY_COUNT_UNREACHABLE` 추가. (성능: dfs에서 max 도달 카테고리 가지치기 — 선택)
    4. `tests/`에 케이스(개수 부족·초과·정확 일치) + `drafts/algorithm-tree.md` §9.3(B-3) 명세에 한 줄 추가.
  - 관련 파일: `app/schemas/preferences.py`(필드·검증), `app/libs/valuation.py`(`_enumerate_feasible_subsets`/`record`), `app/schemas/common.py`(`Category`)
  - 참고 문서: `claude/base/drafts/algorithm-tree.md` §9.3(B-3), 본 세션 기능3 설계 논의(하드, B-3)
  - 비고: 핵심은 서버 닫힘(API로 동작 — bucket B 가중치들과 동일). 프론트 입력 UI 노출은 별도 F 카드로 분리 가능.
  - 변경일: 2026-05-25

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
