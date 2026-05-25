# DB 스키마 설계 — 인덱스

> **이 폴더의 역할**
> 시간표 추천 도메인의 DB(Supabase/Postgres) 구조를 **테이블 1개당 파일 1개**로 설계한 문서다.
> 각 파일에 컬럼·타입·제약·PK/FK·인덱스·`CREATE TABLE` DDL이 상세히 적혀 있다.
>
> **상태: 설계안.** 실제 적용은 각 문서의 DDL을 Supabase에서 실행하는 별도 단계다
> (`../../CLAUDE.md` §4.2 — DB 스키마는 자체 진행하지 않고 제안/문서로 둔다).

---

## 1. 출처

- 알고리즘 입출력 계약: `app/schemas/` (`PreferenceVector`, `FeasibilityResult`,
  `ValuationResult`, `SelectionResult`, 공유 타입 `common.py`)
- 알고리즘 트리: `claude/base/drafts/algorithm-tree.md` §9 (A 가능성 → B 가치 → C 선택)
- 우선순위 근거: `claude/base/product.md` §4 (정확성·설명 가능성·검산 가능성)

**enum은 새로 정의하지 않고 스키마와 같은 값을 재사용한다** (중복 정의 금지):

| enum | 출처 | 사용 테이블 |
| ---- | ---- | ----------- |
| `Weekday` | `app/schemas/common.py` | course_time_slots.day, blackout_windows.days |
| `Category` | `app/schemas/common.py` | courses.category |
| `Requirement` | `app/schemas/common.py` | courses.requirement |
| `InfeasibilityReason` | `app/schemas/common.py` | solve_runs.infeasibility_reason |
| `RationaleStatus` | `app/schemas/selection.py` | course_rationales.status |
| `StageCode` | `app/schemas/selection.py` | course_rationales.stage_code |

DB 전용 enum(스키마에 대응 없음): `selection_flag`(preference_courses),
`constraint_type`(preference_groups), `status`(solve_runs).

## 2. 테이블 목록 (13개)

### 참조 데이터 — 강의 카탈로그

| 테이블 | 문서 | 역할 |
| ------ | ---- | ---- |
| `buildings` | [buildings.md](./buildings.md) | 캠퍼스 건물 마스터 |
| `building_travel_times` | [building_travel_times.md](./building_travel_times.md) | 건물 간 도보 분 (B-2 플로이드-워셜 입력) |
| `courses` | [courses.md](./courses.md) | 강의 = 분반 단위 |
| `course_time_slots` | [course_time_slots.md](./course_time_slots.md) | 강의의 요일·시간 (Course.times 정규화) |

### 요청·선호 — PreferenceVector 영속화

| 테이블 | 문서 | 역할 |
| ------ | ---- | ---- |
| `users` | [users.md](./users.md) | 학생 = 선호 설정 소유자 |
| `preference_sets` | [preference_sets.md](./preference_sets.md) | 학점 한도 + 쉬는시간(min_break) + 후처리 λ + JSONB 가중치 |
| `preference_courses` | [preference_courses.md](./preference_courses.md) | 후보풀 + 중요도 + must/exclude 플래그 |
| `preference_groups` | [preference_groups.md](./preference_groups.md) | 과목 그룹 단위 제약 |
| `blackout_windows` | [blackout_windows.md](./blackout_windows.md) | 절대 불가 시간대 |

### 실행 결과 — ValuationResult / SelectionResult 영속화

| 테이블 | 문서 | 역할 |
| ------ | ---- | ---- |
| `solve_runs` | [solve_runs.md](./solve_runs.md) | 실행 헤더·통계·불가능 진단 |
| `scheduled_results` | [scheduled_results.md](./scheduled_results.md) | 순위 시간표 + 점수 분해 8항 |
| `scheduled_result_courses` | [scheduled_result_courses.md](./scheduled_result_courses.md) | 순위 시간표의 구성 강의 |
| `course_rationales` | [course_rationales.md](./course_rationales.md) | C-3 강의별 사유 색인 |

## 3. 관계 / 생성·삭제 순서

FK 의존 방향(부모 → 자식). 생성은 위에서 아래로, 삭제는 역순(또는 ON DELETE CASCADE 활용).

```
buildings
 ├─ building_travel_times   (from_code, to_code → buildings.code)
 └─ courses                 (building_code → buildings.code, 대표 건물·옵셔널)
     └─ course_time_slots   (course_id → courses.id, building_code → buildings.code)

users
 └─ preference_sets                 (user_id → users.id)
     ├─ preference_courses          (preference_set_id → preference_sets.id, course_id → courses.id)
     ├─ preference_groups           (preference_set_id → preference_sets.id)
     ├─ blackout_windows            (preference_set_id → preference_sets.id)
     └─ solve_runs                  (preference_set_id → preference_sets.id)
         ├─ scheduled_results       (solve_run_id → solve_runs.id)
         │   └─ scheduled_result_courses (scheduled_result_id → scheduled_results.id, course_id → courses.id)
         └─ course_rationales       (solve_run_id → solve_runs.id, course_id → courses.id)
```

## 4. 설계 결정 요약

- **정규화 vs JSONB**: 리스트 필드(강의 시간, 후보풀, blackout, 순위 시간표 강의)는 자식
  테이블로 정규화. 키 집합이 가변적인 가중치 dict(`category_weights` 등)는 JSONB로 보관.
- **건물은 슬롯 단위**: 강의 위치의 권위 출처는 `course_time_slots.building_code`다(슬롯마다
  다른 건물 가능 — 이동 시간 정확도의 핵심). `courses.building_code`는 표시·필터용 대표
  건물(옵셔널·denormalized). `TimeSlot.building` 스키마 변경과 1:1 대응.
- **점수 분해는 명시 컬럼**: `scheduled_results` 의 `ScoreBreakdown` 8항을 JSONB가 아닌
  컬럼으로 풀어, 항별 검산·SQL 집계가 가능하게 함 (`product.md` §4.3.1·§4.3.2).
- **enum 재사용**: 도메인 enum은 `app/schemas/` 한 곳에서만 정의하고 DB는 같은 문자열 값을
  CHECK 제약으로 강제 (§1 표).
- **PK 타입**: 자연키가 있는 참조 데이터는 text PK(`courses.id`, `buildings.code`), 사용자
  생성 데이터는 `uuid DEFAULT gen_random_uuid()`, 단순 링크/슬롯은 `bigint identity`.
- **삭제 전파**: 부모 삭제 시 자식 정리를 위해 대부분 ON DELETE CASCADE. 단,
  `courses.building_code → buildings.code` 는 RESTRICT(카탈로그 보호).

## 5. 적용 방법 (참고)

각 테이블 문서의 DDL을 §3 순서대로 모아 Supabase SQL 에디터에서 실행한다.
실제 적용 전 `../../CLAUDE.md` §4.2에 따라 사용자 확인을 받는다.
```
