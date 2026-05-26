# 테이블: `preference_sets` (저장된 PreferenceVector의 헤더)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`app/schemas/preferences.PreferenceVector` 한 건을 영속화한다. 단, PV의 컬렉션 필드는
정규화해서 자식 테이블로 분리한다:

- `PV.courses` + `course_importance` + `must_include` + `exclude` → [`preference_courses`](./preference_courses.md)
- `PV.must_include_groups` + `exclude_groups` → [`preference_groups`](./preference_groups.md)
- `PV.blackout_windows` → [`blackout_windows`](./blackout_windows.md)

본 헤더 행에는 학점 한도와 시간표 단위 후처리 가중치(스칼라), 그리고 dict 형태의
점수 가중치(JSONB)를 담는다. JSONB로 둔 가중치들은 키 집합이 가변적이라 정규화 이득이 적다.

## 컬럼

| 컬럼                      | 타입        | NULL | 기본값              | 설명                                |
| ------------------------- | ----------- | ---- | ------------------- | ----------------------------------- |
| `id`                      | uuid        | N    | `gen_random_uuid()` | 선호 설정 식별자 (PK)               |
| `user_id`                 | uuid        | N    | —                   | 소유자 (FK→users.id)                |
| `name`                    | text        | Y    | NULL                | 사용자 라벨 (예: '2026-1 시도1')    |
| `term`                    | text        | N    | —                   | 대상 학기 (courses.term 과 매칭)    |
| `credit_min`              | smallint    | N    | `0`                 | 학점 합 하한                        |
| `credit_max`              | smallint    | N    | —                   | 학점 합 상한 (0-1 배낭 용량)        |
| `travel_time_lambda`      | numeric     | N    | `0.1`               | 이동시간 분당 페널티 λ₁             |
| `compactness_lambda`      | numeric     | N    | `0.5`               | 활성 요일 초과당 페널티 λ₂          |
| `target_active_days`      | smallint    | N    | `5`                 | 목표 활성 요일 수                   |
| `diversity_lambda`        | numeric     | N    | `0.0`               | 건물 다양성 페널티 λ₃               |
| `back_to_back_preference` | numeric     | N    | `0.0`               | 연강/공강 선호 (부호 사용자 정의)   |
| `min_break_minutes`       | smallint    | N    | `0`                 | 같은 날 연속 수업 사이 최소 쉬는시간(분). A-2 하드 제약 |
| `time_penalty_grid`       | jsonb       | N    | `'{}'`              | 시간대 페널티 (구간 문자열 → 가중치)|
| `category_weights`        | jsonb       | N    | `'{}'`              | Category → 가중치                   |
| `requirement_weights`     | jsonb       | N    | `'{}'`              | Requirement → 가중치                |
| `building_penalties`      | jsonb       | N    | `'{}'`              | BuildingCode → 가중치               |
| `professor_preferences`   | jsonb       | N    | `'{}'`              | 교수 → 가중치                       |
| `category_count_min`      | jsonb       | N    | `'{}'`              | Category → 강의 *개수* 하한 (기능3)  |
| `category_count_max`      | jsonb       | N    | `'{}'`              | Category → 강의 *개수* 상한 (기능3)  |
| `created_at`              | timestamptz | N    | `now()`             | 생성 시각                           |
| `updated_at`              | timestamptz | N    | `now()`             | 갱신 시각                           |

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **FK**: `user_id → users.id` ON DELETE CASCADE
- **CHECK**: `credit_min >= 0`, `credit_max >= 1`, `credit_min <= credit_max`
- **CHECK**: `target_active_days BETWEEN 1 AND 7`
- **CHECK**: `travel_time_lambda >= 0`, `compactness_lambda >= 0`, `diversity_lambda >= 0`
- **CHECK**: `min_break_minutes >= 0`
- **인덱스**: `idx (user_id)`, `idx (term)`

## 관계

- 참조: `user_id → users.id`
- 참조됨: `preference_courses.preference_set_id`, `preference_groups.preference_set_id`,
  `blackout_windows.preference_set_id`, `solve_runs.preference_set_id`

## DDL

```sql
CREATE TABLE preference_sets (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                    text,
    term                    text NOT NULL,
    credit_min              smallint NOT NULL DEFAULT 0 CHECK (credit_min >= 0),
    credit_max              smallint NOT NULL CHECK (credit_max >= 1),
    travel_time_lambda      numeric NOT NULL DEFAULT 0.1 CHECK (travel_time_lambda >= 0),
    compactness_lambda      numeric NOT NULL DEFAULT 0.5 CHECK (compactness_lambda >= 0),
    target_active_days      smallint NOT NULL DEFAULT 5 CHECK (target_active_days BETWEEN 1 AND 7),
    diversity_lambda        numeric NOT NULL DEFAULT 0.0 CHECK (diversity_lambda >= 0),
    back_to_back_preference numeric NOT NULL DEFAULT 0.0,
    min_break_minutes       smallint NOT NULL DEFAULT 0 CHECK (min_break_minutes >= 0),
    time_penalty_grid       jsonb NOT NULL DEFAULT '{}'::jsonb,
    category_weights        jsonb NOT NULL DEFAULT '{}'::jsonb,
    requirement_weights     jsonb NOT NULL DEFAULT '{}'::jsonb,
    building_penalties      jsonb NOT NULL DEFAULT '{}'::jsonb,
    professor_preferences   jsonb NOT NULL DEFAULT '{}'::jsonb,
    category_count_min      jsonb NOT NULL DEFAULT '{}'::jsonb,
    category_count_max      jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now(),
    CHECK (credit_min <= credit_max)
);
CREATE INDEX idx_prefset_user ON preference_sets (user_id);
CREATE INDEX idx_prefset_term ON preference_sets (term);
```
