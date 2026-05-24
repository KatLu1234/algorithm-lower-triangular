# 테이블: `solve_runs` (최적화 1회 실행 = A→B→C 파이프라인 결과 헤더)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

한 `preference_set` 에 대해 알고리즘 트리를 돌린 결과를 영속화한다.
성공 시 통계(`ValuationResult`/`SelectionResult` 요약)를, 불가능 시
`InfeasibilityReport`(조기 종료) 내용을 함께 담는다.

- `ValuationResult` → `num_total_feasible` / `best_score` / `k_threshold_score`
- `SelectionResult` → `diversity_adjustment_applied`
- `InfeasibilityReport` → `infeasibility_*`, `resolution_hint`
- enum 출처(재사용): `infeasibility_reason → app/schemas/common.InfeasibilityReason`

순위 시간표는 [`scheduled_results`](./scheduled_results.md), 강의별 사유는
[`course_rationales`](./course_rationales.md) 로 분리.

## 컬럼

| 컬럼                           | 타입        | NULL | 기본값              | 설명                                   |
| ------------------------------ | ----------- | ---- | ------------------- | -------------------------------------- |
| `id`                           | uuid        | N    | `gen_random_uuid()` | 실행 식별자 (PK)                       |
| `preference_set_id`            | uuid        | N    | —                   | 입력 선호 설정 (FK)                    |
| `status`                       | text        | N    | —                   | success / infeasible / error           |
| `num_total_feasible`           | integer     | N    | `0`                 | 가지치기 후 가능한 시간표 총 개수      |
| `best_score`                   | numeric     | Y    | NULL                | top-K 중 최고 점수 (success 시)        |
| `k_threshold_score`            | numeric     | Y    | NULL                | top-K 중 최하 점수 (다양성 후처리 기준)|
| `diversity_adjustment_applied` | boolean     | N    | `false`             | C-1 다양성 5% 양보 적용 여부           |
| `infeasibility_reason`         | text        | Y    | NULL                | 조기 종료 사유 코드 (infeasible 시)    |
| `infeasibility_stage`          | text        | Y    | NULL                | 검출 단계 (예: 'A-1')                  |
| `infeasibility_detail`         | text        | Y    | NULL                | 사람이 읽는 1–2줄 진단                 |
| `resolution_hint`              | text        | Y    | NULL                | 어느 제약을 풀면 가능한지 안내         |
| `compute_ms`                   | numeric     | Y    | NULL                | 알고리즘 계산 시간(ms). 목표 ≤ 50ms.   |
| `created_at`                   | timestamptz | N    | `now()`             | 실행 시각                              |

### enum 허용 값

- `status` ∈ { `success`, `infeasible`, `error` }
- `infeasibility_reason` ∈ { `user_contradiction`, `must_include_invalid`,
  `must_include_blackout_conflict`, `empty_pool`, `must_include_group_empty`,
  `must_include_pair_conflict`, `group_pair_conflict`, `credit_ceiling_unreachable` } (NULL 허용)

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **FK**: `preference_set_id → preference_sets.id` ON DELETE CASCADE
- **CHECK**: `status IN ('success','infeasible','error')`
- **CHECK**: `num_total_feasible >= 0`
- **CHECK**: `infeasibility_reason IN (…8개…)` (NULL 허용)
- **인덱스**: `idx (preference_set_id)`, `idx (created_at)`

## 관계

- 참조: `preference_set_id → preference_sets.id`
- 참조됨: `scheduled_results.solve_run_id`, `course_rationales.solve_run_id`

## DDL

```sql
CREATE TABLE solve_runs (
    id                           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    preference_set_id            uuid NOT NULL REFERENCES preference_sets(id) ON DELETE CASCADE,
    status                       text NOT NULL CHECK (status IN ('success','infeasible','error')),
    num_total_feasible           integer NOT NULL DEFAULT 0 CHECK (num_total_feasible >= 0),
    best_score                   numeric,
    k_threshold_score            numeric,
    diversity_adjustment_applied boolean NOT NULL DEFAULT false,
    infeasibility_reason         text CHECK (infeasibility_reason IN (
        'user_contradiction','must_include_invalid','must_include_blackout_conflict',
        'empty_pool','must_include_group_empty','must_include_pair_conflict',
        'group_pair_conflict','credit_ceiling_unreachable')),
    infeasibility_stage          text,
    infeasibility_detail         text,
    resolution_hint              text,
    compute_ms                   numeric,
    created_at                   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_run_prefset ON solve_runs (preference_set_id);
CREATE INDEX idx_run_created ON solve_runs (created_at);
```
