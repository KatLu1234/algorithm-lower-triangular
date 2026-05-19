---
doc_type: progress-log
scope: llm-include
title: LLM 자료 영역 진행 이력
purpose: LLM 자료 영역의 기술·구성 스냅샷과 별도 지침 변경 이력
target_reader: LLM 자료 담당 팀원 + base 작업자 (기술·구성 변경 시)
update_rules:
  - 사용 기술 변경 시 (템플릿 엔진·프롬프트 포맷 표준·자료 직렬화 형식·LLM 공급자/모델 변경)
  - 영역 한정 별도 지침 추가 시 (base 일반 규칙으로 안 풀리는 결정)
do_not_update_for:
  - 프롬프트 문구 다듬기
  - new few-shot 케이스 1건 추가
  - 자료 파일 자체의 메타 헤더와 git 커밋으로 충분한 변경
authoritative_for:
  - LLM 자료 영역의 현재 기술·구성 (§1)
  - LLM 자료 영역 한정 별도 지침 (§2)
status: 초안 단계 (첫 자료 추가 시 §1 확정)
last_updated: 2026-05-17
---

# llm-include/progress.md — LLM 자료 영역 진행 이력

## 1. 현재 사용 기술 / 구성 (스냅샷)

**PURPOSE**: 영역의 권위 있는 기술·구성 상태.
**STATUS**: **아직 초안 단계.** 첫 자료가 추가될 때 함께 확정.

| 분류 | 선택 | 비고 |
| ---- | ---- | ---- |
| 자료 형식 | (TBD: `.md` / `.txt` / `.json`) | 프롬프트와 few-shot의 포맷이 다를 수 있음 |
| 템플릿 엔진 | (TBD: Jinja2 / `str.format` / 직접 치환) | 서버 `app/libs/llm_context.py`와 짝 |
| 디렉터리 구조 | (계획) `prompts/`, `examples/<task>/`, `domain/` | `../base/architecture.md` §5 참고 |
| 메타 헤더 표준 | (TBD: YAML front-matter 등) | 목적·기대 사용처·마지막 수정일 포함 |
| LLM 공급자 / 모델 | (TBD) | `../server/progress.md`와 같은 결정일 가능성 큼 |
| 토큰 한도 / 컨텍스트 정책 | (TBD) | 자료 크기 제한 결정 |

---

## 2. 별도 지침 (llm-include 한정)

**PURPOSE**: `claude/base/` 일반 규칙으로 안 풀리는 자료 영역 한정 결정 기록.

| 항목 | 결정 | 결정일 | 사유 |
| ---- | ---- | ------ | ---- |
| (예) 시스템 프롬프트 길이 상한 | 영문 500단어 이내 | TBD | 토큰 비용·정확도 균형 |
|      |      |        |      |

---

## 3. 변경 이력

**PURPOSE**: 기술/구성 또는 별도 지침 변경의 시간 순 이력.
**RULE**: 가장 최근이 맨 위. 콘텐츠 변경은 기재하지 않음.

| 날짜 | 항목 | 변경 | 사유 / 트리거 |
| ---- | ---- | ---- | ------------- |
| 2026-05-17 | 지침 추가 | `llm-include/tasks.md` 신설 — LLM 자료 영역 작업 칸반(TODO/DOING/DONE) + 카드 형식. 새 task 추가 카드는 (a)프롬프트 (b)case 1개 이상 (c)메타 헤더 모두 갖춰야 DONE 조건 명시 | 팀원 작업 확인 보드 도입 |
| 2026-05-17 | 지침 추가 | `llm-include/team-guide.md` 신설 — LLM 자료 담당의 영역 진입 문서(데이터-온리 원칙·메타 헤더·서버와의 task 합의 사이클·검증용 Claude 사용 패턴 포함) | 영역 팀원 온보딩 통일 |
| 2026-05-17 | 진행 파일 | `llm-include/progress.md` 신설, 초기 미정 상태 기록 | "각 scheme에 진행상황 파일" 지시 |

---

## 4. 변경 유형 분류

**PURPOSE**: §3 변경 이력의 "항목" 컬럼 표준화 카테고리.

| 유형 | 의미 |
| ---- | ---- |
| 형식 변경 | 자료 포맷·디렉터리 구조·메타 표준 변경 |
| 엔진 변경 | 템플릿 엔진 도입/교체 |
| 공급자 변경 | LLM 공급자·모델 변경 |
| 지침 추가 | llm-include 한정 규칙이 새로 굳어짐 |
| 지침 폐기 | 더 이상 적용되지 않는 규칙 제거 |
