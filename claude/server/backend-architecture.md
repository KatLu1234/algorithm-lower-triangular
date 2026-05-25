# server/backend-architecture.md — 백엔드 아키텍처 (캐싱·성능·관측성)

> **이 문서의 역할**
> [`db/`](./db/index.md) 모델을 토대로 서버(FastAPI) 백엔드의 **런타임 아키텍처**를 설계한다.
> 다루는 범위: ① 캐싱 전략 ② 성능 예산·동시성 ③ 에러·관측성. 계층 경계의 큰 틀은
> [`../base/architecture.md`](../base/architecture.md)가 권위, 본 문서는 그 위에서 *어떻게 빠르고
> 정확하고 관측 가능하게 돌릴 것인가*를 정한다.
>
> **상태: 설계안.** 실제 코드·의존성·DB 컬럼 추가는 §7 승인 항목을 거친 별도 단계다
> (`../CLAUDE.md` §4.2, `../base/architecture.md` §2.4).

---

## 1. 설계 입력 (무엇이 이 설계를 결정하는가)

- **우선순위** ([`../base/product.md`](../base/product.md) §4): `정확성 > 설명 가능성 > 중요도 충실도 >
  불가능 안내 > 검증 가능성 > 응답 속도 > 다양성 > …`. 즉 **속도는 정확성·설명보다 아래**다.
  캐싱·동시성은 정확성을 절대 깎지 않는 선에서만 속도를 산다.
- **성능 목표** (product.md §3.2): 알고리즘 산출 **≤ 50 ms** (강의 ≤ 50개, 건물 ≤ 30개),
  사용자 응답 전체 **≤ 3 초**. 지배항은 알고리즘이 아니라 **LLM 호출(~1초)** (algorithm-tree §9.7).
- **계층 경계** (architecture.md §3): `frontend → server → llm-include` 단방향. LLM 호출은
  `app/libs/llm_client.py` **한 곳**, llm-include는 읽기 전용, 에러는 `{detail, code}` (§5.1).
- **순수성 규칙** (team-guide §6): `app/libs/`의 알고리즘 함수는 부수효과 금지 → **캐싱은 libs 안이
  아니라 호출자(crud/오케스트레이션)에서** 한다. 이게 본 설계의 핵심 제약이다.
- **영속화 모델** ([`db/index.md`](./db/index.md)): 입력은 `preference_sets`(+자식), 결과는
  `solve_runs`/`scheduled_results`/`course_rationales`. DB 자체가 **내구성 캐시**의 한 축이 된다.

---

## 2. 한 solve 요청의 처리 파이프라인

`POST /api/v1/timetable/solve` (선호 설정 → 상위 N개 시간표 + 설명) 한 건의 흐름. 괄호는 캐시/영속화 지점.

```
1. endpoints/timetable.py
   └ PreferenceVector 검증 (app/schemas) ............................ <5ms
2. crud: 강의 카탈로그 로드 (term 기준 courses + course_time_slots)
   └ [CACHE A: 카탈로그] hit→메모리, miss→Supabase 1쿼리 ............ cold ~100ms / warm <10ms
3. libs: 이동시간 행렬 확보 (building_travel_times → 플로이드-워셜)
   └ [CACHE B: 이동행렬] 거의 항상 hit (정적) ....................... warm ~0ms
4. libs: A→B→C 순수 알고리즘 (FeasibilityResult→ValuationResult→SelectionResult)
   └ [CACHE C: 알고리즘 결과] 결정적 → 시그니처 hit 시 통째 재사용 ... ≤50ms
5. libs: explain=true 면 llm_context.build → llm_client.complete
   └ [CACHE D: LLM 설명] 동일 결과 시그니처면 재사용 ................. miss ~1000ms / hit <5ms
6. crud: 결과 영속화 (solve_runs + scheduled_results(+courses) + course_rationales)
   └ [영속화 = 내구성 캐시] 같은 시그니처 과거 run 조회 가능 ......... <50ms
7. 응답 직렬화 (SelectionResult → *Response 스키마)
```

정확성 불변항: hard 제약 데이터(강의 시간·이동·학점·고정/제외)는 **절대 stale로 응답하지 않는다**.
캐시 키에 콘텐츠 버전을 박아 자연히 보장한다(§3.4).

---

## 3. 캐싱 전략

### 3.1 캐시 대상 (무엇을·왜·어떻게)

| # | 대상 | 키 | 비용 | 변동성 | 계층(권장) | 무효화 |
| - | ---- | -- | ---- | ------ | ---------- | ------ |
| A | 강의 카탈로그 (term별 `courses`+`course_time_slots`, `Course`로 조립) | `term + catalog_version` | 중 (Supabase RTT + 조립) | 학기 중 거의 고정 | 프로세스 메모리 (짧은 TTL 또는 버전) | catalog_version 변경 시 |
| B | **이동시간 행렬** (플로이드-워셜 산출, `building_travel_times` 입력) | `hash(건물집합+간선집합)` 또는 `buildings_version` | 높음 O(V³) | 거의 불변(정적) | 프로세스 메모리 + (선택) `building_travel_times`에 `is_direct=false`로 영속 | 건물/거리 변경(관리 작업) 시 |
| C | 알고리즘 결과 (`SelectionResult`) | `sig = hash(정규화 PV + catalog_version + travel_version)` | 낮음 ≤50ms | 입력에 100% 종속 | DB(`solve_runs` 조회) + (선택) 메모리 LRU | 입력/버전 변경 시 자동(키가 달라짐) |
| D | **LLM 설명** | `hash(SelectionResult 페이로드 + 프롬프트 템플릿 버전)` | **높음 ~1초·과금** | 결과에 종속 | DB 또는 메모리 LRU | 결과/템플릿 버전 변경 시 자동 |
| E | llm-include 파일 내용 | `path + mtime` | 낮음(디스크 I/O) | 드묾 | 프로세스 메모리 | mtime 변경 시 재로드 |

가치 순위: **B(전 사용자 공유·O(V³)) > D(과금·1초) > A > C > E**. B와 D에 노력을 집중한다.

### 3.2 캐시 티어

- **Tier 0 — 프로세스 메모리** (지금 채택): `functools.lru_cache` 또는 모듈 dict. 신규 의존성
  없음. 현재 단일 환경(architecture.md §2.3 "개발=운영")에 충분. B·A·E는 부팅 시 워밍업.
- **Tier 1 — DB 내구성 캐시** (지금 채택): `solve_runs`/`scheduled_results`/`course_rationales`가
  이미 결과를 영속화하므로, 동일 시그니처의 과거 run을 조회하면 C·D를 통째로 건너뛴다.
  재시작·다중 워커에도 살아남는 유일한 공유 캐시.
- **Tier 2 — 공유 인메모리 캐시(Redis 등)** (미채택·향후): 다중 uvicorn 워커/인스턴스로
  스케일아웃하면 Tier 0가 워커별로 분리(콜드)된다. 그때 B·D를 워커 간 공유하려면 Redis가
  필요. **신규 외부 의존 → §7 승인 필요**. 단일 환경인 현재는 도입하지 않는다.

### 3.3 순수성과의 정합 (어디에 캐시를 두는가)

`app/libs/`의 알고리즘 함수(플로이드-워셜, A/B/C)는 **순수 함수로 유지**한다(부수효과·메모이제이션
금지, team-guide §6). 따라서:

- 캐시는 **호출자**에 둔다: 카탈로그/이동행렬 캐시는 `app/crud` 또는 얇은 오케스트레이션 헬퍼,
  결과/LLM 캐시는 라우트 직전 계층. 제안 위치는 `app/core/cache.py`(키 생성·TTL·LRU 유틸).
- 플로이드-워셜 같은 순수 함수는 입력(건물 간선)을 받아 행렬을 반환만 하고, 그 **반환값을
  호출자가 캐시**한다. "한 번 계산 후 O(1) 룩업"(algorithm-tree B-2)은 호출자 캐시로 달성한다.

### 3.4 무효화·정확성 (정확성 #1 사수)

- **콘텐츠 해시 키 우선, TTL 보조.** hard 제약에 영향을 주는 데이터(B 이동행렬, C 결과)는
  시간 기반 TTL이 아니라 **콘텐츠/버전 키**로 캔다. 입력이 바뀌면 키가 달라져 stale이 원천 차단.
- **카탈로그 버전** = `max(updated_at)` 또는 명시 `catalog_version` 카운터. A·C 키에 포함.
- **가중치 변경 = 새 결과** (product.md §4.3.3 #6 단조 반응 > 결과 안정성): 정규화 PV 해시가
  모든 가중치를 포함하므로, 사용자가 λ·중요도를 바꾸면 캐시 미스가 나고 새로 계산된다. 의도된 동작.
- **관리 작업 무효화 훅**: 건물/거리·카탈로그 갱신 시 해당 버전 키를 올리는 단일 진입점을 둔다
  (예: `cache.bump_catalog_version(term)`), 분산되면 stale 위험.

### 3.5 캐시 키 설계

- **정규화 PV 해시**: `PreferenceVector`는 `frozen=True`(불변)이라 안전. dict/set 필드는 정렬,
  float는 고정 소수로 정규화한 뒤 안정 직렬화(JSON, `sort_keys`)하여 `sha256`. 이 `sig`가 C·D의
  기준이며 `solve_runs`의 조회 키로도 쓴다(§7에서 컬럼 추가 제안).
- **개인정보 금지**: 키·로그에 `user_id`나 식별 정보를 넣지 않는다(architecture.md §5.3). 키는
  내용 해시만으로 구성.

---

## 4. 성능 예산·동시성

### 4.1 단계별 예산 (목표 합 ≤ 3초)

| 단계 | 목표 | 비고 |
| ---- | ---- | ---- |
| 입력 검증 | < 5 ms | Pydantic |
| 카탈로그 로드 | warm < 10 ms / cold ~100 ms | CACHE A |
| 이동행렬 | warm ~0 ms | CACHE B (워밍업됨) |
| 알고리즘 A→B→C | **≤ 50 ms** | product.md §3.2 강제 목표 |
| LLM 설명 | ~1000 ms (miss) / < 5 ms (hit) | 지배항. CACHE D |
| 영속화 + 직렬화 | < 50 ms | Supabase insert 묶음 |
| **합(LLM miss)** | **~1.2 초** | 3초 예산 내 여유 |

알고리즘이 50ms를 못 지키는 입력 규모면 **위조 금지**, "계산 시간 초과"를 정직히 보고
(product.md §4.2). 캐시로 가짜 응답을 만들지 않는다.

### 4.2 async 정책 + CPU 오프로딩

- **모든 라우트 `async def`** (LLM·Supabase가 IO-bound). server/progress.md §2 후보 지침과 일치.
- 알고리즘은 CPU-bound(≤50ms). 이벤트 루프를 막지 않도록 동시성이 올라가면
  **`anyio.to_thread.run_sync(solve, pv)`** 로 스레드 오프로딩한다(파이썬 GIL 한계는 있으나 50ms
  단위라 충분). 순수 함수라 스레드 안전.

### 4.3 LLM 호출 보호

- **타임아웃**: `app/core/config.py` 상수(예: 연결/응답 하드캡 8초, 목표 1초). 초과 시 §5.3 우아한 저하.
- **동시성 제한**: 세마포어로 동시 LLM 호출 수 제한(공급자 레이트리밋·비용 보호).
- **싱글플라이트(in-flight 합치기)**: 동일 `sig`의 동시 요청은 하나의 계산·LLM 호출을 공유해
  중복 과금/연산 제거. CACHE D와 결합.
- **재시도**: 멱등·짧은 백오프 1회까지. 한도·토큰은 config 상수(architecture.md §5.3).

### 4.4 Supabase 접근

- **N+1 금지**: 강의별 쿼리 ❌. term 카탈로그를 **한 번**에 읽어 메모리 조립(CACHE A). 시간슬롯은
  `course_id IN (...)` 한 쿼리로 묶어 로드.
- **클라이언트 재사용**: `app/db/supabase.py` 단일 클라이언트 유지(`api/deps.py` 주입). 매 요청
  생성 금지.
- **결과 쓰기 묶음**: `scheduled_results`·`scheduled_result_courses`·`course_rationales`는
  배치 insert.

### 4.5 워커 스케일아웃 함의

단일 워커(현재)에선 Tier 0 메모리 캐시로 충분. **워커를 늘리면** B·D 캐시가 워커별로 콜드 →
(a) 부팅 워밍업으로 B 비용 흡수, (b) D는 DB 내구성 캐시(Tier 1)로 공유, (c) 그래도 부족하면
Tier 2(Redis) 도입(§7). 이 트레이드오프를 배포 결정 시 다시 본다.

---

## 5. 에러·관측성

### 5.1 결과 분류 (무엇이 에러이고 무엇이 아닌가)

| 분류 | HTTP | 처리 | 영속화 |
| ---- | ---- | ---- | ------ |
| 정상 | 200 | `SelectionResult` 응답 | `solve_runs.status='success'` |
| **불가능(infeasible)** | **200** | `InfeasibilityReport`는 *에러가 아님* — 정상 비즈니스 결과. "어느 제약 풀면 가능"을 담아 응답 | `status='infeasible'` + 진단 컬럼 |
| 입력 검증 실패 | 422/400 | `{detail, code}` (예: `VALIDATION_CREDIT_RANGE`) | 안 함 |
| LLM 실패/타임아웃 | 200 | **우아한 저하**(§5.3): 알고리즘 결과는 그대로, 설명만 생략 | `status='success'`, 설명 없음 표시 |
| 알고리즘 시간 초과 | 200 또는 503 | 위조 금지, "계산 시간 초과" 정직 보고 | 선택 |
| 내부 오류 | 500 | `{detail, code:'INTERNAL'}`, 스택은 로그만 | 안 함 |

핵심: **infeasible은 200**(설명 가능성·불가능 안내가 제품 가치, product.md §4 #4). 검증 실패와
구분한다.

### 5.2 에러 코드 카탈로그 (`{detail, code}`)

`VALIDATION_*`(입력), `CATALOG_UNAVAILABLE`(카탈로그 로드 실패), `LLM_TIMEOUT`/`LLM_UNAVAILABLE`,
`INTERNAL`. 코드 네임스페이스를 `app/core/`에 상수로 모아 frontend가 분기 가능하게 한다
(architecture.md §5.1 `{ "detail": "...", "code": "..." }`).

### 5.3 우아한 저하 (정확성 > 설명 > 속도 그대로 적용)

LLM이 죽거나 느려도 **알고리즘적으로 정확한 시간표는 반드시 반환**한다. 설명(`explanation`)만
`null` + `notes`에 "설명 일시 생략" 표기. 정확한 결과를 설명 때문에 막지 않는다 — 우선순위 직접 반영.

### 5.4 로깅·메트릭·트레이싱 (개인정보 금지)

- **구조화 로깅**: 요청당 `correlation_id`, 단계별 ms(검증/카탈로그/알고리즘/LLM/영속화),
  캐시 hit/miss(A~E), `solve_run_id`, `status`, `sig`(해시). **PII·시크릿 로그 금지**(§5.3 규약).
- **메트릭**: 캐시 적중률(대상별), `algorithm_ms` 히스토그램(50ms SLO 감시), `total_latency`,
  `llm_latency`, infeasible 비율, `llm_timeout` 비율.
- **감사·검산**: `solve_runs.compute_ms`에 알고리즘 시간 기록, `scheduled_results`의 점수 분해
  8컬럼으로 사후 산술 검산(product.md §4.3.1). DB 모델이 이미 이를 지원한다.
- **헬스/레디니스**: `/healthz`(프로세스), `/readyz`(Supabase 연결 + CACHE B 워밍 여부).

---

## 6. 제안하는 코드 배치 (구현은 별도)

team-guide §4 책임 매핑을 따른다. 신규로 제안하는 자리만:

| 관심사 | 제안 위치 | 비고 |
| ------ | --------- | ---- |
| 캐시 유틸(키 생성·LRU·TTL·버전 훅) | `app/core/cache.py` | 순수 함수 밖. libs는 손대지 않음 |
| 타임아웃·세마포어·캐시 TTL 상수 | `app/core/config.py` | 매직넘버 금지 |
| 카탈로그 로드(+캐시) | `app/crud/catalog.py` | term 단위 배치 로드 |
| solve 오케스트레이션 | `app/api/endpoints/timetable.py` | 검증→로드→solve→LLM→영속화 위임만 |
| 관측(미들웨어·correlation id) | `app/core/` 미들웨어 | 구조화 로깅 |

순수 알고리즘(`app/libs/floyd_warshall.py`, `timetable.py` 등)과 LLM 단일 진입점
(`app/libs/llm_client.py`)의 시그니처는 본 설계로 바뀌지 않는다.

---

## 7. 도입 시 승인 필요 항목

- **신규 의존성**: Tier 2 공유 캐시(Redis)·관측 라이브러리(예: structlog/OpenTelemetry)는
  `requirements.txt` 추가 전 사용자 승인(`../CLAUDE.md` §4.2, architecture.md §2.4).
- **DB 컬럼 추가(선택)**: `solve_runs`에 `request_signature text`(C·D 캐시 조회 키),
  `llm_ms numeric`(LLM 시간) 추가를 제안. 추가 시 [`db/solve_runs.md`](./db/solve_runs.md)와
  안전 순서(옵셔널 우선, base/CLAUDE.md §3.2) 동기화.
- **신규 엔드포인트 계약**: `/api/v1/timetable/solve`, `/healthz`, `/readyz`는 frontend 계약 → base 변경
  (base/CLAUDE.md §1) 승인 대상.

## 8. 미해결 / 다음 단계

1. uvicorn 워커 수·배포 형태 확정(4.5의 캐시 티어 결정에 직결).
2. LLM 공급자·SDK 확정(타임아웃·재시도·토큰 상수의 실제 값).
3. catalog_version 메커니즘 선택(`max(updated_at)` vs 명시 카운터).
4. 관측 스택 선택(표준 logging vs structlog/OTel) — §7 승인.
5. 본 결정이 굳으면 server 한정 지침으로 [`./progress.md`](./progress.md) §2(별도 지침)·§3(이력) 갱신.
