# 테이블: `preference_groups` (선호 설정의 과목 그룹 단위 제약)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`PreferenceVector.must_include_groups` 와 `exclude_groups` 를 한 테이블로 합쳐 정규화한다.
`course_group_id` 는 `courses.course_group_id` 와 같은 도메인의 값(분반 묶음 키)이지만,
그룹은 독립 테이블이 아니라 강의에 부착된 라벨이므로 FK를 걸지 않고 텍스트로 저장한다.

`constraint_type` 은 본 테이블 전용 enum:

- `must_include` — 그룹 내 분반 중 *적어도 하나* 가 결과에 포함 (어느 분반인지는 시스템 선택)
- `exclude` — 그룹의 모든 분반을 풀에서 제거

PV 검증 규칙상 같은 그룹이 must_include·exclude 동시일 수 없으므로
`(preference_set_id, course_group_id)` 를 UNIQUE 로 두어 그룹당 한 행만 허용한다.

## 컬럼

| 컬럼                | 타입        | NULL | 기본값              | 설명                                          |
| ------------------- | ----------- | ---- | ------------------- | --------------------------------------------- |
| `id`                | uuid        | N    | `gen_random_uuid()` | 식별자 (PK)                                   |
| `preference_set_id` | uuid        | N    | —                   | 소속 선호 설정 (FK)                           |
| `course_group_id`   | text        | N    | —                   | 과목 그룹 키 (courses.course_group_id 도메인) |
| `constraint_type`   | text        | N    | —                   | must_include / exclude                        |
| `created_at`        | timestamptz | N    | `now()`             | 생성 시각                                     |

### enum 허용 값

- `constraint_type` ∈ { `must_include`, `exclude` }

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **FK**: `preference_set_id → preference_sets.id` ON DELETE CASCADE
- **CHECK**: `constraint_type IN ('must_include','exclude')`
- **UNIQUE**: `(preference_set_id, course_group_id)` — 그룹당 한 제약만
- **인덱스**: `idx (preference_set_id)`

## 관계

- 참조: `preference_set_id → preference_sets.id`
- 느슨한 참조: `course_group_id` ↔ `courses.course_group_id` (FK 미설정)

## DDL

```sql
CREATE TABLE preference_groups (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    preference_set_id uuid NOT NULL REFERENCES preference_sets(id) ON DELETE CASCADE,
    course_group_id   text NOT NULL,
    constraint_type   text NOT NULL CHECK (constraint_type IN ('must_include','exclude')),
    created_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE (preference_set_id, course_group_id)
);
CREATE INDEX idx_prefgroup_set ON preference_groups (preference_set_id);
```
