# algorithm-lower-triangular

국민대 학생용 시간표 추천 + 알고리즘 단위 설명 도구.

## 빠른 시작 — Docker Compose (권장)

```bash
docker compose up --build
```

뜨고 나면:

- **시간표 만들기 화면** → http://localhost:8080
- 백엔드 직접 호출 / OpenAPI → http://localhost:8000/docs

`/api/*` 요청은 frontend(nginx)가 backend(FastAPI)로 자동 프록시합니다 (`frontend/nginx.conf`).

### 정리

```bash
docker compose down            # 컨테이너 중지·제거
docker compose down --rmi all  # 이미지까지 제거
```

## 빠른 시작 — Docker 없이 로컬

두 개의 터미널이 필요합니다.

```bash
# (터미널 1) 백엔드 — Python 3.12 + requirements.txt 설치 가정
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# (터미널 2) 프론트엔드 — Node 20+ 가정
cd frontend
npm install
npm run dev   # http://localhost:5173 (Vite 프록시가 8000으로 /api 넘김)
```

## 구조 한눈에

```
algorithm-lower-triangular/
├── app/                     FastAPI 백엔드 (알고리즘 코어 + 라우트)
│   ├── main.py              ★ 진입점 + CORS + RequestValidationError 핸들러
│   ├── api/endpoints/
│   │   └── timetable.py     ★ POST /api/v1/timetable/solve
│   ├── libs/                A·B·C 트리 + 12개 알고리즘
│   └── schemas/             Pydantic 계약 (common·preferences·feasibility·valuation·selection)
│
├── frontend/                Vite + React + TypeScript + Tailwind
│   ├── src/
│   │   ├── App.tsx          좌측 입력 폼 + 우측 결과 패널
│   │   ├── components/      PreferenceForm · TimetableGrid · ScheduleResult · States
│   │   ├── api/client.ts    {detail, code} 에러 정형 + fetch 래퍼
│   │   └── types/timetable.ts  백엔드 Pydantic 미러 타입
│   ├── Dockerfile           멀티스테이지 (node 빌드 → nginx 서빙)
│   └── nginx.conf           /api → backend:8000 프록시 + SPA 폴백
│
├── claude/                  설계·결정 문서 (`base/`가 권위)
├── tests/                   pytest (스키마 케이스 11개)
├── Dockerfile.backend       python:3.12-slim + uvicorn
├── docker-compose.yml       backend(8000) + frontend(8080)
└── requirements.txt
```

자세한 작업 지침은 [`claude/CLAUDE.md`](claude/CLAUDE.md), 설계 결정은 [`claude/base/`](claude/base/).

## 현재 동작 범위 (MVP)

- ✓ 프론트에서 강의 후보·학점·중요도·blackout 입력 → 백엔드가 top-K 시간표 + 점수 분해 + 포함/배제 사유 반환
- ✓ A-B-C 트리 그대로 (Feasibility → Valuation → Selection), 그룹·교수 차원 반영
- ✓ Infeasibility 응답 (필수 강의 충돌·학점 한도 등) — 사용자 친화 hint 포함
- ✓ **국민대 `sample_data.csv` 파싱** — `time_room` 필드(`화(6-8) 석원경상관 112호` 등)를
  `TimeSlot`으로 변환. 1교시=9시, n교시=(n+8)시 매핑. 같은 `cour_cd`의 분반들은 자동으로
  같은 `course_group_id`로 묶여 그룹 배타 규칙이 그대로 적용됨. 프론트는 마운트 시
  `GET /api/v1/timetable/sample-courses` 호출해 후보 풀을 채움
- ✓ **슬롯별 건물 override** — 같은 강의가 요일마다 다른 건물(예: 월 본관 강의 / 수 공학관 실습)
  쓰는 경우를 A-2 호환 검사·B-3 travel_penalty에 정확히 반영
- ⏳ LLM 자연어 설명 — `explain: true` 옵션은 수신하지만 현재 `explanation: null` 반환 (Upstage 공급자 확정 후 별도 base 변경)
- ⏳ DB 영속화 — 후보 강의는 매 요청 본문에서 전달. Supabase 연결은 미적용 (`claude/server/db/` 설계만 존재)
- ⏳ 건물 거리 — 현재는 후보 강의에서 자동 추출 + 다른 건물 5분 기본값. 실제 거리표는 후속 단계
