#!/usr/bin/env python3
"""
GHF CMS backend — lets staff edit the site with their Microsoft work login, no GitHub accounts.

What it is
----------
Sveltia CMS (docs/admin) speaks to Git hosts through a small HTTP API. This service pretends to be
one of those hosts (Gitea-compatible), but behind it:

  • Sign-in is Microsoft Entra ID (the club's Microsoft 365 tenant). We are the OAuth "provider"
    the CMS talks to (PKCE); we hand off to Microsoft and come back with a session token.
  • Every read/write is performed against GitHub with ONE token held here (CMS_GITHUB_TOKEN).
    Editors never see or hold a GitHub credential.
  • Writes are allowed ONLY under the content folders (content/, docs/assets/img/). Code, the build
    and the deploy pipeline cannot be touched from the portal, whoever is signed in.
  • Every commit is attributed to the editor (name + email from Microsoft) in the commit message
    and author fields, so the history still shows who changed what.

Endpoints
---------
  Auth (Sveltia PKCE):  GET  /login/oauth/authorize    → redirect to Microsoft
                        GET  /auth/callback            → back from Microsoft → redirect to CMS with ?code
                        POST /login/oauth/access_token → {access_token}
  Gitea-compatible API under /api/v1 (see GITEA_* handlers).
  Editor save:          POST /publish  {files:[{path,content}], message}   (visual text editor)
  Health:               GET  /healthz

Environment (.env locally, App Settings on Azure)
-------------------------------------------------
  CMS_GITHUB_TOKEN   fine-grained token, repo ghf-redesign, Contents: read/write   (REQUIRED)
  CMS_REPO           robertjackson-engage/ghf-redesign
  CMS_BRANCH         main
  MS_TENANT_ID       Entra tenant id (or "organizations")
  MS_CLIENT_ID       Entra app registration client id
  MS_CLIENT_SECRET   its client secret
  CMS_PUBLIC_URL     this service's https URL (e.g. https://ghf-cms.azurewebsites.net)
  CMS_ALLOWED_ORIGINS comma list of CMS origins, e.g. https://robertjackson-engage.github.io
  CMS_ALLOWED_DOMAINS comma list of email domains allowed to edit, e.g. ghfc.com (empty = any
                      account in the tenant)
  CMS_SESSION_SECRET random string used to sign session tokens
"""
import os, re, json, time, hmac, hashlib, base64, secrets, urllib.parse, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env():
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
PORT = int(os.environ.get("PORT", "4500"))
GITHUB_TOKEN = os.environ.get("CMS_GITHUB_TOKEN", "")
REPO = os.environ.get("CMS_REPO", "robertjackson-engage/ghf-redesign")
BRANCH = os.environ.get("CMS_BRANCH", "main")
TENANT = os.environ.get("MS_TENANT_ID", "organizations")
MS_CLIENT_ID = os.environ.get("MS_CLIENT_ID", "")
MS_CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET", "")
PUBLIC_URL = os.environ.get("CMS_PUBLIC_URL", f"http://localhost:{PORT}").rstrip("/")
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in os.environ.get("CMS_ALLOWED_ORIGINS", "http://localhost:4173").split(",") if o.strip()]
ALLOWED_DOMAINS = [d.strip().lower() for d in os.environ.get("CMS_ALLOWED_DOMAINS", "").split(",") if d.strip()]
SESSION_SECRET = os.environ.get("CMS_SESSION_SECRET", "") or secrets.token_hex(32)
SESSION_TTL = 12 * 3600
WRITABLE = ("content/", "docs/assets/img/")          # the only paths the portal may change
MAX_FILE = 15 * 1024 * 1024
OWNER, REPO_NAME = REPO.split("/")

# ----------------------------------------------------------------------------- helpers
def b64url(b): return base64.urlsafe_b64encode(b).decode().rstrip("=")
def b64url_dec(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign_session(payload):
    body = b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = b64url(hmac.new(SESSION_SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_session(token):
    try:
        body, sig = token.split(".", 1)
        good = b64url(hmac.new(SESSION_SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, good):
            return None
        p = json.loads(b64url_dec(body))
        return p if p.get("exp", 0) > time.time() else None
    except Exception:
        return None


# auth codes handed to the CMS after Microsoft login: code -> (session_token, code_challenge, exp)
_codes = {}
# login state: state -> (cms_redirect_uri, cms_state, code_challenge, exp)
_logins = {}


def _gc():
    now = time.time()
    for d in (_codes, _logins):
        for k in [k for k, v in d.items() if v[-1] < now]:
            d.pop(k, None)


def http(url, method="GET", headers=None, body=None, form=False, raw=False):
    h = {"User-Agent": "ghf-cms-backend"}
    h.update(headers or {})
    data = None
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode(); h["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw_b = r.read()
            return r.status, (raw_b if raw else (json.loads(raw_b) if raw_b else {})), dict(r.headers)
    except urllib.error.HTTPError as e:
        raw_b = e.read()
        try: j = json.loads(raw_b)
        except Exception: j = {"message": raw_b.decode("utf-8", "replace")[:300]}
        return e.code, j, dict(e.headers)


def gh(path, method="GET", body=None, raw=False, accept="application/vnd.github+json"):
    return http(f"https://api.github.com{path}", method,
                {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": accept, "X-GitHub-Api-Version": "2022-11-28"},
                body, raw=raw)


def writable(path):
    p = path.lstrip("/")
    return ".." not in p.split("/") and any(p.startswith(w) for w in WRITABLE)


# ----------------------------------------------------------------------------- handler
class H(BaseHTTPRequestHandler):
    server_version = "ghf-cms/1"

    def log_message(self, *a): pass

    # ---- plumbing
    def _origin_ok(self):
        o = (self.headers.get("Origin") or "").rstrip("/")
        return o in ALLOWED_ORIGINS or (not o)

    def _cors(self):
        o = (self.headers.get("Origin") or "").rstrip("/")
        if o in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", o)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Max-Age", "600")

    def _send(self, code, body=b"", ctype="application/json", extra=None):
        if isinstance(body, (dict, list)): body = json.dumps(body).encode()
        elif isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self._cors()
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def _redirect(self, url):
        self.send_response(302); self.send_header("Location", url); self.send_header("Content-Length", "0"); self.end_headers()

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try: return json.loads(raw) if raw else {}
        except Exception: return {}

    def _user(self):
        """Editor from the Authorization header (Sveltia sends 'token <t>'; the editor sends 'Bearer <t>')."""
        a = self.headers.get("Authorization", "")
        tok = a.split(" ", 1)[1].strip() if " " in a else ""
        return verify_session(tok) if tok else None

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.send_header("Content-Length", "0"); self.end_headers()

    # ---- routing
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query)); p = u.path
        if p == "/healthz": return self._send(200, {"ok": True, "repo": REPO, "branch": BRANCH, "github": bool(GITHUB_TOKEN), "microsoft": bool(MS_CLIENT_ID)})
        if p == "/login/oauth/authorize": return self.auth_start(q)
        if p == "/auth/callback": return self.auth_callback(q)
        if p.startswith("/api/v1/"): return self.api(p[len("/api/v1"):], q, "GET")
        self._send(404, {"message": "not found"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path); p = u.path
        if p == "/login/oauth/access_token": return self.auth_token()
        if p == "/publish": return self.publish()
        if p.startswith("/api/v1/"): return self.api(p[len("/api/v1"):], dict(urllib.parse.parse_qsl(u.query)), "POST")
        self._send(404, {"message": "not found"})

    # ---- Microsoft sign-in, exposed to the CMS as a PKCE OAuth provider
    def auth_start(self, q):
        _gc()
        redirect_uri, state, challenge = q.get("redirect_uri", ""), q.get("state", ""), q.get("code_challenge", "")
        if not (redirect_uri and state and challenge) or urllib.parse.urlparse(redirect_uri).scheme not in ("http", "https"):
            return self._send(400, "Bad request", "text/plain")
        if (urllib.parse.urlparse(redirect_uri).scheme + "://" + urllib.parse.urlparse(redirect_uri).netloc) not in ALLOWED_ORIGINS:
            return self._send(403, "This site is not allowed to use the GHF CMS.", "text/plain")
        if not MS_CLIENT_ID:
            return self._send(503, "Microsoft sign-in is not configured on the server.", "text/plain")
        ours = secrets.token_urlsafe(24)
        _logins[ours] = (redirect_uri, state, challenge, time.time() + 600)
        params = urllib.parse.urlencode({
            "client_id": MS_CLIENT_ID, "response_type": "code", "response_mode": "query",
            "redirect_uri": f"{PUBLIC_URL}/auth/callback", "scope": "openid profile email User.Read",
            "state": ours, "prompt": "select_account",
        })
        self._redirect(f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/authorize?{params}")

    def auth_callback(self, q):
        _gc()
        login = _logins.pop(q.get("state", ""), None)
        if not login:
            return self._send(400, "Sign-in expired. Close this window and try again.", "text/plain")
        cms_redirect, cms_state, challenge, _ = login
        if "error" in q:
            return self._redirect(f"{cms_redirect}?{urllib.parse.urlencode({'error': q.get('error_description', q['error']), 'state': cms_state})}")
        st, tok, _ = http(f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token", "POST", body={
            "client_id": MS_CLIENT_ID, "client_secret": MS_CLIENT_SECRET, "grant_type": "authorization_code",
            "code": q.get("code", ""), "redirect_uri": f"{PUBLIC_URL}/auth/callback", "scope": "openid profile email User.Read",
        }, form=True)
        if st != 200:
            return self._send(502, f"Microsoft sign-in failed: {tok.get('error_description', st)}", "text/plain")
        st, me, _ = http("https://graph.microsoft.com/v1.0/me", headers={"Authorization": f"Bearer {tok['access_token']}"})
        if st != 200:
            return self._send(502, "Could not read your Microsoft profile.", "text/plain")
        email = (me.get("mail") or me.get("userPrincipalName") or "").lower()
        if ALLOWED_DOMAINS and email.split("@")[-1] not in ALLOWED_DOMAINS:
            return self._send(403, f"{email} is not allowed to edit the GHF site.", "text/plain")
        session = sign_session({"sub": me.get("id"), "name": me.get("displayName") or email, "email": email,
                                "login": email.split("@")[0], "exp": int(time.time() + SESSION_TTL)})
        code = secrets.token_urlsafe(24)
        _codes[code] = (session, challenge, time.time() + 300)
        self._redirect(f"{cms_redirect}?{urllib.parse.urlencode({'code': code, 'state': cms_state})}")

    def auth_token(self):
        _gc()
        b = self._body()
        entry = _codes.pop(b.get("code", ""), None)
        if not entry:
            return self._send(400, {"error": "invalid_grant", "error_description": "Unknown or expired code"})
        session, challenge, _ = entry
        verifier = b.get("code_verifier", "")
        expect = b64url(hashlib.sha256(verifier.encode()).digest())
        if not hmac.compare_digest(expect, challenge):
            return self._send(400, {"error": "invalid_grant", "error_description": "PKCE verification failed"})
        self._send(200, {"access_token": session, "token_type": "bearer", "expires_in": SESSION_TTL})

    # ---- Gitea-compatible API (what Sveltia's 'gitea' backend calls), backed by GitHub
    def api(self, path, q, method):
        if path == "/version":
            return self._send(200, {"version": "1.24.0"})
        user = self._user()
        if not user:
            return self._send(401, {"message": "Please sign in"})
        if path == "/settings/api":
            return self._send(200, {"default_paging_num": 30, "max_response_items": 50, "default_max_blob_size": 10485760, "default_max_response_size": 104857600})
        if path == "/user":
            return self._send(200, {"id": int(hashlib.sha1(user["sub"].encode()).hexdigest()[:8], 16), "login": user["login"],
                                    "full_name": user["name"], "email": user["email"], "avatar_url": "", "html_url": "", "bot": False})
        pre = f"/repos/{OWNER}/{REPO_NAME}"
        if not path.startswith(pre):
            return self._send(404, {"message": "not found"})
        rest = path[len(pre):]

        if rest == "":
            return self._send(200, {"id": 1, "name": REPO_NAME, "full_name": REPO, "default_branch": BRANCH,
                                    "html_url": f"https://github.com/{REPO}", "permissions": {"admin": False, "push": True, "pull": True}})
        if rest.startswith("/branches/"):
            br = urllib.parse.unquote(rest[len("/branches/"):])
            st, j, _ = gh(f"/repos/{REPO}/branches/{urllib.parse.quote(br, safe='')}")
            if st != 200: return self._send(404, {"message": "branch not found"})
            c = j["commit"]
            return self._send(200, {"name": br, "commit": {"id": c["sha"], "message": c["commit"]["message"]}})
        if rest.startswith("/git/trees/"):
            ref = urllib.parse.unquote(rest[len("/git/trees/"):])
            st, j, _ = gh(f"/repos/{REPO}/git/trees/{urllib.parse.quote(ref, safe='')}?recursive=1")
            if st != 200: return self._send(st, j)
            tree = [{"path": t["path"], "type": t["type"], "sha": t["sha"], "size": t.get("size", 0), "mode": t["mode"]}
                    for t in j.get("tree", []) if t["type"] == "blob" and (t["path"].startswith(WRITABLE) or t["path"] in (".gitattributes",))]
            return self._send(200, {"sha": j["sha"], "tree": tree, "truncated": False})
        if rest == "/file-contents" and method == "POST":
            ref = q.get("ref", BRANCH); files = (self._body().get("files") or [])[:50]
            out = []
            for f in files:
                st, j, _ = gh(f"/repos/{REPO}/contents/{urllib.parse.quote(f)}?ref={urllib.parse.quote(ref)}")
                if st == 200 and isinstance(j, dict):
                    out.append({"path": f, "sha": j["sha"], "size": j["size"], "encoding": "base64", "content": j.get("content", "").replace("\n", "")})
            return self._send(200, out)
        if rest.startswith("/contents/") and method == "GET":
            fp = urllib.parse.unquote(rest[len("/contents/"):])
            st, j, _ = gh(f"/repos/{REPO}/contents/{urllib.parse.quote(fp)}?ref={urllib.parse.quote(q.get('ref', BRANCH))}")
            if st != 200 or not isinstance(j, dict): return self._send(404, {"message": "not found"})
            return self._send(200, {"path": fp, "sha": j["sha"], "size": j["size"], "encoding": "base64", "content": j.get("content", "").replace("\n", "")})
        if rest.startswith("/raw/"):
            fp = urllib.parse.unquote(rest[len("/raw/"):])
            st, data, hdr = gh(f"/repos/{REPO}/contents/{urllib.parse.quote(fp)}?ref={urllib.parse.quote(q.get('ref', BRANCH))}", raw=True, accept="application/vnd.github.raw+json")
            return self._send(st, data if st == 200 else {"message": "not found"}, "text/plain; charset=utf-8")
        if rest.startswith("/media/"):
            parts = rest[len("/media/"):].split("/", 1)
            if len(parts) != 2: return self._send(404, {"message": "not found"})
            br, fp = urllib.parse.unquote(parts[0]), urllib.parse.unquote(parts[1])
            st, data, hdr = gh(f"/repos/{REPO}/contents/{urllib.parse.quote(fp)}?ref={urllib.parse.quote(br)}", raw=True, accept="application/vnd.github.raw+json")
            import mimetypes
            return self._send(st, data if st == 200 else b"", mimetypes.guess_type(fp)[0] or "application/octet-stream")
        if rest == "/commits":
            st, j, _ = gh(f"/repos/{REPO}/commits?sha={urllib.parse.quote(q.get('sha', BRANCH))}&path={urllib.parse.quote(q.get('path', ''))}&per_page={min(int(q.get('limit', 30) or 30), 100)}")
            if st != 200: return self._send(st, j)
            return self._send(200, [{"sha": c["sha"], "created": c["commit"]["author"]["date"],
                                     "commit": {"message": c["commit"]["message"], "author": c["commit"]["author"]},
                                     "author": {"login": (c.get("author") or {}).get("login", ""), "avatar_url": (c.get("author") or {}).get("avatar_url", "")}} for c in j])
        if rest == "/contents" and method == "POST":
            return self.commit(self._body(), user)
        self._send(404, {"message": "not found"})

    # ---- the one place anything is written: a single commit on behalf of the editor
    def commit(self, b, user):
        files = b.get("files") or []
        if not files: return self._send(400, {"message": "no files"})
        for f in files:
            for key in ("path", "from_path"):
                if f.get(key) and not writable(f[key]):
                    return self._send(403, {"message": f"'{f[key]}' is outside the editable content folders. Code and site settings can only be changed by a developer."})
        # current head
        st, ref, _ = gh(f"/repos/{REPO}/git/ref/heads/{urllib.parse.quote(BRANCH, safe='')}")
        if st != 200: return self._send(502, {"message": "Could not read the repository"})
        head = ref["object"]["sha"]
        st, headc, _ = gh(f"/repos/{REPO}/git/commits/{head}")
        base_tree = headc["tree"]["sha"]
        entries = []
        for f in files:
            op = f.get("operation", "update")
            if op == "delete":
                entries.append({"path": f["path"], "mode": "100644", "type": "blob", "sha": None}); continue
            raw = base64.b64decode(f.get("content", "") or "")
            if len(raw) > MAX_FILE: return self._send(413, {"message": "File too large"})
            st, blob, _ = gh(f"/repos/{REPO}/git/blobs", "POST", {"content": base64.b64encode(raw).decode(), "encoding": "base64"})
            if st != 201: return self._send(502, {"message": "Could not store file"})
            entries.append({"path": f["path"], "mode": "100644", "type": "blob", "sha": blob["sha"]})
            if f.get("from_path") and f["from_path"] != f["path"]:
                entries.append({"path": f["from_path"], "mode": "100644", "type": "blob", "sha": None})
        st, tree, _ = gh(f"/repos/{REPO}/git/trees", "POST", {"base_tree": base_tree, "tree": entries})
        if st != 201: return self._send(502, {"message": f"Could not build change: {tree.get('message')}"})
        author = {"name": user["name"], "email": user["email"]}
        msg = (b.get("message") or "Update content").rstrip() + f"\n\nEdited in the GHF CMS by {user['name']} <{user['email']}>"
        st, commit, _ = gh(f"/repos/{REPO}/git/commits", "POST", {"message": msg, "tree": tree["sha"], "parents": [head], "author": author, "committer": author})
        if st != 201: return self._send(502, {"message": "Could not create commit"})
        st, upd, _ = gh(f"/repos/{REPO}/git/refs/heads/{urllib.parse.quote(BRANCH, safe='')}", "PATCH", {"sha": commit["sha"], "force": False})
        if st != 200: return self._send(409, {"message": "Someone else published at the same moment. Reload and try again."})
        saved = [{"path": e["path"], "sha": e["sha"]} for e in entries if e["sha"]]
        self._send(201, {"commit": {"sha": commit["sha"], "created": commit["committer"]["date"]}, "files": saved})

    # ---- the visual text editor's save
    def publish(self):
        user = self._user()
        if not user: return self._send(401, {"error": "Please sign in"})
        b = self._body(); files = b.get("files") or []
        payload = {"message": b.get("message") or "Site text update",
                   "files": [{"operation": "update", "path": f["path"], "content": base64.b64encode(f["content"].encode("utf-8")).decode()} for f in files if isinstance(f.get("content"), str)]}
        return self.commit(payload, user)


if __name__ == "__main__":
    bind = "0.0.0.0" if os.environ.get("WEBSITE_SITE_NAME") else "127.0.0.1"
    missing = [k for k, v in {"CMS_GITHUB_TOKEN": GITHUB_TOKEN, "MS_CLIENT_ID": MS_CLIENT_ID, "MS_CLIENT_SECRET": MS_CLIENT_SECRET}.items() if not v]
    print(f"GHF CMS backend → {PUBLIC_URL}  (repo {REPO}@{BRANCH}; origins {ALLOWED_ORIGINS})")
    if missing: print("  NOT CONFIGURED:", ", ".join(missing), "— see .env.example")
    ThreadingHTTPServer((bind, PORT), H).serve_forever()
