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

- [S-01] 카테고리별 강의 개수 제약 (전공 N개 등) — B-3 하드 제약 ✓
  - owner: @claude  | priority: P2
  - 컨텍스트: 학점 *합* 제약(credit_min/max)은 있으나 "전공 3개" 같은 카테고리 *개수* 제약이 없음 (사용자 요청 기능 3). 추천 난이도 순서상 기능 2(쉬는시간, 완료) 다음으로 쉬움.
  - 산출물 (DONE 기준):
    1. ✓ `PreferenceVector`에 옵셔널 필드 `category_count_min`·`category_count_max: dict[Category,int]={}` 추가 + `_check_consistency`에 값 ≥0 / min ≤ max 검증.
    2. ✓ `valuation._enumerate_feasible_subsets.record()`에 `satisfies_category_counts()` 검사 추가 (credit_min·must_groups 옆). `Counter(by_id[cid].category for cid in chosen)` 카운트.
    3. ⏸ (선택) A-3 도달성 사전검증 + `InfeasibilityReason.CATEGORY_COUNT_UNREACHABLE` — 보류 (다음 카드로 분리 가능).
    4. ✓ `tests/test_category_count.py` 신규(7 케이스: 빈 dict·min/max 필터·정확 일치·불가능 min→0·validation 2건) + `drafts/algorithm-tree.md` §9.3(B-3) 한 줄 추가.
  - 관련 파일: `app/schemas/preferences.py`, `app/libs/valuation.py`, `tests/test_category_count.py`
  - 참고 문서: `claude/base/drafts/algorithm-tree.md` §9.3(B-3), `claude/base/progress.md` 2026-05-25 기능3 항목
  - 비고: 서버 닫힘 완료. 프론트 입력 UI 노출은 별도 F 카드로 분리 필요.
  - 변경일: 2026-05-25 (TODO → DONE)

- [S-02] 시간대 선호 페널티 λ₄ (이른 아침·늦은 저녁 회피) ✓
  - owner: @claude  | priority: P2
  - 컨텍스트: 지금은 정확 구간 문자열 `time_penalty_grid`("MON 0900-1015")로만 시간대를 깎을 수 있어 "9시 이전·18시 이후 전부 싫다"를 누르기 번거로움. 연속 임계값 λ로 일반화.
  - 산출물:
    1. ✓ `PreferenceVector`에 `time_window_lambda: float=0.0`(ge=0) + `preferred_start_minute: int=0` + `preferred_end_minute: int=24*60`. `_check_consistency`에 start<end 검증.
    2. ✓ `ScoreBreakdown.time_window_penalty: float=0.0` 전용 필드 + `total` 합산.
    3. ✓ `_build_breakdown`이 `_schedule_out_of_window_minutes()` 헬퍼로 창 밖 분 합산 → `-time_window_lambda * 창밖_분`.
    4. ✓ `tests/test_score_lambdas.py` 신규(out_of_window 4건·breakdown 필드 4건·validation 1건·통합 1건) + `drafts/algorithm-tree.md` §9.3 λ₄ 항 추가.
  - 관련 파일: `app/schemas/preferences.py`, `app/schemas/valuation.py`, `app/libs/valuation.py`, `tests/test_score_lambdas.py`
  - 변경일: 2026-05-25 (TODO → DONE)

- [S-03] 하루 등교 길이(span) 페널티 λ₅ ✓
  - owner: @claude  | priority: P2
  - 컨텍스트: `compactness_lambda`(λ₂)는 등교 *요일 수*만 보고 하루 안 늘어짐은 안 봄. "가는 날엔 짧게 끝내고 싶다"의 within-day 짝.
  - 산출물:
    1. ✓ `PreferenceVector.daily_span_lambda: float=0.0`(ge=0). 기본 0=비활성.
    2. ✓ `ScoreBreakdown.daily_span_penalty: float=0.0` 전용 필드 + `total` 합산.
    3. ✓ `_build_breakdown`이 `_schedule_total_daily_span_hours()` 헬퍼로 요일별 `(max end − min start)`를 시간 단위(/60) 합산 → `-daily_span_lambda * 총_span`.
    4. ✓ `tests/test_score_lambdas.py` 신규(span 3건·breakdown 필드 1건·validation 1건·통합 1건) + `drafts/algorithm-tree.md` §9.3 λ₅ 항 추가.
  - 관련 파일: `app/schemas/preferences.py`, `app/schemas/valuation.py`, `app/libs/valuation.py`, `tests/test_score_lambdas.py`
  - 변경일: 2026-05-25 (TODO → DONE)

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
