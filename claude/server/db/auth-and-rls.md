# 인증 연동 · RLS(행 수준 보안) 정책

> DB 설계 문서 — 횡단(여러 테이블에 걸친) 보안 설계. 테이블별 상세는 각 파일, 전체 목록은 [`index.md`](./index.md).
>
> **상태: 설계안.** 실제 적용은 아래 SQL을 Supabase에서 실행하는 별도 단계다
> (`../../CLAUDE.md` §4.2 — 사용자 확인 후 적용).

## 1. 결정 사항

웹 사용자 인증은 **Supabase Auth 연동**으로 확정. 핵심 원칙은 두 가지다.

- **인증 주체는 `auth.users`** — Supabase가 관리. 우리 `public.users` 는 프로필만 보관하고
  `id` 로 `auth.users.id` 를 참조한다([`users.md`](./users.md)).
- **모든 공개 테이블에 RLS 활성** — 클라이언트(웹)는 익명(anon) 키 + 로그인 세션(JWT)으로만
  접근하고, RLS가 `auth.uid()` 로 본인 데이터만 통과시킨다.

## 2. 키 사용 원칙 (가장 중요)

| 주체 | 사용 키 | RLS | 역할 |
| ---- | ------- | --- | ---- |
| **프론트엔드(웹)** | anon / Publishable | **적용됨** | 로그인 후 본인 데이터 읽기·쓰기. 키가 노출돼도 RLS가 막아줌 |
| **백엔드(FastAPI)** | service_role / Secret | **우회됨** | 알고리즘 실행 결과 기록, 카탈로그 적재. 서버 밖으로 절대 노출 금지 |

- service_role 키는 RLS를 **무시**하므로, 절대로 프론트엔드 번들·로그·git에 넣지 않는다.
  서버에서 `app/core/config.py` 의 `SUPABASE_KEY` 로만 읽는다(시크릿 단일 출처 규칙).
- 따라서 RLS 정책은 *프론트엔드가 직접 Supabase에 접근할 때*의 안전망이다. 백엔드는
  service_role로 우회하므로 결과 테이블 쓰기에 별도 INSERT 정책이 필요 없다.

## 3. `public.users` ↔ `auth.users` 연동 트리거

회원가입(`auth.users` 행 생성) 시 프로필 행을 자동 생성한다.

```sql
-- 신규 가입자의 프로필을 public.users 에 자동 생성
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.users (id, email, display_name)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data ->> 'display_name'   -- 가입 폼에서 넘긴 표시 이름(없으면 NULL)
  );
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

`SECURITY DEFINER` 라서 트리거는 RLS와 무관하게 INSERT한다(그래서 `users` 에 INSERT 정책이 없어도 됨).

## 4. 소유권 헬퍼 함수

자식 테이블은 `user_id` 를 직접 갖지 않고 상위로 거슬러 올라가야 한다. 정책마다 JOIN을
반복하지 않도록 헬퍼 함수 3개로 캡슐화한다(모두 `STABLE` + `SECURITY DEFINER`).

```sql
-- 이 preference_set 이 현재 로그인 사용자 소유인가?
CREATE OR REPLACE FUNCTION public.owns_preference_set(ps_id uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (
    SELECT 1 FROM preference_sets ps
    WHERE ps.id = ps_id AND ps.user_id = auth.uid()
  );
$$;

-- 이 solve_run 이 현재 로그인 사용자 소유인가? (run → preference_set → user)
CREATE OR REPLACE FUNCTION public.owns_solve_run(run_id uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (
    SELECT 1 FROM solve_runs s
    JOIN preference_sets ps ON ps.id = s.preference_set_id
    WHERE s.id = run_id AND ps.user_id = auth.uid()
  );
$$;

-- 이 scheduled_result 가 현재 로그인 사용자 소유인가? (result → run → preference_set → user)
CREATE OR REPLACE FUNCTION public.owns_scheduled_result(res_id uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (
    SELECT 1 FROM scheduled_results r
    JOIN solve_runs s ON s.id = r.solve_run_id
    JOIN preference_sets ps ON ps.id = s.preference_set_id
    WHERE r.id = res_id AND ps.user_id = auth.uid()
  );
$$;
```

## 5. 테이블별 RLS 정책

### 5.1 참조 데이터(카탈로그) — 공개 읽기, 클라이언트 쓰기 금지

`buildings`, `building_travel_times`, `courses`, `course_time_slots` 4개. 강의 카탈로그는
모든 로그인 사용자가 읽되, 적재·수정은 service_role(백엔드)만 한다(쓰기 정책 없음).

```sql
ALTER TABLE buildings             ENABLE ROW LEVEL SECURITY;
ALTER TABLE building_travel_times ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses               ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_time_slots     ENABLE ROW LEVEL SECURITY;

CREATE POLICY catalog_read ON buildings
  FOR SELECT TO authenticated USING (true);
CREATE POLICY catalog_read ON building_travel_times
  FOR SELECT TO authenticated USING (true);
CREATE POLICY catalog_read ON courses
  FOR SELECT TO authenticated USING (true);
CREATE POLICY catalog_read ON course_time_slots
  FOR SELECT TO authenticated USING (true);
```

> 비로그인 사용자도 강의 검색을 허용하려면 `TO authenticated` 를 `TO anon, authenticated` 로 넓힌다.
> 쓰기 정책을 만들지 않았으므로 anon/authenticated 는 INSERT·UPDATE·DELETE 불가(service_role만 가능).

### 5.2 사용자 소유 데이터 — 본인 행만

`FOR ALL` 로 SELECT·INSERT·UPDATE·DELETE 모두 동일 소유권 조건을 적용한다. INSERT는
`WITH CHECK` 가, 나머지는 `USING` 이 본인 여부를 검사한다.

```sql
-- users: 본인 프로필만 (INSERT는 트리거가 담당하므로 정책에서 제외)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_self_select ON users
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY user_self_update ON users
  FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- preference_sets: user_id 직접 비교
ALTER TABLE preference_sets ENABLE ROW LEVEL SECURITY;
CREATE POLICY prefset_owner ON preference_sets
  FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- preference_courses / preference_groups / blackout_windows / solve_runs:
--   preference_set 소유로 판정
ALTER TABLE preference_courses ENABLE ROW LEVEL SECURITY;
CREATE POLICY pc_owner ON preference_courses
  FOR ALL
  USING (public.owns_preference_set(preference_set_id))
  WITH CHECK (public.owns_preference_set(preference_set_id));

ALTER TABLE preference_groups ENABLE ROW LEVEL SECURITY;
CREATE POLICY pg_owner ON preference_groups
  FOR ALL
  USING (public.owns_preference_set(preference_set_id))
  WITH CHECK (public.owns_preference_set(preference_set_id));

ALTER TABLE blackout_windows ENABLE ROW LEVEL SECURITY;
CREATE POLICY bw_owner ON blackout_windows
  FOR ALL
  USING (public.owns_preference_set(preference_set_id))
  WITH CHECK (public.owns_preference_set(preference_set_id));

ALTER TABLE solve_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY sr_owner ON solve_runs
  FOR ALL
  USING (public.owns_preference_set(preference_set_id))
  WITH CHECK (public.owns_preference_set(preference_set_id));

-- scheduled_results / course_rationales: solve_run 소유로 판정
ALTER TABLE scheduled_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY sres_owner ON scheduled_results
  FOR ALL
  USING (public.owns_solve_run(solve_run_id))
  WITH CHECK (public.owns_solve_run(solve_run_id));

ALTER TABLE course_rationales ENABLE ROW LEVEL SECURITY;
CREATE POLICY cr_owner ON course_rationales
  FOR ALL
  USING (public.owns_solve_run(solve_run_id))
  WITH CHECK (public.owns_solve_run(solve_run_id));

-- scheduled_result_courses: scheduled_result 소유로 판정
ALTER TABLE scheduled_result_courses ENABLE ROW LEVEL SECURITY;
CREATE POLICY src_owner ON scheduled_result_courses
  FOR ALL
  USING (public.owns_scheduled_result(scheduled_result_id))
  WITH CHECK (public.owns_scheduled_result(scheduled_result_id));
```

> 결과 테이블(`solve_runs`·`scheduled_results`·`scheduled_result_courses`·`course_rationales`)은
> 백엔드가 service_role로 기록하므로 위 정책의 INSERT(`WITH CHECK`)는 *프론트가 직접 쓰는*
> 경우에만 작동한다. 읽기(SELECT)는 프론트가 직접 하므로 소유권 USING이 핵심이다.

## 6. 적용 순서

1. 13개 테이블 DDL을 [`index.md`](./index.md) §3 순서대로 생성(`auth.users` 는 Supabase가 이미 제공).
2. §3 트리거 함수·트리거 생성.
3. §4 헬퍼 함수 3개 생성.
4. §5 RLS 활성화 + 정책 생성.
5. Supabase 대시보드 → Authentication에서 이메일 가입 등 로그인 방식을 켠다.
6. 백엔드 `.env` 의 `SUPABASE_KEY` 를 **service_role** 키로 설정(서버 전용). 프론트는 anon 키 사용.

## 7. 검증 체크리스트

- 로그인 A로 만든 `preference_sets` 를 로그인 B가 SELECT → 0행이어야 한다.
- anon 키로 `courses` SELECT → 가능, `courses` INSERT → 거부돼야 한다.
- service_role 키로 `scheduled_results` INSERT → RLS 무시하고 성공해야 한다.
- 계정(`auth.users`) 삭제 → `public.users` 및 하위 `preference_sets`… 연쇄 삭제 확인.
