# 페이지: `/login` — 로그인 / 회원가입

> 페이지 설계 문서 — 한 페이지당 한 파일. 전체 목록·라우팅은 [`index.md`](./index.md).
> 공통 작성 항목은 `index.md` §8.

## 1. 목적

토큰이 없거나 만료된 사용자가 인증을 거쳐 보호 라우트(`/`, `/timetable`, `/courses`)로 들어가는 유일한 입구. 로그인과 회원가입은 같은 페이지에 **탭 두 개**로 둔다(신규 사용자에게 별도 페이지로 보내지 않고 한 화면에서 결정). UX 우선순위 — 단순함·빠른 진입(`base/product.md` §4 후순위인 응답속도 직전의 마찰 최소화).

## 2. 진입 경로

- URL: `/login`
- 인증 필요: 아니오 (오히려 인증된 사용자가 들어오면 즉시 `from` 또는 `/`로 리다이렉트해 재방문 방지)
- 어디서 오는가: 앱 첫 진입, 로그아웃, 보호 라우트 가드 실패, 토큰 만료(`/me` 401)

## 3. 레이아웃

단독 풀스크린 — 헤더/공통 셸 없음(현재 `frontend/src/components/Login.tsx` 패턴 유지). 가운데 카드 한 장:

```
┌────────────────────────────────────────────────┐
│                                                │
│              [ 로고/타이틀 ]                     │
│                                                │
│   ┌──────────────────────────────────────┐    │
│   │  [ 로그인 ]  [ 회원가입 ]              │ ← 탭 │
│   ├──────────────────────────────────────┤    │
│   │  email   _______________________     │    │
│   │  password ______________________     │    │
│   │  (회원가입 탭일 때) display_name ____ │    │
│   │                                      │    │
│   │  [ 로그인하기 / 가입하기 ]             │    │
│   │                                      │    │
│   │  에러 메시지(있을 때)                   │    │
│   └──────────────────────────────────────┘    │
│                                                │
└────────────────────────────────────────────────┘
```

- 카드 너비 약 380–420px, 화면 가운데 정렬, 배경은 크림(`#F6F3EE`).
- 탭 활성 색은 브랜드 마룬(`#7C001A`).

## 4. 상태(state)

페이지 로컬 useState로 충분(전역 X):
- `mode: "login" | "signup"` — 탭 선택
- `email: string`, `password: string`, `displayName?: string`
- `submitting: boolean`
- `error: string | null` — `{detail, code}` 의 친화 메시지로 변환된 값

성공 시 부모(App/router)에 토큰·사용자 정보 전파:
- 토큰 → `localStorage["auth_token"]` (현재 `frontend/src/api/auth.ts` 의 `getToken`/`setToken` 유지)
- 사용자 → 전역 사용자 컨텍스트(또는 라우트 최상위 state)에 `UserPublic` 저장

## 5. 사용 API

| 메서드 | 경로 | 요청 | 응답 | 출처 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | `LoginRequest { email, password }` | `AuthResponse { token, user }` | `app/schemas/auth.py` |
| POST | `/api/v1/auth/signup` | `SignupRequest { email, password, display_name? }` | `AuthResponse { token, user }` | `app/schemas/auth.py` |
| GET | `/api/v1/auth/me` | (Bearer 토큰) | `UserPublic` | 진입 후 토큰 검증용 — 본 페이지 안에서는 호출하지 않고 `<ProtectedRoute>` 가 호출 |

에러 응답은 `{detail, code}` 표준. 본 페이지에서 다루는 코드:

| code | HTTP | 사용자에게 보여줄 친화 메시지 |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | "이메일 또는 비밀번호 형식을 확인해 주세요." (detail 그대로 노출 금지) |
| `INVALID_CREDENTIALS` | 401 | "이메일 또는 비밀번호가 올바르지 않습니다." (서버 detail과 동일 톤) |
| `EMAIL_TAKEN` | 409 | "이미 등록된 이메일입니다. 로그인 탭으로 이동해 주세요." |
| 그 외/네트워크 | — | "잠시 후 다시 시도해 주세요." + 재시도 버튼 |

## 6. 컴포넌트 분해

```
<LoginPage>
└─ <AuthCard>                      // 카드 셸
   ├─ <TabSwitch login|signup />   // 탭 두 개
   ├─ <LoginForm />  ─ mode==='login' 일 때
   └─ <SignupForm /> ─ mode==='signup' 일 때
```

재사용 자산: 현재 `frontend/src/components/Login.tsx`(이미 로그인/가입 UI 다 들어 있음)를 `pages/LoginPage.tsx`로 옮기고 onAuthenticated 콜백 → router navigate로 교체.

## 7. 인터랙션 (Happy Path)

1. 사용자가 이메일·비밀번호를 입력(회원가입은 display_name까지) → submit.
2. `submitting=true`, 버튼 비활성, 폼 inert.
3. 성공: 토큰 저장, 전역 사용자 컨텍스트 갱신, `useNavigate()` 로 `state.from?.pathname ?? "/"` 로 replace 이동(브라우저 히스토리에 /login 안 남김).
4. 회원가입 성공이면 메인에 환영 토스트(현재 `App.tsx` 의 welcome 패턴 유지). 토스트 텍스트만 라우트 이동의 state로 전달.

## 8. 상태 — 로딩 / 에러 / 빈

- **로딩(submitting)**: 버튼 라벨을 "처리 중…"으로 바꾸고 spinner. 입력 비활성. 다중 submit 차단.
- **에러**: 카드 하단 alert 영역에 친화 메시지(§5 표). 입력 값은 유지(특히 비밀번호는 비우지 않는다 — 사용자가 다시 칠 필요 없게).
- **빈 상태**: 초기 진입은 폼이 그 자체로 "할 일이 명확한 상태"라 별도 빈 안내 불필요.

> 인증된 사용자가 어떤 이유로든 `/login`에 직접 접근하면 `<Navigate to="/" replace />` 로 즉시 빠져나가게 한다(빈 상태 자체가 발생하지 않게).

## 9. 나가는 길

| 액션 | 도착 |
| --- | --- |
| 로그인/가입 성공 | `state.from` 이 있으면 그곳, 없으면 `/` |
| 이미 인증된 채 진입 | `/` (replace) |
| 가입 탭에서 "로그인" 링크 클릭 | 같은 페이지에서 탭만 전환 (라우트 이동 X) |

## 10. 열린 항목 / 향후

- **비밀번호 정책 강화**: 현재 서버는 `min_length=4` 만 강제. 운영 전환 시 길이·복잡도 정책을 서버와 같이 올리고, 본 페이지에서 클라이언트 1차 검증 추가.
- **Supabase Auth 전환 후**: 서버가 `auth.users` 기반 JWT를 발급하면 본 페이지의 요청·응답 모양은 같지만 토큰 형식이 바뀐다(서명·exp 클레임). `frontend/src/api/auth.ts` 의 토큰 파싱 추가 가능.
- **소셜 로그인 / 이메일 검증**: 현재 비-목적. UX 페르소나 확정 후 product 차원에서 결정.
- **"비밀번호 잊음" 흐름**: 현재 없음. Supabase Auth 도입 시 자연스레 따라옴.
