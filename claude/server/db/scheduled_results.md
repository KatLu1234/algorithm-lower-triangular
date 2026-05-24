# 테이블: `scheduled_results` (한 실행이 낸 순위별 후보 시간표)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`app/schemas/valuation.ScoredSchedule` + 최종 순위(`rank`)를 영속화한다.
점수 분해(`ScoreBreakdown`)는 JSONB가 아니라 **명시 컬럼 8개**로 풀어 저장한다 —
`product.md` §4.3.1 산술 정확성·§4.3.2 설명 가능성(분해 1순위) 때문에 항별 감사·검산이
가능해야 하고 SQL 집계 검증도 쉽다. `total_score` 는 8개 항의 합과 일치해야 한다.

구성 강의(courses 집합)는 [`scheduled_result_courses`](./scheduled_result_courses.md)로
분리(시간 순 `position` 보존).

## 컬럼

| 컬럼                  | 타입        | NULL | 기본값              | 설명                            |
| --------------------- | ----------- | ---- | ------------------- | ------------------------------- |
| `id`                  | uuid        | N    | `gen_random_uuid()` | 식별자 (PK)                     |
| `solve_run_id`        | uuid        | N    | —                   | 소속 실행 (FK→solve_runs.id)    |
| `rank`                | smallint    | N    | —                   | 최종 순위 (1 = 최고)            |
| `used_credit`         | smallint    | N    | —                   | 학점 합                         |
| `total_score`         | numeric     | N    | —                   | 총점 (= 아래 8개 항의 합)       |
| `core_importance`     | numeric     | N    | —                   | Σ 중요도(c)×학점(c) — 핵심 점수 |
| `time_penalty`        | numeric     | N    | `0`                 | Σ 시간대 페널티 (보통 ≤ 0)      |
| `building_penalty`    | numeric     | N    | `0`                 | Σ 건물 페널티                   |
| `category_weight`     | numeric     | N    | `0`                 | Σ 카테고리 가중치 (보통 ≥ 0)    |
| `travel_penalty`      | numeric     | N    | `0`                 | −λ₁·총 이동시간 (보통 ≤ 0)      |
| `compactness_penalty` | numeric     | N    | `0`                 | −λ₂·(활성 요일−목표) (보통 ≤ 0) |
| `diversity_penalty`   | numeric     | N    | `0`                 | −λ₃·방문 건물 수 (보통 ≤ 0)     |
| `back_to_back_term`   | numeric     | N    | `0`                 | 연강/공강 선호 항               |
| `created_at`          | timestamptz | N    | `now()`             | 생성 시각                       |

> 검산 규칙: `total_score = core_importance + time_penalty + building_penalty +
> category_weight + travel_penalty + compactness_penalty + diversity_penalty + back_to_back_term`

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **FK**: `solve_run_id → solve_runs.id` ON DELETE CASCADE
- **CHECK**: `rank >= 1`, `used_credit >= 0`
- **UNIQUE**: `(solve_run_id, rank)` — 한 실행 안에서 순위 중복 금지
- **인덱스**: `idx (solve_run_id)`

## 관계

- 참조: `solve_run_id → solve_runs.id`
- 참조됨: `scheduled_result_courses.scheduled_result_id`

## DDL

```sql
CREATE TABLE scheduled_results (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    solve_run_id         uuid NOT NULL REFERENCES solve_runs(id) ON DELETE CASCADE,
    rank                 smallint NOT NULL CHECK (rank >= 1),
    used_credit          smallint NOT NULL CHECK (used_credit >= 0),
    total_score          numeric NOT NULL,
    core_importance      numeric NOT NULL,
    time_penalty         numeric NOT NULL DEFAULT 0,
    building_penalty     numeric NOT NULL DEFAULT 0,
    category_weight      numeric NOT NULL DEFAULT 0,
    travel_penalty       numeric NOT NULL DEFAULT 0,
    compactness_penalty  numeric NOT NULL DEFAULT 0,
    diversity_penalty    numeric NOT NULL DEFAULT 0,
    back_to_back_term    numeric NOT NULL DEFAULT 0,
    created_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (solve_run_id, rank)
);
CREATE INDEX idx_schedresult_run ON scheduled_results (solve_run_id);
```
