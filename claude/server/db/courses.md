# 테이블: `courses` (강의 = 분반 단위)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`app/schemas/common.Course` 의 영속화 대상. 단, 스키마의 `Course.times`(list[TimeSlot])는
정규화해서 자식 테이블 [`course_time_slots`](./course_time_slots.md)로 분리한다. 본 행에는
시간 슬롯을 두지 않는다.

**건물은 슬롯 단위로 이동**했다. 권위 있는 위치는 `course_time_slots.building_code`이고,
본 테이블의 `building_code`는 표시·필터용 **대표 건물(옵셔널·denormalized)**일 뿐이다
(보통 가장 자주 쓰는 건물). 한 강의가 요일마다 다른 건물에서 열릴 수 있기 때문이다.

같은 *과목*의 여러 분반은 서로 다른 `id` 를 가지되 같은 `course_group_id` 를 공유한다
(A-2가 그룹 동일성을 양립 불가 조건으로 적용 — 그룹당 최대 1개 선택).

- enum 출처(재사용): `category → app/schemas/common.Category`, `requirement → app/schemas/common.Requirement`

## 컬럼

| 컬럼              | 타입        | NULL | 기본값  | 설명                                       |
| ----------------- | ----------- | ---- | ------- | ------------------------------------------ |
| `id`              | text        | N    | —       | 강의(분반) 코드 (PK). 예: 'CS101-01-홍교수' |
| `term`            | text        | N    | —       | 학기 (예: '2026-1'). 단일 학기 범위.       |
| `name`            | text        | N    | —       | 강의명                                     |
| `credit`          | smallint    | N    | —       | 학점 (양수)                                |
| `building_code`   | text        | Y    | NULL    | 대표(denormalized) 건물. 실제 위치는 course_time_slots. (FK→buildings.code) |
| `category`        | text        | N    | —       | 카테고리 (Category enum 값)                |
| `requirement`     | text        | Y    | NULL    | 이수 요건 (Requirement enum 값). 옵셔널.   |
| `course_group_id` | text        | Y    | NULL    | 분반 묶음 키. 같은 값끼리 상호 배타.       |
| `section`         | text        | Y    | NULL    | 분반 라벨 (예: 'A반', '01'). 표시용.       |
| `professor`       | text        | Y    | NULL    | 담당 교수. 표시 + 교수 가중치 룩업 키.     |
| `created_at`      | timestamptz | N    | `now()` | 생성 시각                                  |

### enum 허용 값

- `category` ∈ { `전공`, `복수전공`, `교양`, `일선` }
- `requirement` ∈ { `필수`, `선택`, `자율` } (NULL 허용)

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **CHECK**: `credit >= 1`
- **CHECK**: `category IN ('전공','복수전공','교양','일선')`
- **CHECK**: `requirement IN ('필수','선택','자율')`
- **FK**: `building_code → buildings.code` ON DELETE RESTRICT
- **인덱스**: `idx (term)`, `idx (course_group_id)`, `idx (building_code)`

## 관계

- 참조: `building_code → buildings.code`
- 참조됨: `course_time_slots.course_id`, `preference_courses.course_id`,
  `scheduled_result_courses.course_id`, `course_rationales.course_id`

## DDL

```sql
CREATE TABLE courses (
    id              text PRIMARY KEY,
    term            text NOT NULL,
    name            text NOT NULL,
    credit          smallint NOT NULL CHECK (credit >= 1),
    building_code   text REFERENCES buildings(code) ON DELETE RESTRICT,  -- 대표 건물(옵셔널), 권위 위치는 course_time_slots
    category        text NOT NULL CHECK (category IN ('전공','복수전공','교양','일선')),
    requirement     text CHECK (requirement IN ('필수','선택','자율')),
    course_group_id text,
    section         text,
    professor       text,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_courses_term     ON courses (term);
CREATE INDEX idx_courses_group    ON courses (course_group_id);
CREATE INDEX idx_courses_building ON courses (building_code);
```
