#!/usr/bin/env bash
# init-letsencrypt.sh — 첫 부팅 시 Let's Encrypt 인증서 발급 부트스트랩.
#
# 절차 (한 번만 실행):
#   1) ./certbot/conf/live/<DOMAIN>/ 에 더미 자체서명 인증서 생성
#      (nginx 가 :443 SSL 블록을 로드하려면 cert 파일이 반드시 있어야 함)
#   2) docker compose up -d nginx — :80 에서 ACME 챌린지 서빙 가능 상태
#   3) 더미 cert 삭제 → certbot 으로 실 Let's Encrypt 인증서 발급
#      (--webroot 모드 — nginx 의 /.well-known/acme-challenge/ 경유)
#   4) nginx reload — 새 인증서를 메모리에 다시 로드
#
# 사전 조건:
#   - DOMAINS 의 A 레코드가 이 호스트의 공인 IP 를 가리킬 것 (DNS 전파 확인)
#   - 호스트 :80 / :443 이 외부에서 접근 가능 (방화벽·보안그룹 열려 있을 것)
#   - docker compose, openssl 설치
#
# 옵션:
#   STAGING=1 ./init-letsencrypt.sh   # rate limit 안전한 staging 서버로 먼저 테스트
#   EMAIL=you@example.com ./init-letsencrypt.sh  # 만료 알림 이메일
#
# 본 스크립트는 idempotent — 다시 실행해도 안전(기존 인증서가 있으면 확인 후 진행).
# 참고: https://github.com/wmnnd/nginx-certbot 패턴.

set -euo pipefail

# ── 설정 ────────────────────────────────────────────────────────────
DOMAINS=("kustimetable.duckdns.org")
EMAIL="${EMAIL:-}"        # 비워두면 --register-unsafely-without-email
RSA_KEY_SIZE=4096
STAGING="${STAGING:-0}"   # 0=production, 1=staging
DATA_PATH="./certbot"

# ── 사전 점검 ──────────────────────────────────────────────────────
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ docker 가 필요합니다." >&2; exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "❌ 'docker compose' 가 필요합니다 (Compose v2)." >&2; exit 1
fi

mkdir -p "$DATA_PATH/conf" "$DATA_PATH/www"

# 기존 인증서가 있으면 사용자 확인
PRIMARY="${DOMAINS[0]}"
if [ -d "$DATA_PATH/conf/live/$PRIMARY" ]; then
  read -rp "기존 인증서가 ./certbot/conf/live/$PRIMARY 에 있습니다. 다시 발급하시겠습니까? (y/N) " yn
  if [[ ! "$yn" =~ ^[Yy]$ ]]; then
    echo "기존 인증서 유지. 끝."
    exit 0
  fi
fi

# ── 1) TLS 옵션 파일 다운로드 (없으면) ───────────────────────────────
# Let's Encrypt 가 권장하는 보안 옵션. ssl_dhparam 까지는 이번 스크립트에서
# 생성하지 않는다(처음 발급 흐름을 단순하게 유지). 필요해지면 별도 추가.
if [ ! -e "$DATA_PATH/conf/options-ssl-nginx.conf" ] || [ ! -e "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
  echo "### Let's Encrypt 권장 옵션 파일 다운로드…"
  mkdir -p "$DATA_PATH/conf"
  curl -fsSL \
    "https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/src/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf" \
    > "$DATA_PATH/conf/options-ssl-nginx.conf" || true
  curl -fsSL \
    "https://raw.githubusercontent.com/certbot/certbot/master/certbot/src/certbot/ssl-dhparams.pem" \
    > "$DATA_PATH/conf/ssl-dhparams.pem" || true
fi

# ── 2) 더미 자체서명 인증서 생성 ─────────────────────────────────────
echo "### 더미 자체서명 인증서 생성 (nginx 부팅용)…"
DUMMY_PATH="/etc/letsencrypt/live/$PRIMARY"
mkdir -p "$DATA_PATH/conf/live/$PRIMARY"
docker compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE -days 1 \
    -keyout '$DUMMY_PATH/privkey.pem' \
    -out    '$DUMMY_PATH/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

# ── 3) nginx 띄우기 ──────────────────────────────────────────────────
echo "### nginx 부팅…"
docker compose up --force-recreate -d nginx
echo

# ── 4) 더미 인증서 삭제 ─────────────────────────────────────────────
echo "### 더미 인증서 삭제…"
docker compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$PRIMARY \
         /etc/letsencrypt/archive/$PRIMARY \
         /etc/letsencrypt/renewal/$PRIMARY.conf" certbot
echo

# ── 5) 실 Let's Encrypt 인증서 발급 ─────────────────────────────────
echo "### Let's Encrypt 인증서 발급…"
DOMAIN_ARGS=()
for d in "${DOMAINS[@]}"; do DOMAIN_ARGS+=( -d "$d" ); done

EMAIL_ARG="--register-unsafely-without-email"
[ -n "$EMAIL" ] && EMAIL_ARG="--email $EMAIL"

STAGING_ARG=""
[ "$STAGING" != "0" ] && STAGING_ARG="--staging"

docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $STAGING_ARG \
    $EMAIL_ARG \
    ${DOMAIN_ARGS[*]} \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --non-interactive \
    --force-renewal" certbot
echo

# ── 6) nginx 리로드 ─────────────────────────────────────────────────
echo "### nginx 리로드…"
docker compose exec nginx nginx -s reload
echo

echo "✅ 완료. HTTPS 가 활성화되었습니다 — https://${DOMAINS[0]} 에서 확인하세요."
echo "   인증서 갱신은 certbot 컨테이너가 12시간마다 자동으로 시도합니다."
