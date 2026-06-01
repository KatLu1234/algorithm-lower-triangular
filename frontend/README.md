# frontend — 시간표 만들기 화면

고려대 시간표 추천 + 알고리즘 설명 도구의 프론트엔드입니다.
스택: **Vite + React 18 + TypeScript + Tailwind CSS 3** (fetch 기반 API 클라이언트).

## 실행

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

빌드 / 타입체크:

```bash
npm run build      # tsc + vite build
npm run typecheck  # tsc --noEmit
```

## 백엔드 연결

- 개발 시 `/api` 요청은 `vite.config.ts`의 프록시가 `http://127.0.0.1:8000`(FastAPI)으로 넘깁니다.
- 다른 호스트의 백엔드를 쓰려면 `.env.example`를 `.env.local`로 복사하고 `VITE_API_BASE_URL`을 채우세요.
- ⚠️ **비-비밀 값(서버 URL)만** 둡니다. LLM 키·Supabase 시크릿은 프론트에 두지 않습니다.

## 현재 상태 (2026-05-21)

- 화면: 좌측 입력 폼 + 우측 결과(주간 격자·점수 분해·포함/제외 사유)를 한 페이지에.
- **시간표 생성 엔드포인트는 서버에 아직 없습니다.** "시간표 만들기" 버튼은
  잠정 경로 `POST /api/v1/timetable/solve`를 호출하므로 현재는 실패(에러 상태)합니다.
  화면 확인은 **"샘플 결과로 미리보기"** 버튼을 쓰세요.
- 요청/응답 envelope(`src/types/timetable.ts`의 `TimetableRequest`/`TimetableResponse`)는
  **잠정**이며, 서버 팀과 `claude/base/CLAUDE.md` §3.2 안전 순서로 확정해야 합니다.
  강의/선호/결과 본체(`Course`/`PreferenceVector`/`SelectionResult`)는 이미 확정된
  `app/schemas/*` Pydantic 스키마를 미러링합니다.

## 폴더 구조

```
frontend/
├── index.html
├── src/
│   ├── main.tsx / App.tsx       # 진입점 + 페이지 레이아웃·상태
│   ├── api/client.ts            # fetch 래퍼 + {detail, code} 에러 표준 처리
│   ├── types/timetable.ts       # 백엔드 스키마 미러 타입
│   ├── lib/time.ts              # 분↔시각 변환·격자 계산
│   ├── lib/sampleData.ts        # 디자인 미리보기용 샘플 (실제 결과 아님)
│   └── components/
│       ├── PreferenceForm.tsx   # 입력 폼
│       ├── TimetableGrid.tsx    # 주간 격자 (요일 × 시간)
│       ├── ScheduleResult.tsx   # 결과 패널
│       └── States.tsx           # 로딩·에러·빈 상태
```
