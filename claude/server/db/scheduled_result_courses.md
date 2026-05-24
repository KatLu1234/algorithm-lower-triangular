# 테이블: `scheduled_result_courses` (순위 시간표의 구성 강의 링크)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`ScoredSchedule.courses`(CourseId 리스트, 보통 시작 시간 순)를 정규화한 연결 테이블.
한 `scheduled_results` 행과 여러 `courses` 행을 N:M로 잇되, `position` 으로 시간 순서를 보존한다.

## 컬럼

| 컬럼                  | 타입        | NULL | 기본값      | 설명                                  |
| --------------------- | ----------- | ---- | ----------- | ------------------------------------- |
| `id`                  | bigint      | N    | identity    | 대리키 (PK)                           |
| `scheduled_result_id` | uuid        | N    | —           | 소속 순위 시간표 (FK)                 |
| `course_id`           | text        | N    | —           | 구성 강의 (FK→courses.id)             |
| `position`            | smallint    | N    | —           | 시간표 내 순서 (0-based, 시작 시간 순)|
| `created_at`          | timestamptz | N    | `now()`     | 생성 시각                             |

## 키 · 제약 · 인덱스

- **PK**: `(id)` (identity)
- **FK**: `scheduled_result_id → scheduled_results.id` ON DELETE CASCADE
- **FK**: `course_id → courses.id` ON DELETE CASCADE
- **CHECK**: `position >= 0`
- **UNIQUE**: `(scheduled_result_id, course_id)` — 같은 시간표에 같은 강의 중복 금지
- **UNIQUE**: `(scheduled_result_id, position)` — 순서 충돌 금지
- **인덱스**: `idx (scheduled_result_id)`

## 관계

- 참조: `scheduled_result_id → scheduled_results.id`, `course_id → courses.id`

## DDL

```sql
CREATE TABLE scheduled_result_courses (
    id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scheduled_result_id  uuid NOT NULL REFERENCES scheduled_results(id) ON DELETE CASCADE,
    course_id            text NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    position             smallint NOT NULL CHECK (position >= 0),
    created_at           timestamptz NOT NULL DEFAULT now(),
    UNIQUE (scheduled_result_id, course_id),
    UNIQUE (scheduled_result_id, position)
);
CREATE INDEX idx_srcourse_result ON scheduled_result_courses (scheduled_result_id);
```
