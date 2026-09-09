#!/usr/bin/env bash
# Deploy the GHF join sample to Azure App Service (free F1 tier) so it can be shared.
# Usage:  ./deploy-azure.sh            (re-run to redeploy; safe to repeat)
# Needs:  az CLI signed in (az login), and intellipay/.env with IPAY_MERCHANT_KEY / IPAY_API_KEY.
set -euo pipefail
APP="${APP:-ghf-join-demo}"; RG="${RG:-ghf-join-rg}"; LOC="${LOC:-eastus2}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT

echo "▶ staging a secret-free copy"
rsync -a --exclude '.env' --exclude 'members.json' --exclude 'postbacks.log' --exclude 'exports' \
      --exclude 'https_server.py' --exclude '__pycache__' --exclude '.gitignore' --exclude '.azure' \
      --exclude 'deploy-azure.sh' "$HERE/" "$STAGE/"
printf '# stdlib only — tells App Service (Oryx) this is a Python app\n' > "$STAGE/requirements.txt"
if grep -rq "$(grep '^IPAY_API_KEY=' "$HERE/.env" | cut -d= -f2-)" "$STAGE" 2>/dev/null; then
  echo "✗ API key found in staged files — aborting"; exit 1; fi

echo "▶ creating/updating $APP (F1 free · Linux · Python 3.12) and deploying"
# First-ever run: the app boots once with App Service's default (gunicorn) before our startup
# command exists and reports a failure. That's expected — the resources are created; the
# startup command below fixes the boot and the final restart brings it up.
( cd "$STAGE" && az webapp up --name "$APP" --resource-group "$RG" --location "$LOC" \
    --sku F1 --os-type Linux --runtime PYTHON:3.12 --output none ) \
  || echo "  (first boot failed before startup command was set — continuing, fixed below)"

echo "▶ startup command + settings"
az webapp config set -g "$RG" -n "$APP" --startup-file "python3 server.py" --output none
set -a; . "$HERE/.env"; set +a
az webapp config appsettings set -g "$RG" -n "$APP" --output none --settings \
   IPAY_MERCHANT_KEY="$IPAY_MERCHANT_KEY" IPAY_API_KEY="$IPAY_API_KEY" \
   IPAY_HOST="${IPAY_HOST:-test.cpteller.com}" PORT=8000 SCM_DO_BUILD_DURING_DEPLOYMENT=true
az webapp update -g "$RG" -n "$APP" --https-only true --output none
az webapp restart -g "$RG" -n "$APP" --output none

URL="https://$APP.azurewebsites.net"
echo "▶ waiting for the app to come up"
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$URL/api/catalog" || true)
  [ "$code" = "200" ] && break; sleep 10
done
echo
echo "✓ live:  $URL"
echo "  terminal check: $(curl -s "$URL/" | grep -c 'intellipay.initialize') intellipay refs in page (expect 4)"
echo "  logs:   az webapp log tail -g $RG -n $APP"
