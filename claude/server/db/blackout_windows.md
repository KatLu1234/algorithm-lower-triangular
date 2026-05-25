# 테이블: `blackout_windows` (선호 설정의 절대 불가 시간대)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`app/schemas/common.BlackoutWindow` (PV.blackout_windows 리스트의 원소)를 영속화한다.
A-1이 이 시간대와 겹치는 슬롯을 하나라도 가진 강의를 풀에서 통째로 제거한다(강의는 슬롯을 쪼개 들을 수 없으므로 — 슬롯 단위 any 판정).

`days` 는 Weekday 값들의 배열(text[]). 정규화(요일별 한 행)하지 않고 배열로 두는 이유는
한 blackout 이 여러 요일에 같은 시간대로 걸리는 일이 흔하고, 검색 대상이 아니기 때문.

- enum 출처(재사용): `days 원소 → app/schemas/common.Weekday`

## 컬럼

| 컬럼                | 타입        | NULL | 기본값              | 설명                          |
| ------------------- | ----------- | ---- | ------------------- | ----------------------------- |
| `id`                | uuid        | N    | `gen_random_uuid()` | 식별자 (PK)                   |
| `preference_set_id` | uuid        | N    | —                   | 소속 선호 설정 (FK)           |
| `days`              | text[]      | N    | —                   | 적용 요일 (Weekday 값 배열)   |
| `start_minute`      | integer     | N    | —                   | 시작 (자정 기준 분)           |
| `end_minute`        | integer     | N    | —                   | 종료 (자정 기준 분)           |
| `reason`            | text        | Y    | NULL                | 사용자 표기 사유 (예: '통학') |
| `created_at`        | timestamptz | N    | `now()`             | 생성 시각                     |

### enum 허용 값

- `days` 원소 ∈ { `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, `SUN` }

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **FK**: `preference_set_id → preference_sets.id` ON DELETE CASCADE
- **CHECK**: `array_length(days, 1) >= 1`
- **CHECK**: `start_minute >= 0 AND start_minute < 1440`
- **CHECK**: `end_minute >= 1 AND end_minute <= 1440`
- **CHECK**: `start_minute < end_minute`
- **인덱스**: `idx (preference_set_id)`

## 관계

- 참조: `preference_set_id → preference_sets.id`

## DDL

```sql
CREATE TABLE blackout_windows (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    preference_set_id uuid NOT NULL REFERENCES preference_sets(id) ON DELETE CASCADE,
    days              text[] NOT NULL CHECK (array_length(days, 1) >= 1),
    start_minute      integer NOT NULL CHECK (start_minute >= 0 AND start_minute < 1440),
    end_minute        integer NOT NULL CHECK (end_minute   >= 1 AND end_minute  <= 1440),
    reason            text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    CHECK (start_minute < end_minute)
);
CREATE INDEX idx_blackout_set ON blackout_windows (preference_set_id);
```
