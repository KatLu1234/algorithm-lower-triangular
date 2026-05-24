# 테이블: `preference_courses` (선호 설정의 후보 강의 + 강의별 제약)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`PreferenceVector` 의 강의 단위 필드들을 한 행으로 합쳐 정규화한다:

- `courses` — 후보 풀 멤버십 (이 행이 존재하면 후보)
- `course_importance` — `importance` (1~5, 기본 3)
- `must_include` — `selection_flag = 'must_include'`
- `exclude` — `selection_flag = 'exclude'`

`selection_flag` 는 본 테이블 전용 enum(스키마 직접 대응 없음 — PV의 두 집합을 한 컬럼으로 표현).

## 컬럼

| 컬럼                | 타입        | NULL | 기본값              | 설명                            |
| ------------------- | ----------- | ---- | ------------------- | ------------------------------- |
| `id`                | uuid        | N    | `gen_random_uuid()` | 식별자 (PK)                     |
| `preference_set_id` | uuid        | N    | —                   | 소속 선호 설정 (FK)             |
| `course_id`         | text        | N    | —                   | 후보 강의 (FK→courses.id)       |
| `importance`        | smallint    | N    | `3`                 | 강의별 중요도 (1~5)             |
| `selection_flag`    | text        | N    | `'normal'`          | normal / must_include / exclude |
| `created_at`        | timestamptz | N    | `now()`             | 생성 시각                       |

### enum 허용 값

- `selection_flag` ∈ { `normal`, `must_include`, `exclude` }

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **FK**: `preference_set_id → preference_sets.id` ON DELETE CASCADE
- **FK**: `course_id → courses.id` ON DELETE CASCADE
- **CHECK**: `importance BETWEEN 1 AND 5`
- **CHECK**: `selection_flag IN ('normal','must_include','exclude')`
- **UNIQUE**: `(preference_set_id, course_id)` — 후보 풀 내 강의 중복 금지
- **인덱스**: `idx (preference_set_id)`, unique`(preference_set_id, course_id)`

## 관계

- 참조: `preference_set_id → preference_sets.id`, `course_id → courses.id`

## DDL

```sql
CREATE TABLE preference_courses (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    preference_set_id uuid NOT NULL REFERENCES preference_sets(id) ON DELETE CASCADE,
    course_id         text NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    importance        smallint NOT NULL DEFAULT 3 CHECK (importance BETWEEN 1 AND 5),
    selection_flag    text NOT NULL DEFAULT 'normal'
                      CHECK (selection_flag IN ('normal','must_include','exclude')),
    created_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE (preference_set_id, course_id)
);
CREATE INDEX idx_prefcourse_set ON preference_courses (preference_set_id);
```
