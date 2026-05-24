# 테이블: `building_travel_times` (건물 간 도보 이동 시간)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

B-2 전이 비용 전계산(플로이드-워셜)의 **입력 간선 목록**이자, 필요 시 모든 쌍 최단 경로
결과를 캐시하는 자리. 런타임에는 `FeasibilityResult.travel_time_table`
( `(from, to) → 분` )로 메모리에 올라가 O(1) 룩업된다.

- 대응 스키마: `app/schemas/feasibility.FeasibilityResult.travel_time_table`

### 대칭 가정

도보 시간은 보통 대칭이므로 한 방향만 저장해도 되며, `FeasibilityResult.travel_minutes()` 가
역방향 폴백을 제공한다. 비대칭(계단·일방통행)이 필요하면 양방향 행을 모두 넣는다.
같은 건물(자기 자신)은 행을 두지 않고 0으로 간주한다.

## 컬럼

| 컬럼        | 타입        | NULL | 기본값  | 설명                                  |
| ----------- | ----------- | ---- | ------- | ------------------------------------- |
| `from_code` | text        | N    | —       | 출발 건물 코드 (PK·FK→buildings.code) |
| `to_code`   | text        | N    | —       | 도착 건물 코드 (PK·FK→buildings.code) |
| `minutes`   | integer     | N    | —       | 도보 최단 분                          |
| `is_direct` | boolean     | N    | `true`  | 실측 직접 간선(true) vs 전계산 결과(false) |
| `created_at`| timestamptz | N    | `now()` | 생성 시각                             |

## 키 · 제약 · 인덱스

- **PK**: `(from_code, to_code)` — 건물 쌍 복합키
- **CHECK**: `minutes >= 0`
- **CHECK**: `from_code <> to_code` (자기 자신 거리는 저장하지 않고 0으로 처리)
- **FK**: `from_code → buildings.code` ON DELETE CASCADE
- **FK**: `to_code → buildings.code` ON DELETE CASCADE
- **인덱스**: PK `(from_code, to_code)`, `idx (from_code)`

## 관계

- 참조: `from_code`, `to_code` → `buildings.code`

## DDL

```sql
CREATE TABLE building_travel_times (
    from_code   text NOT NULL REFERENCES buildings(code) ON DELETE CASCADE,
    to_code     text NOT NULL REFERENCES buildings(code) ON DELETE CASCADE,
    minutes     integer NOT NULL CHECK (minutes >= 0),
    is_direct   boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (from_code, to_code),
    CHECK (from_code <> to_code)
);
CREATE INDEX idx_travel_from ON building_travel_times (from_code);
```
