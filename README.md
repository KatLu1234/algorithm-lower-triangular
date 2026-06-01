# algorithm-lower-triangular

고려대 학생용 시간표 추천 + 알고리즘 단위 설명 도구.

## 빠른 시작 — Docker Compose (HTTPS, 운영 토폴로지)

docker compose는 **HTTPS 운영형 토폴로지**(nginx TLS 종단 + Let's Encrypt + FastAPI)로 동작합니다. 로컬 개발은 [Docker 없이 로컬](#빠른-시작--docker-없이-로컬) 섹션을 사용하세요.

### 1) 사전 준비

- 공인 IP가 있는 호스트(EC2/오라클 무료티어 등)
- 도메인 A 레코드가 호스트 IP를 가리킴 (`nginx.conf`·`init-letsencrypt.sh`의 `kustimetable.duckdns.org`를 본인 도메인으로 바꾸세요)
- 호스트의 80·443 포트가 외부에 열려 있어야 함 (Let's Encrypt 검증)
- `docker compose v2`, `openssl`, `curl`, `wget`

### 2) Let's Encrypt 인증서 최초 발급 (한 번)

```bash
# (선택) staging 으로 먼저 테스트 — rate limit 안전
STAGING=1 EMAIL=you@example.com ./init-letsencrypt.sh

# 실제 발급
EMAIL=you@example.com ./init-letsencrypt.sh
```

스크립트가 더미 자체서명 → nginx 부트 → certbot `--webroot` 실 인증서 → nginx reload 까지 자동.

### 3) 일반 기동

```bash
# (선택) 자연어 입력 기능을 켜려면 Upstage Solar API 키
export UPSTAGE_API_KEY=up_xxxxxxxxxxxxxxxxx

docker compose up -d --build
```

뜨고 나면:

- **앱 화면** → `https://<your-domain>/`
- HTTP 요청은 301로 HTTPS 리다이렉트
- `/api/*` 요청은 nginx가 backend(FastAPI)로 프록시 (`frontend/nginx.conf`)

### 4) 인증서 갱신

`certbot` 서비스가 12시간마다 `certbot renew`를 자동 실행, nginx 서비스도 6시간마다 자체 `nginx -s reload`를 돌려 새 인증서를 메모리에 다시 로드. **수동 갱신 불필요**.

### 5) 포트 충돌 시

호스트의 80·443이 점유돼 있으면 `.env`로 우회:

```bash
HTTP_PORT=8080 HTTPS_PORT=8443 docker compose up -d
```

단, Let's Encrypt 챌린지는 **외부에서 :80**으로 와야 하므로 운영 환경에서는 표준 포트를 권장.

### 정리

```bash
docker compose down            # 컨테이너 중지·제거 (cert/auth 볼륨은 유지)
docker compose down -v --rmi all  # 볼륨·이미지까지 제거 (계정·인증서 전부 사라짐)
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
├── docker-compose.yml       nginx(:80→301, :443 TLS) + backend(내부 :8000) + certbot(자동 갱신)
├── init-letsencrypt.sh      ★ 최초 1회 — 더미 cert → 실 Let's Encrypt 인증서 발급
├── certbot/conf/            ★ /etc/letsencrypt 영속화 (인증서·옵션)
├── certbot/www/             ★ ACME http-01 챌린지 webroot
└── requirements.txt
```

자세한 작업 지침은 [`claude/CLAUDE.md`](claude/CLAUDE.md), 설계 결정은 [`claude/base/`](claude/base/).

## 현재 동작 범위 (MVP)

- ✓ 프론트에서 강의 후보·학점·중요도·blackout 입력 → 백엔드가 top-K 시간표 + 점수 분해 + 포함/배제 사유 반환
- ✓ A-B-C 트리 그대로 (Feasibility → Valuation → Selection), 그룹·교수 차원 반영
- ✓ Infeasibility 응답 (필수 강의 충돌·학점 한도 등) — 사용자 친화 hint 포함
- ✓ **고려대 `sample_data.csv` 파싱** — `time_room` 필드(`화(6-8) 석원경상관 112호` 등)를
  `TimeSlot`으로 변환. 1교시=9시, n교시=(n+8)시 매핑. 같은 `cour_cd`의 분반들은 자동으로
  같은 `course_group_id`로 묶여 그룹 배타 규칙이 그대로 적용됨. 프론트는 마운트 시
  `GET /api/v1/timetable/sample-courses` 호출해 후보 풀을 채움
- ✓ **슬롯별 건물 override** — 같은 강의가 요일마다 다른 건물(예: 월 본관 강의 / 수 공학관 실습)
  쓰는 경우를 A-2 호환 검사·B-3 travel_penalty에 정확히 반영
- ✓ **자연어 입력 → PreferenceVector 자동 채우기** — Upstage Solar API(`solar-pro2`)로
  "전공 위주로 듣고 금요일은 통학이라 비워주세요. 조민호 교수님 운영체제 듣고 싶어요"
  같은 문장을 가중치·blackout·교수 선호·필수/제외로 변환. 화면에 *이해한 항목*과
  *이해 못 한 / 미지원 항목*을 항상 명시. `UPSTAGE_API_KEY` 미설정 시 자동 비활성
- ⏳ LLM 자연어 *설명* (결과 해설) — `explain: true` 옵션은 수신하지만 현재 `explanation: null` 반환
- ⏳ DB 영속화 — 후보 강의는 매 요청 본문에서 전달. Supabase 연결은 미적용 (`claude/server/db/` 설계만 존재)
- ⏳ 건물 거리 — 현재는 후보 강의에서 자동 추출 + 다른 건물 5분 기본값. 실제 거리표는 후속 단계
