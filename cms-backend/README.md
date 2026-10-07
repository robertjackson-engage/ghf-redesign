# GHF CMS backend — Microsoft sign-in for the content portal

Staff sign in to `/admin/` (and the visual text editor at `/admin/edit.html`) with their **Microsoft
work account**. No GitHub accounts, no tokens to hand out. This small service sits between the CMS
and GitHub:

```
 staff browser ──Microsoft login──▶  ghf-cms (this)  ──one GitHub token──▶  github.com/…/ghf-redesign
   /admin/            PKCE OAuth        Gitea-compatible API                   content/ only
```

* **Only `content/` and `docs/assets/img/` can be written.** `build.py`, the deploy workflow and the
  join/IntelliPay code are unreachable from the portal, whoever is signed in.
* Every commit is **attributed to the editor** (name + email from Microsoft) and ends with
  “Edited in the GHF CMS by …”, so history still shows who changed what.
* Access is controlled in Microsoft: remove someone from the tenant (or from `CMS_ALLOWED_DOMAINS`)
  and they can no longer edit. Sessions last 12 hours.

## One-time setup (≈15 minutes)

### 1. Microsoft app registration  *(Microsoft 365 admin for GHF)*
Entra admin center → **App registrations** → **New registration**
- Name: `GHF Website CMS`
- Supported account types: **Accounts in this organizational directory only**
- Redirect URI: **Web** → `https://ghf-cms.azurewebsites.net/auth/callback`
- After creating: copy **Application (client) ID** → `MS_CLIENT_ID`, and **Directory (tenant) ID** → `MS_TENANT_ID`.
- **Certificates & secrets** → New client secret (24 months) → copy the *value* → `MS_CLIENT_SECRET`.
- **API permissions** → Microsoft Graph → Delegated → `openid`, `profile`, `email`, `User.Read`
  (these are usually present by default) → **Grant admin consent**.

### 2. GitHub token  *(repo owner — once)*
github.com → Settings → Developer settings → **Fine-grained tokens** → Generate
- Repository access: **Only select repositories → ghf-redesign**
- Permissions: **Contents → Read and write**. Nothing else.
- Copy → `CMS_GITHUB_TOKEN`. This is the only GitHub credential in the system; it lives in Azure App Settings.

### 3. Deploy
```bash
cd cms-backend && cp .env.example .env     # fill in the values above
./deploy-azure.sh                           # same free App Service plan as the join API
```
It prints the health check and the redirect URI to confirm in step 1.

### 4. Switch the site over
`docs/admin/config.yml` already points at `https://ghf-cms.azurewebsites.net` (`backend: gitea`,
`base_url`, `api_root`). Rebuild and push; staff can sign in as soon as the deploy is live.

## Daily use
- **CMS:** `/admin/` → *Sign in* → Microsoft account picker → done. Pages, Blog, Staff, Site Text.
- **Visual text editor:** `/admin/edit.html` uses the same sign-in (sign in at `/admin/` once).
- Saves publish to the live site in about a minute (the GitHub Action builds and deploys as before).

## Local development
```bash
cd cms-backend && CMS_PUBLIC_URL=http://localhost:4500 python3 server.py
```
With `.env` filled in, add `http://localhost:4500/auth/callback` as a second redirect URI in the
Entra app, and set `base_url`/`api_root` in `config.yml` to `http://localhost:4500` while testing.
Without Microsoft configured you can still use **Work with Local Repository** on the `/admin/`
screen, which edits files on disk with no login.

## Operations
- Health: `GET /healthz` reports whether GitHub and Microsoft are configured.
- Rotate the GitHub token or Microsoft secret: update the App Setting, restart. Rotate
  `CMS_SESSION_SECRET` to sign everyone out.
- Logs: `az webapp log tail -g ghf-join-rg -n ghf-cms`.
