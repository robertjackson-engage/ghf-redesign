#!/usr/bin/env python3
"""
GHF Online Join — cart-style enrollment with IntelliPay.

PAYMENT MODEL (two distinct stages, per GHF requirements):

  Stage 1 — RECURRING METHOD ON FILE
      Lightbox in Store Only mode. Member may choose **bank draft (ACH)** or
      **credit card**. Nothing is charged. IntelliPay returns `custid`
      (the token) + `paymenttype` ("A" = ACH, "C" = card).
      -> token is handed to GHF's billing/member-management system nightly.

  Stage 2 — TODAY'S TOTAL (one-time)
      Charged immediately. **Card only — ACH is not accepted up front.**
        • If the recurring method is a CARD -> offer one-click reuse of that
          saved token (card_payment with custid).
        • If the recurring method is ACH   -> member must supply a card for
          today; a second Lightbox opens with ACH disabled.

Card data never touches this server (PCI SAQ-A) — see AGENTS.md §1a.
"""
import os, json, uuid, hmac, hashlib, base64, csv, io, datetime
import urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = "https://robertjackson-engage.github.io/ghf-redesign/assets/img/"
def _pick_public_logo():
    try:
        import urllib.request
        urllib.request.urlopen(urllib.request.Request(PAGES + "ghf-logo.png", method="HEAD"), timeout=4)
        return PAGES + "ghf-logo.png"
    except Exception:
        return PAGES + "header-logo.jpg"
PUBLIC_LOGO_URL = _pick_public_logo()
DB   = os.path.join(HERE, "members.json")
PORT = int(os.environ.get("PORT", "4400"))
TAX  = 0.07   # Alachua County sales tax applied to dues

def load_env():
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("="); os.environ.setdefault(k.strip(), v.strip())
load_env()

MERCHANT_KEY = os.environ.get("IPAY_MERCHANT_KEY", "")
API_KEY      = os.environ.get("IPAY_API_KEY", "")
AUTH_KEY     = os.environ.get("IPAY_AUTH_KEY", "")
BEARER       = os.environ.get("IPAY_BEARER", "")
IPAY_HOST    = os.environ.get("IPAY_HOST", "test.cpteller.com")
TERMINAL_URL = f"https://{IPAY_HOST}/api/custapi.cfc?method=autoterminal"
WEBAPI_URL   = f"https://{IPAY_HOST}/api/26/webapi.cfc"

CLUBS = ["GHF Main — 4820 W Newberry Rd (open 24/7)",
         "GHF Women — 2441 NW 43rd St (women only)",
         "GHF Tioga — 12830 SW 1st Ln, Newberry"]

PLANS = {
  "24mo": {"name":"24-Month Agreement","startFee":49.00,"dues":29.99,"badge":"BEST VALUE",
           "note":"After 24 months dues drop to $20.99 + tax."},
  "12mo": {"name":"12-Month Agreement","startFee":49.00,"dues":29.99,"badge":"",
           "note":"After 12 months stays $29.99 + tax, renews month-to-month."},
  "m2m":  {"name":"Month-to-Month","startFee":149.00,"dues":29.99,"badge":"MOST FLEXIBLE",
           "note":"Cancel anytime with 30 days' notice."},
}
ADDONS = {
  "pt3":   {"name":"3 Personal Training sessions","price":149.00,"oneTime":True},
  "towel": {"name":"Towel service","price":5.00,"oneTime":False},
}

def db_read():
    try: return json.load(open(DB))
    except Exception: return {}
def db_write(d): json.dump(d, open(DB,"w"), indent=2)

def totals(plan_key, addon_keys):
    """Cart math: what's due today vs what recurs."""
    p = PLANS[plan_key]
    lines = [{"label": f"{p['name']} — starting fee", "amount": p["startFee"]},
             {"label": "First dues installment",      "amount": p["dues"]}]
    recurring = p["dues"]
    for k in addon_keys or []:
        a = ADDONS.get(k)
        if not a: continue
        if a["oneTime"]: lines.append({"label": a["name"], "amount": a["price"]})
        else: recurring += a["price"]; lines.append({"label": f"{a['name']} (first period)", "amount": a["price"]})
    sub = round(sum(l["amount"] for l in lines), 2)
    tax = round(sub * TAX, 2)
    return {"lines": lines, "subtotal": sub, "tax": tax, "dueToday": round(sub+tax,2),
            "recurring": round(recurring,2), "recurringWithTax": round(recurring*(1+TAX),2)}

def fetch_terminal():
    if not (MERCHANT_KEY and API_KEY) and not BEARER:
        return False, "IntelliPay credentials not configured (.env)."
    body = urllib.parse.urlencode({"merchantkey":MERCHANT_KEY,"apikey":API_KEY}).encode()
    req = urllib.request.Request(TERMINAL_URL, data=body, method="POST",
          headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r: txt = r.read().decode("utf-8","replace")
    except Exception as e: return False, f"IntelliPay request failed: {e}"
    if "Authentication Failed" in txt:
        return False, (f"IntelliPay rejected the credentials on {IPAY_HOST}. Confirm the "
                       "merchantkey/apikey belong to this merchant and Lightbox is enabled.")
    return True, txt

def webapi(method, **params):
    data = {k:v for k,v in params.items() if v not in (None,"")}
    headers = {"Content-Type":"application/x-www-form-urlencoded"}
    if BEARER: data["apikey"]=BEARER; headers["Authorization"]=f"Bearer {BEARER}"
    else: data["merchantkey"]=MERCHANT_KEY; data["apikey"]=API_KEY
    req = urllib.request.Request(f"{WEBAPI_URL}?method={method}",
          data=urllib.parse.urlencode(data).encode(), method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r: raw=r.read().decode("utf-8","replace")
    except Exception as e: return {"ok":False,"error":f"{method}: {e}"}
    try: return {"ok":True,"data":json.loads(raw)}
    except Exception: return {"ok":True,"raw":raw[:600]}

def approved(res):
    try:
        st=(res.get("data") or {}).get("status")
        return str(st).lstrip("-").isdigit() and int(st)>0
    except Exception: return False

class H(BaseHTTPRequestHandler):
    # The GHF website (GitHub Pages / ghfc.com) calls this API from another origin.
    # JOIN_ALLOWED_ORIGINS: comma-separated list, or "*" (default for dev).
    def _cors(self):
        allowed = os.environ.get("JOIN_ALLOWED_ORIGINS", "*")
        origin = self.headers.get("Origin", "")
        if allowed == "*" or origin in [a.strip() for a in allowed.split(",")]:
            self.send_header("Access-Control-Allow-Origin", origin if origin and allowed != "*" else "*")
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.send_header("Content-Length","0"); self.end_headers()
    def _send(self,c,b,ct="application/json"):
        b=b.encode() if isinstance(b,str) else b
        self.send_response(c); self.send_header("Content-Type",ct); self._cors()
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def _j(self,c,o): self._send(c,json.dumps(o,indent=2))
    def _body(self):
        n=int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n).decode("utf-8","replace") if n else ""
    def log_message(self,*a): pass

    def logo_url(self):
        """Public https URL of the GHF logo for the IntelliPay banner."""
        if os.environ.get("IPAY_LOGO_URL"):
            return os.environ["IPAY_LOGO_URL"]
        https = getattr(self.server, "scheme", "http") == "https" or \
                self.headers.get("X-Forwarded-Proto", "").lower() == "https"      # App Service terminates TLS
        if https:   # we are reachable over https: serve our own copy
            host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host", "localhost:4443")
            return f"https://{host}/static/ghf-logo.png"
        return PUBLIC_LOGO_URL                                    # plain-http dev: use the hosted copy

    def _static(self, path):
        import mimetypes
        root = os.path.realpath(os.path.join(HERE, "static"))
        full = os.path.realpath(os.path.join(root, path[len("/static/"):]))
        if not full.startswith(root + os.sep) or not os.path.isfile(full):
            return self._j(404, {"error": "not found"})
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        with open(full, "rb") as fh:
            return self._send(200, fh.read(), ctype)

    def do_GET(self):
        u=urllib.parse.urlparse(self.path); path=u.path
        if path in ("/","/join"):
            page = open(os.path.join(HERE,"join.html"),encoding="utf-8").read()
            # Documented Lightbox pattern: the autoterminal response (scripts, styles,
            # short-lived tokens) is placed in <head> at page load, so window.load
            # runs intellipay.initialize() natively. Fresh tokens on every page view.
            ok, blob = fetch_terminal()
            inject = blob if ok else f'<script>window.__ipayError={json.dumps(blob)};</script>'
            # Logo for the Lightbox banner. The frame (https, test.cpteller.com) refuses data: URIs and
            # mixed content, so this must be an https URL it can fetch.
            inject += f'<script>window.__ghfLogo={json.dumps(self.logo_url())};</script>'
            page = page.replace("<!--IPAY_TERMINAL-->", inject, 1)
            return self._send(200, page.encode("utf-8"), "text/html")
        if path.startswith("/static/"):
            return self._static(path)
        if path=="/api/catalog":
            return self._j(200,{"clubs":CLUBS,"plans":PLANS,"addons":ADDONS,"taxRate":TAX})
        if path=="/api/quote":
            q=urllib.parse.parse_qs(u.query)
            plan=q.get("plan",["24mo"])[0]
            add=[a for a in q.get("addons",[""])[0].split(",") if a]
            if plan not in PLANS: return self._j(400,{"error":"unknown plan"})
            return self._j(200, totals(plan, add))
        if path=="/api/terminal":
            ok,out=fetch_terminal()
            if not ok: return self._j(502,{"ok":False,"error":out})
            out += f'<script>window.__ghfLogo={json.dumps(self.logo_url())};</script>'
            return self._send(200,out,"text/html")
        if path.startswith("/api/member/"):
            m=db_read().get(path.rsplit("/",1)[-1]); return self._j(200 if m else 404, m or {"error":"not found"})
        if path=="/api/export":
            q=urllib.parse.parse_qs(u.query); want=q.get("date",[""])[0] or datetime.date.today().isoformat()
            rows=[]
            for m in db_read().values():
                r=m.get("recurring") or {}
                if not r.get("token"): continue
                day=(r.get("vaultedAt") or m.get("created") or "")[:10]
                if want!="all" and day!=want: continue
                t=m.get("today") or {}
                rows.append({"member_id":m["memberId"],"recurring_token":r["token"],
                  "recurring_method":"ACH" if r.get("type")=="A" else "CARD",
                  "recurring_hint":r.get("hint",""),"recurring_amount":m.get("recurringWithTax",""),
                  "first_name":m.get("firstName",""),"last_name":m.get("lastName",""),
                  "email":m.get("email",""),"phone":m.get("phone",""),
                  "plan":m.get("plan",""),"plan_name":m.get("planName",""),
                  "home_club":m.get("club",""),"due_today_charged":t.get("amount",""),
                  "today_payment_id":t.get("paymentId",""),"today_approved":t.get("approved",""),
                  "vaulted_at":r.get("vaultedAt","")})
            cols=list(rows[0].keys()) if rows else ["member_id","recurring_token","recurring_method"]
            buf=io.StringIO(); w=csv.DictWriter(buf,fieldnames=cols); w.writeheader(); w.writerows(rows)
            os.makedirs(os.path.join(HERE,"exports"),exist_ok=True)
            fn=f"ghf-cardonfile-{want}.csv"
            open(os.path.join(HERE,"exports",fn),"w",newline="").write(buf.getvalue())
            d=buf.getvalue().encode()
            self.send_response(200); self.send_header("Content-Type","text/csv")
            self.send_header("Content-Disposition",f'attachment; filename="{fn}"')
            self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d); return
        return self._j(404,{"error":"not found"})

    def do_POST(self):
        path=urllib.parse.urlparse(self.path).path; raw=self._body()
        def body():
            try: return json.loads(raw or "{}")
            except Exception: return None

        # ---- create the cart/member record
        if path=="/api/member":
            d=body()
            if d is None: return self._j(400,{"error":"invalid JSON"})
            miss=[f for f in ("firstName","lastName","email","plan","club") if not d.get(f)]
            if miss: return self._j(400,{"error":"missing: "+", ".join(miss)})
            if d["plan"] not in PLANS: return self._j(400,{"error":"unknown plan"})
            t=totals(d["plan"], d.get("addons"))
            mid="GHF-"+uuid.uuid4().hex[:10].upper()
            db=db_read()
            db[mid]={"memberId":mid,"status":"cart","plan":d["plan"],"planName":PLANS[d["plan"]]["name"],
              "addons":d.get("addons",[]),"club":d["club"],
              "firstName":d["firstName"],"lastName":d["lastName"],"email":d["email"],
              "phone":d.get("phone",""),"dueToday":t["dueToday"],
              "recurringWithTax":t["recurringWithTax"],"quote":t,
              "recurring":None,"today":None,
              "created":datetime.datetime.utcnow().isoformat()+"Z"}
            db_write(db); return self._j(201, db[mid])

        # ---- STAGE 1: store the recurring method (ACH or card) — no charge
        if path=="/api/recurring-method":
            d=body() or {}
            mid,custid=d.get("memberId"),d.get("custid")
            if not mid or not custid: return self._j(400,{"error":"memberId and custid required"})
            db=db_read(); rec=db.get(mid)
            if not rec: return self._j(404,{"error":"unknown memberId"})
            ptype=(d.get("paymenttype") or "C").upper()
            rec["recurring"]={"token":str(custid),"type":ptype,
              "method":"ACH (bank draft)" if ptype=="A" else "Credit card",
              "hint":d.get("methodhint",""),
              "vaultedAt":datetime.datetime.utcnow().isoformat()+"Z"}
            rec["status"]="recurring_on_file"; db_write(db)
            return self._j(200,{"ok":True,"memberId":mid,"token":str(custid),
              "type":ptype,"method":rec["recurring"]["method"],"hint":d.get("methodhint",""),
              "canReuseForToday": ptype=="C",   # ACH not accepted for the up-front charge
              "dueToday":rec["dueToday"]})

        # ---- STAGE 2a: charge today's total to the SAVED CARD token
        if path=="/api/charge-today":
            d=body() or {}
            mid=d.get("memberId"); db=db_read(); rec=db.get(mid)
            if not rec: return self._j(404,{"error":"unknown memberId"})
            r=rec.get("recurring") or {}
            if not r.get("token"): return self._j(400,{"error":"no payment method on file yet"})
            if r.get("type")!="C":
                return self._j(400,{"error":"Bank draft can't be used for today's payment — a credit card is required."})
            amt=float(d.get("amount") or rec["dueToday"])
            res=webapi("card_payment", custid=r["token"], amount=f"{amt:.2f}", invoice=mid)
            ok=approved(res)
            rec["today"]={"amount":amt,"method":"saved card","token":r["token"],
              "approved":ok,"paymentId":(res.get("data") or {}).get("status"),
              "result":res,"at":datetime.datetime.utcnow().isoformat()+"Z"}
            rec["status"]="enrolled" if ok else "today_payment_failed"; db_write(db)
            return self._j(200,{"ok":True,"approved":ok,"memberId":mid,"amount":amt,"result":res})

        # ---- STAGE 2b: today's total paid with a DIFFERENT card (recurring was ACH)
        if path=="/api/today-card":
            d=body() or {}
            mid=d.get("memberId"); db=db_read(); rec=db.get(mid)
            if not rec: return self._j(404,{"error":"unknown memberId"})
            rec["today"]={"amount":float(d.get("amount") or rec["dueToday"]),
              "method":"new card","token":str(d.get("custid") or ""),
              "hint":d.get("methodhint",""),"approved":bool(d.get("approved",True)),
              "paymentId":d.get("status"),"at":datetime.datetime.utcnow().isoformat()+"Z"}
            rec["status"]="enrolled"; db_write(db)
            return self._j(200,{"ok":True,"memberId":mid,"today":rec["today"]})

        if path=="/api/postback":
            d={k:v[0] for k,v in urllib.parse.parse_qs(raw).items()}
            db=db_read(); rec=db.get(d.get("account") or d.get("invoice") or "")
            if rec:
                rec.setdefault("postbacks",[]).append(d); db_write(db)
            open(os.path.join(HERE,"postbacks.log"),"a").write(json.dumps(d)+"\n")
            return self._send(200,"OK","text/plain")
        return self._j(404,{"error":"not found"})

if __name__=="__main__":
    print(f"GHF cart-style join  →  http://localhost:{PORT}")
    print(f"IntelliPay {IPAY_HOST} | auth: {'bearer' if BEARER else ('merchantkey+apikey' if API_KEY else 'MISSING')}")
    ok,msg=fetch_terminal(); print("Lightbox auth:", "✅ OK" if ok else f"❌ {msg[:110]}")
    BIND = os.environ.get("BIND", "0.0.0.0" if os.environ.get("WEBSITE_SITE_NAME") else "127.0.0.1")  # App Service → all interfaces
    ThreadingHTTPServer((BIND,PORT),H).serve_forever()
