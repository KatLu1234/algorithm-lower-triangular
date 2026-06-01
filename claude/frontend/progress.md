---
doc_type: progress-log
scope: frontend
title: 프론트엔드 영역 진행 이력
purpose: 프론트엔드 영역의 기술 스택 스냅샷과 별도 지침 변경 이력
target_reader: 프론트엔드 팀원 + base 작업자 (기술 변경 시)
update_rules:
  - 사용 기술 변경 시 (프레임워크·번들러·UI 라이브러리·상태관리·스타일링 도구 도입/교체/제거)
  - 영역 한정 별도 지침 추가 시 (base 일반 규칙으로 안 풀리는 결정)
do_not_update_for:
  - 컴포넌트 추가, 스타일 손질, 화면 수정
  - 모두 git 커밋으로 충분
authoritative_for:
  - 프론트엔드 영역의 현재 기술 스택 (§1)
  - 프론트엔드 영역 한정 별도 지침 (§2)
stack_status: 1차 확정 (2026-05-21) — 라우터·다중 페이지 추가 (2026-06-01)
last_updated: 2026-06-01
---

# frontend/progress.md — 프론트엔드 영역 진행 이력

## 1. 현재 사용 기술 스택 (스냅샷)

**PURPOSE**: 영역의 권위 있는 기술 스택 상태.
**STATUS**: **1차 확정 (2026-05-21).** 시간표 생성 페이지 구현을 위해 React 기반 스택 확정. 코드는 프로젝트 루트 `frontend/` 디렉터리.

| 분류 | 선택 | 비고 |
| ---- | ---- | ---- |
| 언어 | TypeScript | 시간표/동선 데이터 구조가 복잡 → 타입 안정성 (team-guide §3 권장) |
| 프레임워크 | React 18 | |
| 번들러 / 빌드 | Vite 5 | SSR 불필요 → Vite로 충분 |
| 라우팅 | react-router-dom (다중 페이지) | 4 페이지 구조 `/login`·`/`·`/timetable`·`/courses`. 인증 가드 `<ProtectedRoute>`. 페이지 설계는 `pages/index.md` |
| 상태 관리 | React 로컬 상태 (useState) | 전역 상태가 필요해지면 재검토 |
| 스타일링 | Tailwind CSS 3 | |
| UI 컴포넌트 | 자체 컴포넌트 | 외부 UI 라이브러리 미도입 |
| API 클라이언트 | fetch + 얇은 래퍼 (`src/api/client.ts`) | 서버 `/api/v1` 호출, `{detail, code}` 에러 표준 처리 |
| 배포 | (TBD) | 정적 호스팅 예정 |

---

## 2. 별도 지침 (frontend 한정)

**PURPOSE**: `claude/base/` 일반 규칙으로 안 풀리는 프론트엔드 한정 결정 기록.

| 항목 | 결정 | 결정일 | 사유 |
| ---- | ---- | ------ | ---- |
| 다중 페이지 구조 | 4 페이지(`/login`·`/`·`/timetable`·`/courses`) 분할. 단일 페이지 데모(`frontend/docs/demo-layout.md`)를 운영형 다중 페이지로 흡수. 페이지별 설계는 `pages/<slug>.md` 한 페이지당 한 파일. 인증 가드는 `<ProtectedRoute>` 공통 셸. | 2026-06-01 | "로그인 → 메인(시간표 짜기·강의 검색 분기) + 두 기능 페이지 분리" 사용자 요청 |

---

## 3. 변경 이력

**PURPOSE**: 기술 스택 또는 별도 지침 변경의 시간 순 이력.
**RULE**: 가장 최근이 맨 위. 컴포넌트 추가·스타일 손질은 기재하지 않음.

| 날짜 | 항목 | 변경 | 사유 / 트리거 |
| ---- | ---- | ---- | ------------- |
| 2026-06-01 | 스택 추가 + 지침 추가 | `react-router-dom` 도입(다중 페이지). 4 페이지 구조(`/login`·`/`·`/timetable`·`/courses`) + 인증 가드 `<ProtectedRoute>` + 공통 셸. 페이지 설계 문서를 `claude/frontend/pages/` 한 페이지당 한 파일로 분리(`index.md`·`login.md`·`main.md`·`timetable.md`·`course-search.md`). `frontend/docs/demo-layout.md`의 단일 페이지 데모를 본 다중 페이지가 대체. §1 라우팅 행 갱신, §2 별도 지침 1행 신설. | "로그인 → 메인(시간표 짜기/강의 검색 카드) + 두 기능 페이지 분리, claude/frontend 폴더 구성" 사용자 요청 |
| 2026-05-21 | 스택 추가 | frontend 스택 1차 확정: TypeScript + React 18 + Vite 5 + Tailwind CSS 3 + fetch 래퍼. 단일 페이지(라우터 미도입), 로컬 상태. 프로젝트 루트 `frontend/` 디렉터리에 부트스트랩. `architecture.md` §2.1 frontend 행 동기화. | 시간표 생성 페이지(입력 폼 + 주간 격자) 구현 착수, 사용자 승인 |
| 2026-05-17 | 지침 추가 | `frontend/tasks.md` 신설 — 프론트엔드 영역 작업 칸반(TODO/DOING/DONE) + 카드 형식 + 영역 간 승격 기록. 스택 미확정 단계의 카드는 owner 옆 "스택 결정 후 착수" 표기 컨벤션 도입 | 팀원 작업 확인 보드 도입 |
| 2026-05-17 | 지침 추가 | `frontend/team-guide.md` 신설 — 프론트엔드 팀원의 영역 진입 문서. 스택 미정이므로 §3은 결정 시 체크리스트 형식 | 영역 팀원 온보딩 통일 |
| 2026-05-17 | 진행 파일 | `frontend/progress.md` 신설, 스택 미정 상태로 스냅샷 작성 | "각 scheme에 진행상황 파일" 지시 |

---

## 4. 변경 유형 분류

**PURPOSE**: §3 변경 이력의 "항목" 컬럼 표준화 카테고리.

| 유형 | 의미 |
| ---- | ---- |
| 스택 추가 | 새 라이브러리·도구 도입 |
| 스택 교체 | 기존 선택을 다른 것으로 변경 |
| 스택 제거 | 의존성 제거 |
| 지침 추가 | frontend 한정 규칙이 새로 굳어짐 |
| 지침 폐기 | 더 이상 적용되지 않는 규칙 제거 |
