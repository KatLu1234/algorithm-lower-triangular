# 테이블: `users` (학생 = 선호 설정의 소유자)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`preference_sets`(저장된 PreferenceVector)와 그 결과의 소유 주체.
Supabase Auth 를 도입하면 `id` 를 `auth.users.id`(uuid)와 일치시켜 1:1 매핑할 수 있다.
현재는 독립 테이블로 두되 PK 타입을 uuid 로 맞춰 둔다.

- `product.md` §2.3 비-목적: 친구 시간표 매칭은 하지 않는다 → 사용자 간 관계 테이블은 두지 않는다.

## 컬럼

| 컬럼           | 타입        | NULL | 기본값                | 설명               |
| -------------- | ----------- | ---- | --------------------- | ------------------ |
| `id`           | uuid        | N    | `gen_random_uuid()`   | 사용자 식별자 (PK) |
| `email`        | text        | N    | —                     | 로그인 이메일      |
| `display_name` | text        | Y    | NULL                  | 표시 이름 (옵셔널) |
| `created_at`   | timestamptz | N    | `now()`               | 가입 시각          |
| `updated_at`   | timestamptz | N    | `now()`               | 갱신 시각          |

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **UNIQUE**: `(email)`
- **인덱스**: PK, unique(email)

> 이메일 형식 검증이 필요하면 애플리케이션 계층에서 처리한다(별도 DB 제약은 두지 않음).

## 관계

- 참조됨: `preference_sets.user_id → users.id`

## DDL

```sql
CREATE TABLE users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email         text NOT NULL UNIQUE,
    display_name  text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
```
