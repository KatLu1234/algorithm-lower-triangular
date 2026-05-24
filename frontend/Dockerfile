# 프론트엔드 — Vite 빌드 → nginx 서빙 (멀티스테이지)

# ── 1. 빌드 스테이지 ──────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# 의존성 먼저 (lock 없음 → install)
COPY package.json ./
RUN npm install

# 소스 복사 후 정적 자산 빌드
COPY . .
RUN npm run build

# ── 2. 서빙 스테이지 ──────────────────────────────────────────────
FROM nginx:1.27-alpine

# 빌드 산출물만 옮김
COPY --from=builder /app/dist /usr/share/nginx/html
# /api 프록시 + SPA 폴백
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD wget -q -O- http://127.0.0.1/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
