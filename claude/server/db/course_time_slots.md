# 테이블: `course_time_slots` (강의의 개별 수업 시간)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`app/schemas/common.Course.times`(list[TimeSlot])를 정규화한 자식 테이블.
한 강의가 주당 여러 번(요일·시간) 열리면 그만큼 행이 생긴다. A-2 시간 충돌 검사가
본 데이터를 소비한다.

**건물은 슬롯 단위다.** `TimeSlot.building`에 대응하며, 한 강의가 요일마다 다른 건물에서
열릴 수 있으므로(예: 월 과기1관 / 화 농심국제관) 위치는 본 테이블에 둔다. 이동 시간
계산(A-2 충돌·B-2 합산)이 이 슬롯별 건물을 사용한다. `courses.building_code`는
표시용 대표 건물(옵셔널·denormalized)일 뿐 권위 있는 위치는 아니다.

- 분(minute)은 자정 기준 정수: 09:00 = 540, 10:30 = 630
- enum 출처(재사용): `day → app/schemas/common.Weekday`

## 컬럼

| 컬럼           | 타입        | NULL | 기본값      | 설명                       |
| -------------- | ----------- | ---- | ----------- | -------------------------- |
| `id`           | bigint      | N    | identity    | 대리키                     |
| `course_id`    | text        | N    | —           | 소속 강의 (FK→courses.id)  |
| `day`          | text        | N    | —           | 요일 (Weekday enum 값)     |
| `start_minute` | integer     | N    | —           | 시작 (자정 기준 분)        |
| `end_minute`   | integer     | N    | —           | 종료 (자정 기준 분)        |
| `building_code`| text        | N    | —           | 이 슬롯이 열리는 건물 (FK→buildings.code) |
| `created_at`   | timestamptz | N    | `now()`     | 생성 시각                  |

### enum 허용 값

- `day` ∈ { `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, `SUN` }

## 키 · 제약 · 인덱스

- **PK**: `(id)` (identity)
- **FK**: `course_id → courses.id` ON DELETE CASCADE
- **FK**: `building_code → buildings.code` ON DELETE RESTRICT
- **CHECK**: `start_minute >= 0 AND start_minute < 1440`
- **CHECK**: `end_minute >= 1 AND end_minute <= 1440`
- **CHECK**: `start_minute < end_minute`
- **인덱스**: `idx (course_id)`, `idx (course_id, day)`, `idx (building_code)`

## 관계

- 참조: `course_id → courses.id`
- 참조: `building_code → buildings.code`

## DDL

```sql
CREATE TABLE course_time_slots (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    course_id     text NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    day           text NOT NULL CHECK (day IN ('MON','TUE','WED','THU','FRI','SAT','SUN')),
    start_minute  integer NOT NULL CHECK (start_minute >= 0 AND start_minute < 1440),
    end_minute    integer NOT NULL CHECK (end_minute   >= 1 AND end_minute  <= 1440),
    building_code text NOT NULL REFERENCES buildings(code) ON DELETE RESTRICT,
    created_at    timestamptz NOT NULL DEFAULT now(),
    CHECK (start_minute < end_minute)
);
CREATE INDEX idx_slots_course     ON course_time_slots (course_id);
CREATE INDEX idx_slots_course_day ON course_time_slots (course_id, day);
CREATE INDEX idx_slots_building   ON course_time_slots (building_code);
```
