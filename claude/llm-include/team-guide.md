---
doc_type: team-guide
scope: llm-include
title: LLM 자료 영역 진입 문서
purpose: LLM 자료 영역(프롬프트·few-shot·도메인 자료) 팀원이 작업 전 가장 먼저 읽는 큰 틀 문서
target_reader: LLM 자료 담당 팀원 (프롬프트·few-shot·도메인 자료 작성·검증)
data_only_policy: 본 폴더는 데이터·텍스트만. .py 코드 금지.
authoritative_for:
  - LLM 자료 영역의 책임 범위와 비-책임
  - 자료 유형별 위치 매핑 (prompts·examples·domain)
  - Claude 사용 프롬프트 패턴 (자료 작성·검증)
  - 새 LLM 기능 사이클 (서버 팀과의 task 합의 포함)
not_authoritative_for:
  - 현재 자료 형식·템플릿 엔진 스냅샷 → ./progress.md §1
  - 영역 내 작업 카드 → ./tasks.md
  - 영역 경계·server ↔ llm-include 계약 → ../base/architecture.md
priority_reading_order:
  - ../CLAUDE.md
  - ../base/product.md (§2 + §4)
  - ../base/user-experience.md (§3.2 핵심 약속)
  - ../base/architecture.md (§2 + §5.2)
  - ./progress.md (§1 스냅샷)
  - ./tasks.md
  - 본 문서 §4 이하
related_docs:
  - { path: ../base/CLAUDE.md, why: 작업 절차·LLM 호출 추가 5단계 (§3.3) }
  - { path: ../base/architecture.md, why: 본 영역 책임과 server ↔ llm-include 계약 (§3.3, §5.2) }
  - { path: ../base/user-experience.md, why: LLM 응답 톤·약속의 기준 (§3.1, §3.2) }
  - { path: ../base/product.md, why: LLM이 풀어야 할 문제와 우선순위 }
  - { path: ./progress.md, why: 자료 영역의 기술·메타 표준 현황 }
  - { path: ./tasks.md, why: LLM 자료 영역 작업 카드 }
  - { path: ../base/tasks.md, why: 전체 작업 인덱스·교차 영역 카드 }
last_updated: 2026-05-17
---

# llm-include/team-guide.md — LLM 자료 담당 팀원을 위한 진입 문서

## 1. 이 영역이 책임지는 것

**PURPOSE**: LLM 자료 영역의 단일 책임 정의.
**OUTPUT**: "이 자료가 여기 와야 하는가?"의 빠른 판단 기준.

`claude/llm-include/`는 LLM에게 **컨텍스트로 들어가는 모든 자료**의 저장소입니다.

**책임**
1. **프롬프트 템플릿** — 시스템 프롬프트·유저 프롬프트의 베이스.
2. **Few-shot 예시** — 작업별로 LLM이 흉내 낼 입출력 케이스.
3. **도메인 자료** — 시간표 최적화·알고리즘·캠퍼스 동선 같은 LLM이 참고할 배경 지식.

**비-책임 (여기서 하지 않음)**
- 실제 LLM 호출 ❌ (서버 `app/libs/llm_client.py`만 호출)
- 프롬프트 조립(템플릿 + payload 합치기) ❌ (서버 `app/libs/llm_context.py`가 함)
- `.py` 코드 ❌ — 이 폴더는 **데이터·텍스트만**.
- 시크릿·개인정보 ❌.

계층 책임: `../base/architecture.md` §3.3.

---

## 2. 시작 전 읽기 (3분 코스)

**PURPOSE**: 새 작업 시작 전 머리에 박아야 할 컨텍스트.

1. `../CLAUDE.md` — 프로젝트 전반 관습.
2. `../base/product.md` §2 목적성 + §4 우선순위 — LLM이 무엇을 도와주는 게 가장 중요한지 파악.
3. `../base/user-experience.md` §3.2 핵심 약속 — LLM 응답의 톤·길이 기준.
4. `../base/architecture.md` §2 기술 스택 + §5.2 server ↔ llm-include 계약.
5. `./progress.md` §1 — 현재 자료 영역의 권위 있는 스냅샷(자료 형식·템플릿 엔진·메타 표준).
6. `./tasks.md` — 자기에게 주어진 카드 확인.
7. 본 문서 §4 이하.

---

## 3. 다루는 기술

**PURPOSE**: 본 영역에서 사용되는 기술의 빠른 참조.
**AUTHORITATIVE**: 아님. 권위 있는 출처는 `./progress.md` §1.

- **자료 파일 형식**: `.md` / `.txt` / `.json` (선택은 TBD — 프롬프트와 few-shot의 형식이 다를 수 있음).
- **템플릿 엔진**: Jinja2 또는 `str.format` 중 하나 (TBD). 서버 `app/libs/llm_context.py`와 짝.
- **메타 헤더 표준**: YAML front-matter 등 (TBD). 자료마다 `목적·기대 사용처·마지막 수정일`을 단다.
- **LLM 공급자 / 모델**: TBD. 서버 `app/libs/llm_client.py` 결정과 동일 시점.
- **디렉터리 구조**:
  - `prompts/` — 시스템·유저 프롬프트 템플릿 (`<task>.md` 형태)
  - `examples/<task>/` — `case-01.json`, `case-02.json` 식의 few-shot 케이스
  - `domain/` — 알고리즘·문제 정의서·용어집 등 배경 지식

**스택 변경 절차**: `../base/architecture.md` §2.4 → `./progress.md` §1/§3 갱신.

---

## 4. 책임 매핑 (작업 유형별 위치)

**PURPOSE**: 자료 작업이 어느 폴더로 가야 하는지의 룩업 표.

| 작업 유형 | 위치 | 한 줄 규칙 |
| --------- | ---- | ---------- |
| 새 작업용 프롬프트 | `prompts/<task>.md` | 상단 메타 헤더 필수. 변수 자리는 템플릿 엔진 표기. |
| Few-shot 케이스 추가 | `examples/<task>/case-NN.json` | 입력·기대 출력 쌍. 케이스를 의도적으로 분산. |
| 도메인 자료 | `domain/<주제>.md` | LLM 읽기 좋은 길이로 분할. 정의/규칙/예시 순. |
| 메타 헤더 표준 변경 | (별도 지침 추가) | `progress.md` §1·§2 동시 갱신. |
| 토큰·길이 제한 변경 | (별도 지침 추가) | `progress.md` §2에 결정과 사유 기록. |

**전형적 새 LLM 기능 사이클**:
`서버 팀과 task 이름·payload 형태 합의 → prompts/<task>.md 작성 → examples/<task>/case-01.json 최소 1개 → 서버 llm_context.py 빌더에서 읽도록 연결 → 응답 품질 확인 → 케이스 추가하며 다듬기`.

서버 측 단계는 `../base/CLAUDE.md` §3.3에 상세.

---

## 5. Claude 사용 패턴

**PURPOSE**: 자료 영역에서 Claude를 두 종류로 사용.
**USAGE_MODES**:
- (a) **자료를 만드는 보조** — 프롬프트·few-shot·도메인 자료의 초안 작성.
- (b) **자료를 검증하는 평가자** — 프롬프트 토큰 추정, few-shot 품질 점검, 모호한 표현 찾기.

### 5.1 새 프롬프트 템플릿 초안

```
컨텍스트: claude/llm-include/team-guide.md, claude/base/product.md §2·§4
작업: 시간표 최적화 결과를 사람에게 설명하는 시스템 프롬프트를 작성해줘.
대상 task 이름: explain_schedule
입력 페이로드: <필드 설명>
원하는 응답 톤: user-experience.md §3.1 인용 ("정돈된, 신뢰감 있는" 등)
길이: <문장 수 / 토큰 상한>
변수 자리: progress.md §1의 템플릿 엔진 표기 그대로.
상단 메타 헤더 포함: 목적·기대 사용처·마지막 수정일.
```

### 5.2 Few-shot 케이스 작성

```
컨텍스트: claude/llm-include/prompts/<task>.md (현재 템플릿)
작업: 다음 3가지 시나리오에 대한 case-*.json을 작성해줘.
- 케이스 A: <대표 입력>
- 케이스 B: <엣지 케이스>
- 케이스 C: <오해하기 쉬운 입력>
각 케이스의 기대 출력은 user-experience.md §3.2 약속을 만족해야 해.
```

### 5.3 자료 검증·정리

```
컨텍스트: claude/llm-include/<파일들>
작업: 다음 항목을 점검해줘.
1. 토큰 길이 추정 (대략 단어 수 기준)
2. 모호한 표현·중복 문장
3. user-experience.md §3 톤과 어긋나는 부분
4. 시크릿·개인정보가 섞여 있지 않은지
수정은 내 승인 후에.
```

### 5.4 도메인 자료 요약·재구성

```
컨텍스트: <도메인 자료 초안>
작업: LLM이 컨텍스트로 받기 좋게 재구성해줘. 형식: 정의 → 규칙 → 예시 → 자주 틀리는 점.
길이 상한: <토큰 또는 줄 수>.
```

### 5.5 Claude에게 시키지 말 것

- 이 폴더에 `.py` 파일 만들기 ❌
- 메타 헤더 없이 새 자료 추가 ❌
- 실제 LLM 호출 또는 키 사용 ❌ (이 영역은 자료만 다룸)
- `user-experience.md`에 없는 응답 톤을 본인 취향으로 도입 ❌

---

## 6. 지켜야 할 지침 (요약)

**PURPOSE**: 자주 부딪히는 규칙의 빠른 참조.

- **데이터-온리**: 이 폴더는 텍스트·JSON·MD만. `.py` 금지. (`../base/architecture.md` §3.3)
- **서버 경유**: 서버는 이 폴더를 **읽기 전용**으로 사용. 본인이 import 가능한 코드를 두면 단방향 의존이 깨짐.
- **메타 헤더**: 모든 자료 상단에 `목적 / 기대 사용처 / 마지막 수정일` 표기.
- **톤**: 응답 톤·약속은 `../base/user-experience.md` §3.1, §3.2. 본인 취향으로 톤 바꾸기 금지.
- **시크릿**: 키·토큰·개인정보·실제 사용자 데이터 포함 ❌. 예시는 가공된 더미 데이터로.
- **트레이드오프**: `../base/product.md` §4 우선순위로 결정. 결정 근거는 PR/응답에 인용.
- **progress 갱신**: 자료 영역은 **자료 형식·템플릿 엔진·메타 표준·공급자 변경 또는 별도 지침 추가 시에만** `./progress.md` 갱신. 프롬프트 문구 다듬기·case 1건 추가는 기록 안 함. (`../base/CLAUDE.md` §5.2)

---

## 7. 빠른 참조표 (상황 → 문서)

**PURPOSE**: 자주 발생하는 상황에 대한 진입점 룩업.

| 상황 | 어디 보러 가나 |
| ---- | -------------- |
| 새 LLM 기능(task) 추가 | `../base/CLAUDE.md` §3.3 5단계 + 본 문서 §5.1 |
| Few-shot 케이스 추가 | 본 문서 §5.2 프롬프트 |
| 자료 형식·메타 표준 변경 | `../base/architecture.md` §2.4 절차 |
| 서버 측 빌더 연결 방식 | `../base/architecture.md` §5.2 |
| 응답 톤이 헷갈림 | `../base/user-experience.md` §3.1·§3.2 |
| LLM 공급자 결정 | 서버 `../server/progress.md`와 동일 시점에 `./progress.md` 갱신 |
| 무엇이 base 변경인가 헷갈림 | `../base/CLAUDE.md` §1 분류 기준 |
| 내 작업이 뭔지 모르겠음 | `./tasks.md` DOING 컬럼에서 owner 확인. 전체 보드는 `../base/tasks.md` |

---

## 8. 다음에 읽을 문서

**PURPOSE**: 본 진입 문서를 다 읽은 뒤의 후속 자료 인덱스.

- `../base/CLAUDE.md` — 작업 절차·금지 사항.
- `../base/architecture.md` §3.3, §5.2 — 본 영역 책임과 server ↔ llm-include 계약.
- `../base/user-experience.md` — LLM 응답 톤·약속의 기준.
- `../base/product.md` — LLM이 풀어야 할 문제와 우선순위.
- `./progress.md` — 자료 영역의 기술·메타 표준 현황.
- `./tasks.md` — LLM 자료 영역 작업 카드.
- `../base/tasks.md` — 전체 작업 인덱스·교차 영역 카드·진행 요약.

**막혔을 때**: 서버 팀과 task 인터페이스(이름·payload 형태·응답 스키마)를 먼저 합의한 뒤 자료를 만들 것. base 문서 우선순위(`product.md > user-experience.md > architecture.md`)는 이 영역에도 동일 적용.
