# base/progress.md — 베이스 문서 변경 이력

> **갱신 규칙 (반드시 지킬 것)**
> `claude/base/` 내 **어떤 문서가 바뀌든** 이 파일에 한 줄을 추가한다.
> 오타 수정·줄바꿈 정리도 포함한다(다만 "외형 수정"이라고 분류해 묶어도 됨).
> Claude가 base 문서를 편집할 때마다 같은 응답 안에서 본 파일도 함께 갱신한다 — 잊으면 안 된다.

## 1. 현재 베이스라인 (스냅샷)

마지막으로 정리된 시점의 base 문서 구성입니다. 새 문서가 추가/제거되면 이 표를 업데이트하세요.

| 파일 | 역할 | 최신 갱신일 |
| ---- | ---- | ----------- |
| `CLAUDE.md` | base 레벨 Claude 작업 지침 (인덱스 + 절차 + progress 규칙) | 2026-05-17 |
| `architecture.md` | 계층 조합 설계 + **기술 스택** + 인터페이스 규약 | 2026-05-21 |
| `product.md` | 제품 목적성·기대 효과·우선순위 (시간표 추천 균형 모델로 초기 입력 완료) | 2026-05-17 |
| `user-experience.md` | 유저가 기대할 수 있는 경험 (빈 템플릿) | 2026-05-17 |
| `tasks.md` | 전체 작업 칸반 인덱스 + 영역 진행 요약 + 교차 영역 카드 | 2026-05-19 |
| `progress.md` | (현재 파일) base 문서 변경 이력 | 2026-05-19 |
| `structure-overview.md` | 프로젝트 현재 계획의 한 장 구조도 (SVG 임베드 + 그림 읽는 법 + 위치 매핑 + 갱신 규칙) | 2026-05-19 |
| `drafts/` | 임시 저장 영역 — 승인 전 초안 보관. 코드 결정 근거로 인용 금지. | 2026-05-17 |
| `drafts/algorithm-tree.md` | 알고리즘 분해 트리 — 시간표 도메인 §9 확정 (locked). 건물 슬롯 단위(TimeSlot.building) 수정 반영. A-1 blackout 슬롯 단위 제거(any) 반영. §1~§8 LT-as-DAG 자료는 폐기 대기 | 2026-05-25 |

## 2. 변경 이력

가장 최근 변경이 맨 위. 한 줄에 하나의 변경을 적되, 같은 응답에서 동시 변경된 항목은 묶어도 된다.

| 날짜 | 파일 | 변경 유형 | 요약 | 사유 / 트리거 |
| ---- | ---- | --------- | ---- | ------------- |
| 2026-05-25 | `app/libs/feasibility.py` (+ `app/schemas/preferences.py`, `drafts/algorithm-tree.md`) | 동작 변경 (A-1) | **blackout 제거 판정을 강의 단위 `all()` → 슬롯 단위 `any()` 로 변경.** 기존 `_fully_blacked_out`(강의의 *모든* 슬롯이 blackout에 걸려야 제외)은 월·수·금 같은 다요일 강의의 blackout 슬롯(금요일 회차)이 시간표에 새어 들어오는 버그가 있었다. `_any_slot_blacked_out`(걸친 슬롯이 *하나라도* 있으면 강의 통째 제외)로 교체 — 강의는 슬롯을 쪼개 들을 수 없다는 도메인 사실 반영. 필수 강의가 blackout과 충돌하면 기존 `MUST_INCLUDE_BLACKOUT_CONFLICT` infeasible 경로로 처리(하류 변경 불필요). preferences.py `blackout_windows` 설명·algorithm-tree.md §A-1 명세 동기화. AST 통과 + pydantic-free mock으로 월수금+금요일 blackout 제거 확인, 기존 conftest 화요일(00:00~09:00) 픽스처 무영향 확인(런타임 전체 검증은 Windows 환경 필요). | "금요일 blackout인데 금요일에 수업이 잡힘 — 하드 방식(권장)으로 슬롯 단위 강제" 지시 |
| 2026-05-24 | `drafts/algorithm-tree.md` (+ `app/schemas/common.py`, `app/libs/feasibility.py`, `app/libs/valuation.py`, `claude/server/db/{course_time_slots,courses,index}.md`, `tests/conftest.py`, `tests/test_schemas.py`) | 스키마·명세·DB 갱신 | **건물을 슬롯 단위로 이동.** `TimeSlot.building` 필드 신설, `Course.building`은 `@computed_field` 대표 건물(최빈, 동률 시 첫 등장) 파생값으로 변경. A-2 충돌 검사가 강의 대표 건물이 아니라 **슬롯별 건물**로 이동시간 계산(한 강의가 요일마다 다른 건물 가능 — 예: 월 과기1관/화 농심국제관). v(c) 건물 페널티는 강의가 쓰는 **distinct 건물 가중치 합**, 다양성 페널티는 전 슬롯 건물 집합 기준. DB: `course_time_slots`에 `building_code`(NOT NULL, FK→buildings, +인덱스) 추가, `courses.building_code`는 nullable 대표건물(denormalized)로 완화, `index.md` §3 관계도·§4 설계결정 동기화. `algorithm-tree.md` §9.2(A-2)·§9.3(B-1·B-2)·그룹 자료에 슬롯 단위 건물 명시. 픽스처에 다건물 강의(GSFC038) 추가. py_compile 통과 + pydantic-free mock으로 distinct 합·대표 최빈·슬롯 이동충돌 로직 검증 통과(런타임 전체 검증은 Windows 환경 필요). | "각 시간마다 다른 건물을 사용하는 과목 대응 — TimeSlot.building 방식으로 플랜 변경" 지시 |
| 2026-05-21 | `architecture.md` | 갱신 | §2.1 frontend 행 5개를 확정 스택으로 동기화: 언어 TypeScript · 프레임워크 React 18 · 빌드 Vite 5 · 스타일링 Tailwind CSS 3 · API 클라이언트 fetch 래퍼. 권위 출처는 `frontend/progress.md` §1(같은 응답에서 §1·§3 함께 갱신); 본 표는 청사진 동기화. | 프론트 스택 1차 확정 — 시간표 생성 페이지(입력 폼 + 주간 격자) 구현 착수, 사용자 승인 |
| 2026-05-19 | `app/schemas/common.py`, `app/schemas/preferences.py`, `app/schemas/selection.py`, `app/schemas/__init__.py`, `drafts/algorithm-tree.md` | 스키마 확장 + 명세 갱신 | **분반·교수 차원 추가** (안전 순서 step 1). Course에 옵셔널 3개 필드(`course_group_id`·`section`·`professor`) + 같은 group_id 분반은 상호 배타. PreferenceVector에 옵셔널 3개(`must_include_groups`·`exclude_groups`·`professor_preferences`) + `professor_weight()`·`courses_in_group()` 헬퍼 + 중복 ID 검사 + 그룹 정합성 검사. `InfeasibilityReason`에 `MUST_INCLUDE_GROUP_EMPTY`·`GROUP_PAIR_CONFLICT` 추가. `InfeasibilityReport.offending_group_ids` 필드 추가. `StageCode`에 `A1_GROUP_EXCLUDED`·`A2_GROUP_DUPLICATE`·`B3_GROUP_LOSER` 추가. v(c) 식에 교수 가중치 항 추가. drafts/algorithm-tree.md §9.2~§9.4 명세를 그룹 처리 반영해 갱신 (A-2 그룹 양립 불가, B-3 그룹 유일성 제약, C-3 새 사유 코드). | "교수가 다른 경우 시간이 다른 두 개의 같은 과목 처리" 지시 |
| 2026-05-19 | `app/schemas/common.py`, `app/schemas/preferences.py`, `app/schemas/__init__.py` | 스키마 확장 | **Requirement 직교 차원 추가** (base/CLAUDE.md §3.2 안전 순서 step 1). `Requirement` enum 신설(REQUIRED·ELECTIVE·OPTIONAL) · `Course.requirement: Optional[Requirement] = None` 옵셔널 필드 추가 · `PreferenceVector.requirement_weights: dict[Requirement, float]` 옵셔널 필드 + `requirement_weight()` 헬퍼 추가 · `__init__.py`에 Requirement 노출. 기존 데이터·호출 100% 호환 (모두 옵셔널). 전공 필수 vs 전공 선택 같은 세분화를 Category와 직교 차원으로 표현 가능. 라우트·프론트엔드 변경은 향후 안전 순서 step 2~3으로 진행. | "전공 필수/선택/교양 구분 기능 — 옵션 (다) 직교 차원으로 확장" 지시 |
| 2026-05-19 | `structure-overview.md` | 신규 | 프로젝트 현재 계획의 한 장 구조도 신설. SVG 임베드(viewBox 1000×670) + 4패널(좌상 기준결정·우상 알고리즘트리 ✓확정·좌하 구현·우하 영역+TBD) + 상태기호 4종 범례 + 그림 읽는 법 + 위치 매핑 표 + 갱신 규칙. algorithm-tree.md §9 확정 처리 직후 상태 반영. | "구조도 만들어 base에 저장" 지시 |
| 2026-05-19 | `tasks.md` | 갱신 | §4 영역별 진행 요약 표에서 `llm-include` TODO `0 → 1` 동기화. `llm-include/tasks.md` §2 TODO에 `[I-01] Upstage Solar API 조사 및 도메인 자료 작성` 카드 추가에 따른 보드 카운트 갱신. | 사용자 지시: "Upstage Solar API 조사·사용법을 AI로 `claude/llm-include`에 Claude 읽기 좋은 형태로 상세 작성하는 할 일 지정" |
| 2026-05-17 | `drafts/algorithm-tree.md` | 확정 | **§9 확정 처리** — "초안 (반영률 ~60%)" → "확정 (locked)"로 승격. 파일 헤더에 [DRAFT] 태그 제거 및 timetable 방향 확정 명시. §5 LT-as-DAG 예시는 폐기 대기로 표시. §9.9 변동성 표 → 확정·변동 분리표(확정 8 + 구현 시 결정 4). §9.10 합의 항목 4건 해소(✓) + 다음 단계 4건(⏳). 본 파일은 `architecture.md` §4.1 흡수까지만 유지 후 폐기 예정. | "draft 확정" 지시 |
| 2026-05-17 | (영역 9개 문서) `server/{team-guide,tasks,progress}.md`, `frontend/{team-guide,tasks,progress}.md`, `llm-include/{team-guide,tasks,progress}.md` | 형식 변경 | Gemini-친화 형식으로 일괄 변환 — 각 파일 상단 YAML front matter(`doc_type`·`scope`·`purpose`·`target_reader`·`authoritative_for`·`not_authoritative_for`·`priority_reading_order`·`related_docs`·`last_updated`) + 각 절 시작에 PURPOSE/INPUT/OUTPUT/CONSTRAINTS 명시 라벨. 본문 내용·규칙·표는 모두 보존. `claude/base/` 내부 문서와 최상위 `claude/CLAUDE.md`는 변경 대상 외. 향후 새 영역 문서는 본 형식을 따른다. | "base 제외 스키마 md 파일을 Gemini 읽기 쉬운 형태로" 지시 |
| 2026-05-17 | `product.md` | 갱신 | 빈 템플릿 → 전 항목 초기 입력. §1 한 줄 요약(균형 모델: 국민대 학생 대상 시간표 추천 + 알고리즘 단위 설명). §2 목적성(풀려는 문제, 존재 이유, 비-목적 7개). §3 기대 효과(정성 + 정량 지표 5개). §4 우선순위 10개(정확성→설명가능성→중요도충실도→...→결과안정성) + §4.1 근거 + §4.2 예외 4개 + §4.3 세부 우선순위(정확성·설명가능성·중요도 충실도 내부 구조) + §4.4 LLM 역할 분담(시스템 불변항). §5 범위(포함 기능 + 보류 항목). | 사용자 "이 계획대로 설정" 지시, 명시한 작업 순서의 1단계(목적성). |
| 2026-05-17 | `drafts/algorithm-tree.md` | 갱신 | §9 "시간표 도메인 상세 트리 초안 (반영률 ~60%)" 추가. 옵션 1 책임 기반 3분할(A 가능성·B 가치·C 선택) + 각 자식 9개 분해 + 알고리즘 매핑 표 + 노드 간 계약 잠정안(FeasibilityResult/ValuationResult/SelectionResult) + 복잡도 요약(T = O(V³+N²+N·C+Ñ²·L²), 약 11k 연산/1ms) + Infeasibility 조기 종료 경로 + 변동성 표(부분별 반영 가능성). 기존 §1~§8(LT-as-DAG 방향)은 유지. | "이 계획 임시 저장, 반영률 60%" 지시 |
| 2026-05-17 | `drafts/`, `drafts/algorithm-tree.md` | 신규 | 임시 저장 영역(`drafts/`) 신설 + 첫 초안 문서로 "알고리즘 분해 트리" 아이디어 저장. 본 영역 문서는 공식 base 문서가 아니며 코드 결정의 근거로 인용 금지(합의 후 `architecture.md` 등에 흡수 또는 폐기). | "아이디어를 임시 저장 영역에 저장" 지시 |
| 2026-05-17 | `tasks.md` | 신규 | 전체 작업 칸반 인덱스(TODO/DOING/DONE) + 영역 진행 요약 + 운영 규칙 + 영역 ↔ 본 파일 분담 정의 | "팀원에게 주어진 작업 확인" 지시 |
| 2026-05-17 | `CLAUDE.md` | 갱신 | 비교 표에 `tasks.md` 행 추가, §8 빠른 참조에 작업 확인·교차 영역 카드 등록 행 추가 | `tasks.md` 신설 |
| 2026-05-17 | `architecture.md` | 갱신 | §6 디렉터리 트리에 각 영역의 `tasks.md` 추가(base 포함 4개) | `tasks.md` 4종 신설 반영 |
| 2026-05-17 | `architecture.md` | 갱신 | §6 디렉터리 트리에 각 영역의 `team-guide.md` 추가 | 영역별 진입 문서 신설(상위 `claude/CLAUDE.md`와 영역 `team-guide.md` 참고) |
| 2026-05-17 | `CLAUDE.md` | 갱신 | §8 빠른 참조에 "팀원이 처음 영역 진입" 행 추가 | `team-guide.md` 관습 도입 |
| 2026-05-17 | `architecture.md` | 갱신 | §2 기술 스택 신설(계층별 스택·통신 기술·환경·도입 절차 4개 소절), 기존 §2~§6 → §3~§7 재번호, §6 디렉터리 트리에 base 4개 파일·영역별 `progress.md` 반영 | "아키텍처 부분에 기술스택 부분도 추가" 지시 |
| 2026-05-17 | `CLAUDE.md` | 갱신 | §2 체크리스트의 architecture 참조를 신규 §2/§5/§6으로 갱신, 비교 표에 architecture.md 행을 "계층 조합 + 기술 스택"으로 명확화 | `architecture.md` §2 신설 반영 |
| 2026-05-17 | `CLAUDE.md` | 갱신 | §5 progress 갱신 규칙 신설, 기존 §5/§6/§7 → §6/§7/§8 재번호, §4 보고 양식에 5번째 항목(progress 상태) 추가, §7 금지/§8 빠른참조에 progress 관련 항목 추가, 인덱스에 `progress.md` 포함 | `progress.md` 4종 신설에 따른 정합성 유지 |
| 2026-05-17 | `progress.md` | 신규 | base 문서 변경 이력 파일 신설 (현재 파일) | "진행상황도 문서화" 지시 |
| 2026-05-17 | `product.md` | 신규 | 제품 우선순위·목적·기대 효과 빈 템플릿 생성 | 의사결정 기준 문서화 |
| 2026-05-17 | `user-experience.md` | 신규 | 유저 경험 빈 템플릿 생성 | UX 결정 기준 문서화 |
| 2026-05-17 | `CLAUDE.md` | 갱신 | 비교 표·문서 우선순위·§5 두 파일 활용 규칙·§6 금지사항·§7 빠른참조 추가 | `product.md` / `user-experience.md` 신설 반영 |
| 2026-05-17 | `architecture.md` | 신규 | `frontend → server → llm-include` 조합 설계, 데이터 흐름, 인터페이스 규약 정의 | base 폴더 신설 |
| 2026-05-17 | `CLAUDE.md` | 신규 | base 레벨 Claude 작업 지침 (계층 변경 분류·절차·금지사항) | base 폴더 신설 |
| 2026-05-17 | `base/` | 신규 | `claude/base.md`(빈 파일) 삭제 → `claude/base/` 폴더로 대체 | 베이스 영역을 폴더 단위로 확장하기 위함 |

## 3. 변경 유형 분류 (선택)

| 유형 | 의미 | 예 |
| ---- | ---- | -- |
| 신규 | 새 파일 / 새 섹션 추가 | `product.md` 신설 |
| 갱신 | 본문 내용 추가·수정 | `CLAUDE.md`에 §5 추가 |
| 정정 | 오타·문장 다듬기 (의미 불변) | `architecture.md` 오탈자 |
| 외형 | 줄바꿈·표 정렬 등 외형만 | 표 컬럼 너비 정리 |
| 폐기 | 파일·섹션 제거 | `base.md`(빈 파일) 삭제 |
| 이동 | 위치 변경 | (해당 시) |
