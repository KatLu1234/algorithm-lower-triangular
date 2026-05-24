# 테이블: `course_rationales` (실행별 강의 포함/배제 사유 색인)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`app/schemas/selection.Rationale` (SelectionResult.course_rationale 의 값)을 영속화한다.
C-3 사유 색인 — `product.md` §4.3.2 설명 가능성의 1순위(제외 사유)·2순위(포함 사유) 자료이고,
LLM-B 풀이의 단일 진실 출처다. 한 실행의 후보 풀 모든 강의에 대해 1행씩 생긴다.

- enum 출처(재사용): `status → app/schemas/selection.RationaleStatus`,
  `stage_code → app/schemas/selection.StageCode`

`related_course_ids` 는 결정에 관여한 다른 강의(시간 충돌 상대·같은 그룹 다른 분반 등)를
`text[]` 로 담는다. `courses` 로의 강한 FK는 걸지 않는다(스냅샷 성격, 카탈로그 변경에 견고).

## 컬럼

| 컬럼                 | 타입        | NULL | 기본값              | 설명                                |
| -------------------- | ----------- | ---- | ------------------- | ----------------------------------- |
| `id`                 | uuid        | N    | `gen_random_uuid()` | 식별자 (PK)                         |
| `solve_run_id`       | uuid        | N    | —                   | 소속 실행 (FK→solve_runs.id)        |
| `course_id`          | text        | N    | —                   | 대상 강의 (FK→courses.id)           |
| `status`             | text        | N    | —                   | included / excluded                 |
| `stage_code`         | text        | N    | —                   | 결정이 일어난 트리 단계 코드        |
| `detail`             | text        | N    | —                   | 사람이 읽는 1줄 설명                |
| `score_contribution` | numeric     | Y    | NULL                | 포함 강의의 v(c) 기여 (있을 때만)   |
| `related_course_ids` | text[]      | N    | `'{}'`              | 결정에 관여한 다른 강의 ID          |
| `created_at`         | timestamptz | N    | `now()`             | 생성 시각                           |

### enum 허용 값

- `status` ∈ { `included`, `excluded` }
- `stage_code` ∈ { `A-1.must_include`, `B-3.selected_by_DP`, `A-1.user_excluded`,
  `A-1.data_invalid`, `A-1.blackout_conflict`, `A-1.group_excluded`, `A-2.time_conflict`,
  `A-2.travel_infeasible`, `A-2.group_duplicate`, `A-3.pruned`, `B-3.score_too_low`,
  `B-3.credit_bumped`, `B-3.group_loser`, `C-1.not_in_top_n` }

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **FK**: `solve_run_id → solve_runs.id` ON DELETE CASCADE
- **FK**: `course_id → courses.id` ON DELETE CASCADE
- **CHECK**: `status IN ('included','excluded')`
- **CHECK**: `stage_code IN (…14개…)`
- **UNIQUE**: `(solve_run_id, course_id)` — 실행당 강의 1행
- **인덱스**: `idx (solve_run_id)`

## 관계

- 참조: `solve_run_id → solve_runs.id`, `course_id → courses.id`

## DDL

```sql
CREATE TABLE course_rationales (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    solve_run_id        uuid NOT NULL REFERENCES solve_runs(id) ON DELETE CASCADE,
    course_id           text NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    status              text NOT NULL CHECK (status IN ('included','excluded')),
    stage_code          text NOT NULL CHECK (stage_code IN (
        'A-1.must_include','B-3.selected_by_DP',
        'A-1.user_excluded','A-1.data_invalid','A-1.blackout_conflict','A-1.group_excluded',
        'A-2.time_conflict','A-2.travel_infeasible','A-2.group_duplicate',
        'A-3.pruned','B-3.score_too_low','B-3.credit_bumped','B-3.group_loser',
        'C-1.not_in_top_n')),
    detail              text NOT NULL,
    score_contribution  numeric,
    related_course_ids  text[] NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (solve_run_id, course_id)
);
CREATE INDEX idx_rationale_run ON course_rationales (solve_run_id);
```
