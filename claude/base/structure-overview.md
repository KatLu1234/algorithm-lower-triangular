# structure-overview.md — 프로젝트 구조도

> 본 문서는 알고리즘 시간표 추천 프로젝트의 **현재 계획 상태**를 한 장으로 시각화한 자료입니다.
> 새 팀원이 처음 진입할 때, 또는 작업 흐름에서 길을 잃었을 때 본 그림으로 컨텍스트를 잡으세요.
> 본 그림은 스냅샷입니다 — 계획 변경 시 함께 갱신해야 합니다 (§5 갱신 규칙).

---

## 1. 한 장 구조도 (2026-05-17 기준)

<svg viewBox="0 0 1000 670" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d">
  <title id="t">현재 계획 구조도 — 비전 · 기준 결정 · 초안 · 구현 · 미결정</title>
  <desc id="d">균형 모델(후보 C) 비전 아래 네 가지 영역의 현재 상태. 좌상: 기준 결정(claude/base/) 6개 문서 상태. 우상: 초안(drafts/algorithm-tree.md §9) 확정 — A·B·C와 12개 알고리즘. 좌하: 구현(app/) 대부분 대기. 우하: 영역 문서 9개 변환 완료 + TBD 항목들. 상태 범례 4종.</desc>

  <defs>
    <style>
      .panel       { fill: var(--color-bg-primary, transparent); stroke: currentColor; stroke-width: 1.6; }
      .panel-hi    { fill: var(--color-bg-secondary, #f5f5f4); stroke: currentColor; stroke-width: 1.6; }
      .item-done   { fill: var(--color-bg-secondary, #f0f0ee); stroke: currentColor; stroke-width: 1.2; }
      .item-draft  { fill: var(--color-bg-tertiary, #fef3e7); stroke: currentColor; stroke-width: 1.4; stroke-dasharray: 5 3; }
      .item-wait   { fill: none; stroke: currentColor; stroke-width: 1.2; stroke-dasharray: 4 3; }
      .item-tbd    { fill: none; stroke: currentColor; stroke-width: 1; stroke-dasharray: 1 3; }

      .t-vision-title { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 17px; font-weight: 700; }
      .t-vision-sub   { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 12px; opacity: 0.7; }
      .t-panel-title  { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 14px; font-weight: 700; letter-spacing: 0.2px; }
      .t-panel-sub    { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 11px; opacity: 0.6; font-style: italic; }
      .t-item-title   { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 12.5px; font-weight: 600; }
      .t-item-sub     { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 10.5px; opacity: 0.65; }
      .t-status       { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 11px; font-weight: 700; }
      .t-tree-row     { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 12px; }
      .t-tree-arr     { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 14px; opacity: 0.55; }
      .t-note         { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 11px; opacity: 0.55; font-style: italic; }
      .t-legend       { fill: currentColor; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK KR", sans-serif; font-size: 11.5px; }
    </style>
  </defs>

  <!-- ══════════ VISION ══════════ -->
  <rect x="20" y="18" width="960" height="64" rx="10" class="panel-hi"/>
  <text x="500" y="44" text-anchor="middle" class="t-vision-title">현재 계획 — 균형 모델 (후보 C)</text>
  <text x="500" y="64" text-anchor="middle" class="t-vision-sub">고려대 학생 시간표 추천 + 알고리즘 단위 설명  ·  product.md ✓ 결정</text>

  <!-- ══════════ TIER 2 ══════════ -->

  <!-- ─── 좌: 기준 결정 ─── -->
  <rect x="20" y="100" width="470" height="245" rx="10" class="panel"/>
  <text x="38" y="125" class="t-panel-title">기준 결정  (claude/base/)</text>
  <text x="455" y="125" text-anchor="end" class="t-panel-sub">의사결정 문서</text>

  <rect x="38" y="138" width="200" height="46" rx="5" class="item-done"/>
  <text x="48" y="158" class="t-item-title">✓ product.md</text>
  <text x="48" y="175" class="t-item-sub">§1~§5 채움 · 우선순위 10 · LLM 불변항</text>

  <rect x="252" y="138" width="220" height="46" rx="5" class="item-wait"/>
  <text x="262" y="158" class="t-item-title">⏳ user-experience.md  ★ 다음</text>
  <text x="262" y="175" class="t-item-sub">페르소나·여정·약속·인터랙션 원칙</text>

  <rect x="38" y="194" width="200" height="46" rx="5" class="item-draft"/>
  <text x="48" y="214" class="t-item-title">◐ architecture.md</text>
  <text x="48" y="231" class="t-item-sub">§1-3 ✓ · §4.1 트리 흡수 ⏳</text>

  <rect x="252" y="194" width="220" height="46" rx="5" class="item-done"/>
  <text x="262" y="214" class="t-item-title">✓ algorithms.md</text>
  <text x="262" y="231" class="t-item-sub">참조용 · 4+ 알고리즘 요건</text>

  <rect x="38" y="250" width="200" height="46" rx="5" class="item-wait"/>
  <text x="48" y="270" class="t-item-title">⏳ tasks.md</text>
  <text x="48" y="287" class="t-item-sub">전체 칸반 (빈 보드)</text>

  <rect x="252" y="250" width="220" height="46" rx="5" class="item-done"/>
  <text x="262" y="270" class="t-item-title">✓ progress.md</text>
  <text x="262" y="287" class="t-item-sub">변경 이력 운영 중</text>

  <text x="38" y="318" class="t-note">우선순위: 정확성 → 설명가능성 → 중요도 충실도 → 불가능 안내 → 검증 → 응답속도 → …</text>
  <text x="38" y="334" class="t-note">LLM 불변항: 결정은 알고리즘, LLM은 번역가(입구) · 변호인(출구)</text>

  <!-- ─── 우: 초안 (algorithm tree) — 확정 ─── -->
  <rect x="510" y="100" width="470" height="245" rx="10" class="panel-hi"/>
  <text x="528" y="125" class="t-panel-title">초안  drafts/algorithm-tree.md §9</text>
  <text x="965" y="125" text-anchor="end" class="t-status">✓ 확정 (locked)</text>

  <rect x="528" y="138" width="436" height="50" rx="5" class="item-done"/>
  <text x="540" y="158" class="t-item-title">[A] 가능성 분석  (Feasibility)</text>
  <text x="540" y="177" class="t-tree-row">A-1 풀 정제 (해시) · A-2 충돌 산출 (정렬·이진) · A-3 가지치기 (활동선택)</text>

  <text x="746" y="201" text-anchor="middle" class="t-tree-arr">↓</text>

  <rect x="528" y="207" width="436" height="50" rx="5" class="item-done"/>
  <text x="540" y="227" class="t-item-title">[B] 가치 평가  (Valuation)</text>
  <text x="540" y="246" class="t-tree-row">B-1 v(c) (해시·이진) · B-2 전이비용 (플로이드) · B-3 DP+top-K (행렬경로 DP + 0-1 배낭)</text>

  <text x="746" y="270" text-anchor="middle" class="t-tree-arr">↓</text>

  <rect x="528" y="276" width="436" height="50" rx="5" class="item-done"/>
  <text x="540" y="296" class="t-item-title">[C] 선택과 비교  (Selection)</text>
  <text x="540" y="315" class="t-tree-row">C-1 정렬·동률 (합병) · C-2 쌍 비교 (LCS) · C-3 사유 색인 (해시)</text>

  <text x="746" y="338" text-anchor="middle" class="t-note">필수 9 + 옵션 3 = 12 알고리즘 · algorithms.md 5 카테고리 모두 횡단</text>

  <!-- ══════════ TIER 3 ══════════ -->

  <!-- ─── 좌: 구현 ─── -->
  <rect x="20" y="365" width="470" height="220" rx="10" class="panel"/>
  <text x="38" y="390" class="t-panel-title">구현  (app/)</text>
  <text x="455" y="390" text-anchor="end" class="t-status">✓ 대부분 구현됨</text>

  <rect x="38" y="402" width="434" height="36" rx="5" class="item-done"/>
  <text x="48" y="425" class="t-item-title">✓ FastAPI 골격  +  Supabase 클라이언트 (`app/db/supabase.py`)</text>

  <rect x="38" y="446" width="434" height="36" rx="5" class="item-done"/>
  <text x="48" y="469" class="t-item-title">✓ app/schemas/  —  PreferenceVector · FeasibilityResult · ValuationResult · SelectionResult</text>

  <rect x="38" y="490" width="434" height="36" rx="5" class="item-done"/>
  <text x="48" y="513" class="t-item-title">✓ app/libs/  —  A·B·C 노드 + 9 알고리즘 구현(+옵션 3) (순수 함수)</text>

  <rect x="38" y="534" width="210" height="36" rx="5" class="item-done"/>
  <text x="48" y="557" class="t-item-title">✓ POST /api/v1/timetable/solve</text>

  <rect x="262" y="534" width="210" height="36" rx="5" class="item-done"/>
  <text x="272" y="557" class="t-item-title">✓ tests/  (단위)</text>

  <!-- ─── 우: 영역 문서 + TBD ─── -->
  <rect x="510" y="365" width="470" height="220" rx="10" class="panel"/>
  <text x="528" y="390" class="t-panel-title">영역 문서  +  미결정</text>
  <text x="965" y="390" text-anchor="end" class="t-panel-sub">claude/{server, frontend, llm-include}</text>

  <rect x="528" y="402" width="436" height="50" rx="5" class="item-done"/>
  <text x="540" y="422" class="t-item-title">✓ 영역 9개 문서  —  Gemini-친화 형식 변환 완료</text>
  <text x="540" y="441" class="t-item-sub">team-guide.md · tasks.md · progress.md  ×  3 영역  =  9 파일 (YAML front matter + 절별 라벨)</text>

  <rect x="528" y="460" width="210" height="40" rx="5" class="item-tbd"/>
  <text x="538" y="479" class="t-item-title">❓ 프론트엔드 스택</text>
  <text x="538" y="494" class="t-item-sub">React / Vue / Svelte / HTML?</text>

  <rect x="752" y="460" width="212" height="40" rx="5" class="item-tbd"/>
  <text x="762" y="479" class="t-item-title">❓ LLM 공급자 · 모델</text>
  <text x="762" y="494" class="t-item-sub">server·llm-include 동시 결정</text>

  <rect x="528" y="508" width="436" height="40" rx="5" class="item-tbd"/>
  <text x="540" y="527" class="t-item-title">❓ 자유 텍스트 LLM-A 도입 여부</text>
  <text x="540" y="542" class="t-item-sub">product.md §5.2 보류 — 단계적 도입 vs 입력 폼 단순화</text>

  <text x="528" y="572" class="t-note">결정 보류된 항목들은 user-experience.md / architecture.md 작성 시 자연스럽게 풀림</text>

  <!-- ══════════ LEGEND ══════════ -->
  <g transform="translate(20, 615)">
    <rect x="0" y="-9" width="18" height="13" rx="2" class="item-done"/>
    <text x="24" y="1" class="t-legend">✓ 결정 / 완료</text>

    <rect x="160" y="-9" width="18" height="13" rx="2" class="item-draft"/>
    <text x="184" y="1" class="t-legend">◐ 부분 완료 / 초안</text>

    <rect x="340" y="-9" width="18" height="13" rx="2" class="item-wait"/>
    <text x="364" y="1" class="t-legend">⏳ 대기 / 다음 단계</text>

    <rect x="520" y="-9" width="18" height="13" rx="2" class="item-tbd"/>
    <text x="544" y="1" class="t-legend">❓ TBD / 미결정</text>

    <text x="960" y="1" text-anchor="end" class="t-note">★ = 즉시 다음 단계</text>
  </g>

  <!-- ══════════ 시각적 흐름 화살표 ══════════ -->
  <text x="495" y="222" text-anchor="middle" class="t-tree-arr">→</text>
  <text x="495" y="475" text-anchor="middle" class="t-tree-arr">↑</text>
</svg>

---

## 2. 그림 읽는 법

- **상단 헤더**: 비전 (균형 모델, 후보 C). 출처: `./product.md` §1.
- **좌상 패널 — 기준 결정**: `claude/base/` 6개 문서의 현재 상태 (✓ ⏳ ◐).
- **우상 패널 — 초안**: `drafts/algorithm-tree.md` §9 — 알고리즘 분해 트리. A·B·C 책임 기반 3분할 + 9개 자식 노드 + 12개 알고리즘. 2026-05-17 확정.
- **좌하 패널 — 구현**: `app/` 의 현재 상태. FastAPI 골격·Supabase 클라이언트만 ✓, 나머지는 ⏳.
- **우하 패널 — 영역 문서 + 미결정**: `claude/{server, frontend, llm-include}/` 9개 ✓ Gemini-친화 형식 변환 완료 + TBD 3건.

## 3. 위치 매핑 (그림 박스 ↔ 실제 파일)

| 그림 박스 | 권위 있는 출처 |
| --------- | ------------- |
| 비전 헤더 | [`./product.md`](./product.md) §1 한 줄 요약 |
| product.md | [`./product.md`](./product.md) |
| user-experience.md (다음 단계) | [`./user-experience.md`](./user-experience.md) (빈 템플릿) |
| architecture.md | [`./architecture.md`](./architecture.md) |
| algorithms.md | [`./algorithms.md`](./algorithms.md) |
| tasks.md | [`./tasks.md`](./tasks.md) |
| progress.md | [`./progress.md`](./progress.md) |
| 초안 / 알고리즘 트리 | [`./drafts/algorithm-tree.md`](./drafts/algorithm-tree.md) §9 (확정) |
| 구현 (app/) | `<project root>/app/` |
| 영역 문서 | [`../server/`](../server/), [`../frontend/`](../frontend/), [`../llm-include/`](../llm-include/) |
| 미결정 (프론트 스택·LLM 공급자·LLM-A 도입) | [`./product.md`](./product.md) §5.2, [`../frontend/progress.md`](../frontend/progress.md), [`../llm-include/progress.md`](../llm-include/progress.md) |

## 4. 상태 기호

| 기호 | 의미 |
| ---- | ---- |
| `✓` | 결정 / 완료 |
| `◐` | 부분 완료 / 초안 (architecture.md처럼 일부 절만 결정된 경우) |
| `⏳` | 대기 / 다음 단계 |
| `❓` | TBD / 미결정 |

## 5. 갱신 규칙

본 그림은 base 문서이므로 다음 시점에 갱신 — 모두 같은 응답에서 [`./progress.md`](./progress.md) §2에 한 줄 남깁니다 ([`./CLAUDE.md`](./CLAUDE.md) §5.1).

- **상태 변화**: `⏳ → ✓`, `◐ → ✓`, `❓ → 결정` 등의 전환 시.
- **새 박스 추가**: 새 영역·새 결정이 더해질 때 (예: 4번째 영역 도입, 새 base 문서 추가).
- **박스 제거**: 폐기된 결정·문서.
- **그림 자체 폐기**: 프로젝트 종료 또는 본 그림이 더 이상 유의미하지 않을 때.

갱신은 base 변경입니다 ([`./CLAUDE.md`](./CLAUDE.md) §1 분류). 큰 변경(박스 추가·제거)은 사용자 승인 절차(§2) 적용.

## 6. 변경 이력

| 날짜 | 변경 내용 |
| ---- | --------- |
| 2026-05-17 | 신설 — 현재 계획 한 장 구조도 (비전 + 4 패널 + 범례). algorithm-tree.md §9 확정 처리 직후 상태 반영. |
