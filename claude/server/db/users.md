# 테이블: `users` (학생 = 선호 설정의 소유자)

> DB 설계 문서 — 한 테이블당 한 파일. 전체 목록·관계는 [`index.md`](./index.md).

## 목적

`preference_sets`(저장된 PreferenceVector)와 그 결과의 소유 주체.

**Supabase Auth 연동(확정).** 인증·계정·비밀번호는 Supabase가 관리하는 `auth.users`가
담당하고, 본 테이블(`public.users`)은 앱 전용 프로필(표시 이름 등)을 보관한다.
`id` 는 자체 생성하지 않고 **`auth.users.id` 를 그대로 참조**한다(1:1). 따라서 RLS에서
`auth.uid() = users.id` 로 본인 여부를 판정할 수 있다. 전체 정책은 [`auth-and-rls.md`](./auth-and-rls.md).

회원가입(`auth.users` INSERT) 시 `handle_new_user` 트리거가 본 테이블에 1행을 자동
생성하며 `email`·`display_name` 을 채운다(트리거 정의는 `auth-and-rls.md`).

- `product.md` §2.3 비-목적: 친구 시간표 매칭은 하지 않는다 → 사용자 간 관계 테이블은 두지 않는다.

## 컬럼

| 컬럼           | 타입        | NULL | 기본값      | 설명                                         |
| -------------- | ----------- | ---- | ----------- | -------------------------------------------- |
| `id`           | uuid        | N    | —           | 사용자 식별자 (PK = FK→`auth.users.id`)      |
| `email`        | text        | N    | —           | 로그인 이메일 (가입 시 `auth.users`에서 복사)|
| `display_name` | text        | Y    | NULL        | 표시 이름 (옵셔널)                           |
| `created_at`   | timestamptz | N    | `now()`     | 가입 시각                                    |
| `updated_at`   | timestamptz | N    | `now()`     | 갱신 시각                                    |

## 키 · 제약 · 인덱스

- **PK**: `(id)`
- **FK**: `id → auth.users(id)` ON DELETE CASCADE — 계정 삭제 시 프로필·하위 데이터 연쇄 삭제
- **UNIQUE**: `(email)`
- **인덱스**: PK, unique(email)
- **RLS**: 활성. 본인 행만 SELECT/UPDATE (`auth.uid() = id`). INSERT는 트리거(service_role)가 담당.

> `id` 에 `DEFAULT gen_random_uuid()` 를 두지 않는다 — 값의 출처는 항상 `auth.users` 다.
> `email` 은 가입 시점 스냅샷이며, 사용자가 Auth에서 이메일을 바꾸면 드리프트가 생길 수 있다.
> 필요 시 `auth.users` 변경 트리거로 동기화하거나, 표시용으로만 쓰고 권위 출처는 `auth.users` 로 둔다.

## 관계

- 참조: `id → auth.users.id` (Supabase 관리 스키마)
- 참조됨: `preference_sets.user_id → users.id`

## DDL

```sql
CREATE TABLE users (
    id            uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email         text NOT NULL UNIQUE,
    display_name  text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
```

> 회원가입 자동 생성 트리거(`handle_new_user`)와 RLS 정책 DDL은 [`auth-and-rls.md`](./auth-and-rls.md) 참조.
