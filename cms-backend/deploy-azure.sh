#!/usr/bin/env bash
# Deploy the GHF CMS backend to Azure App Service, on the same free plan as the join API.
# Usage: ./deploy-azure.sh   (re-run to redeploy; safe to repeat). Needs: az login, cms-backend/.env filled in.
set -euo pipefail
APP="${APP:-ghf-cms}"; RG="${RG:-ghf-join-rg}"; PLAN="${PLAN:-robert_asp_2750}"; LOC="${LOC:-eastus2}"
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -f "$HERE/.env" ] || { echo "✗ $HERE/.env missing — copy .env.example and fill it in"; exit 1; }
set -a; . "$HERE/.env"; set +a
for v in CMS_GITHUB_TOKEN MS_TENANT_ID MS_CLIENT_ID MS_CLIENT_SECRET; do [ -n "${!v:-}" ] || { echo "✗ $v is empty in .env"; exit 1; }; done
[ -n "${CMS_SESSION_SECRET:-}" ] || CMS_SESSION_SECRET="$(python3 -c 'import secrets;print(secrets.token_hex(32))')"
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
cp "$HERE/server.py" "$STAGE/"; printf '# stdlib only\n' > "$STAGE/requirements.txt"
echo "▶ creating/updating $APP on plan $PLAN ($RG)"
az webapp show -g "$RG" -n "$APP" -o none 2>/dev/null \
  || az webapp create -g "$RG" -p "$PLAN" -n "$APP" --runtime "PYTHON:3.12" -o none
( cd "$STAGE" && zip -qr app.zip . && az webapp deploy -g "$RG" -n "$APP" --src-path app.zip --type zip -o none )
echo "▶ startup + settings"
az webapp config set -g "$RG" -n "$APP" --startup-file "python3 server.py" -o none
URL="https://$APP.azurewebsites.net"
az webapp config appsettings set -g "$RG" -n "$APP" -o none --settings \
  CMS_GITHUB_TOKEN="$CMS_GITHUB_TOKEN" CMS_REPO="${CMS_REPO:-robertjackson-engage/ghf-redesign}" CMS_BRANCH="${CMS_BRANCH:-main}" \
  MS_TENANT_ID="$MS_TENANT_ID" MS_CLIENT_ID="$MS_CLIENT_ID" MS_CLIENT_SECRET="$MS_CLIENT_SECRET" \
  CMS_ALLOWED_DOMAINS="${CMS_ALLOWED_DOMAINS:-}" CMS_PUBLIC_URL="${CMS_PUBLIC_URL:-$URL}" \
  CMS_ALLOWED_ORIGINS="${CMS_ALLOWED_ORIGINS:-https://robertjackson-engage.github.io}" \
  CMS_SESSION_SECRET="$CMS_SESSION_SECRET" PORT=8000 SCM_DO_BUILD_DURING_DEPLOYMENT=true
az webapp update -g "$RG" -n "$APP" --https-only true -o none
az webapp restart -g "$RG" -n "$APP" -o none
echo "▶ waiting for $URL/healthz"
for i in $(seq 1 30); do curl -sf -m 10 "$URL/healthz" >/dev/null 2>&1 && break; sleep 10; done
echo; echo "✓ live: $URL"; curl -s "$URL/healthz"; echo
echo "  Microsoft redirect URI to register: $URL/auth/callback"
echo "  logs: az webapp log tail -g $RG -n $APP"
