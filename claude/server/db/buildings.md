# 테이블: `buildings` (캠퍼스 건물 마스터)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계·생성 순서는 [`index.md`](./index.md).
> 본 문서는 **설계안**이며, 실제 적용은 맨 아래 DDL을 Supabase에서 실행하는 별도 단계다.

## 목적

캠퍼스 건물의 참조 테이블. 이동 시간 계산(B-2 플로이드-워셜)과 강의 위치의 기준점이다.
`courses.building_code` 와 `building_travel_times.from_code`/`to_code` 가 본 테이블의 `code` 를 참조한다.

- 대응 스키마: `app/schemas/common.BuildingCode` (= 본 테이블 PK `code`)

## 컬럼

| 컬럼        | 타입             | NULL | 기본값      | 설명                                |
| ----------- | ---------------- | ---- | ----------- | ----------------------------------- |
| `code`      | text             | N    | —           | 건물 코드 (PK, 자연키). 예: '공학관' |
| `name`      | text             | N    | —           | 건물 전체 표시명                    |
| `campus`    | text             | Y    | NULL        | 캠퍼스/구역 구분 (옵셔널)           |
| `latitude`  | double precision | Y    | NULL        | 위도 (지도/거리 추정용, 옵셔널)     |
| `longitude` | double precision | Y    | NULL        | 경도 (옵셔널)                       |
| `created_at`| timestamptz      | N    | `now()`     | 생성 시각                           |

## 키 · 제약 · 인덱스

- **PK**: `(code)`
- **인덱스**: PK 인덱스 외 추가 없음 (소규모 마스터 테이블)

## 관계

- 참조됨: `courses.building_code → buildings.code`
- 참조됨: `building_travel_times.from_code / to_code → buildings.code`

## DDL

```sql
CREATE TABLE buildings (
    code        text PRIMARY KEY,
    name        text NOT NULL,
    campus      text,
    latitude    double precision,
    longitude   double precision,
    created_at  timestamptz NOT NULL DEFAULT now()
);
```
