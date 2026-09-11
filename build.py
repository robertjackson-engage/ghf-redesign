#!/usr/bin/env python3
# GHF redesign — static site generator
import os, time, json

OUT = os.path.join(os.path.dirname(__file__), "docs")
IMG = "assets/img"

# ============================================================ CMS content engine
CONTENT = os.path.join(os.path.dirname(__file__), "content")
import glob as _glob, re as _re, json as _json

def _parse_md(path):
    raw = open(path, encoding="utf-8").read(); meta, body = {}, raw
    m = _re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, _re.S)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, _, v = line.partition(":"); meta[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2)
    return meta, _md_to_html(body.strip())

def _md_to_html(md):
    md = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if _re.match(r"^\s*[-*]\s+", ln):
            items = []
            while i < len(lines) and _re.match(r"^\s*[-*]\s+", lines[i]):
                items.append("<li>" + _inline(_re.sub(r"^\s*[-*]\s+", "", lines[i])) + "</li>"); i += 1
            out.append("<ul>" + "".join(items) + "</ul>"); continue
        h = _re.match(r"^(#{1,4})\s+(.*)$", ln)
        if h:
            lvl = len(h.group(1)); out.append(f"<h{lvl+1}>{_inline(h.group(2))}</h{lvl+1}>"); i += 1; continue
        if ln.strip() == "":
            i += 1; continue
        para = [ln]; i += 1
        while i < len(lines) and lines[i].strip() and not _re.match(r"^(#{1,4}\s|\s*[-*]\s)", lines[i]):
            para.append(lines[i]); i += 1
        out.append("<p>" + _inline(" ".join(para)) + "</p>")
    return "\n".join(out)

def _inline(t):
    t = _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = _re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    t = _re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t

def load_collection(folder):
    items = []
    for p in _glob.glob(os.path.join(CONTENT, folder, "*.md")):
        meta, body = _parse_md(p)
        meta["_slug"] = os.path.splitext(os.path.basename(p))[0]; meta["_body"] = body
        items.append(meta)
    items.sort(key=lambda m: m.get("date", ""), reverse=True)
    return items

def cms_img(path):
    return (path or "").lstrip("/") or f"assets/img/Echo_GroupFit_Outdoor_Classes_Fun_Classes_2021.jpg"

def fmt_date(d):
    months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m = _re.match(r"(\d{4})-(\d{2})-(\d{2})", d or "")
    return f"{months[int(m.group(2))]} {int(m.group(3))}, {m.group(1)}" if m else (d or "")
# ============================================================ end CMS content engine

# Trainers come from the CMS (content/staff/*.md) so staff can maintain the roster
# at /admin. Loaded here rather than beside POSTS because pt_body is built at
# module level far above that, and load_collection() sorts by "date" — which staff
# records don't have — so re-sort explicitly.
TRAINERS = sorted(load_collection("staff"),
                  key=lambda t: (t.get("order", ""), t.get("name", "")))


def _facts(t):
    out = []
    for key, label in (("hometown", "Hometown"), ("education", "Education"),
                       ("certifications", "Certifications"), ("hobbies", "Hobbies")):
        if t.get(key):
            out.append([label, t[key]])
    return out


# Keap / Infusionsoft endpoint for personal training leads. Taken from the hosted
# form behind the embed script (form id d33934f0…, "Web Form submitted"). That form's
# own markup writes the .app host; we use .com to match the two proven integrations on
# the same pv228 tenant. Note it carries only three hidden inputs — the ghfc.com-sourced
# forms add inf_IntegrationName / inf_CallName / inf_api_enabled for their custom-action
# setup, which this one does not use.
KEAP_PT_ACTION = "https://pv228.infusionsoft.com/app/form/process/d33934f006555af5a3ee939461149a73"
KEAP_PT_XID = "d33934f006555af5a3ee939461149a73"
KEAP_PT_VERSION = "1.70.0.1003601"

# Keap ships the same two spam traps on its forms; they must be present and left empty.
KEAP_TRAPS = ('<input type="text" name="inf_eGYY1p7FcL3TD8b6" value="" tabindex="-1" autocomplete="off" style="display:none !important">'
                 '<input type="text" name="inf-sbt" value="" tabindex="-1" autocomplete="off" style="display:none !important">')


def trainers_section(num):
    if not TRAINERS:
        return ""
    cards = ""
    for t in TRAINERS:
        specs = [x.strip() for x in (t.get("specialties") or "").split(",") if x.strip()]
        payload = _json.dumps({
            "name": t.get("name", ""), "role": t.get("role", "Personal Trainer"),
            "photo": cms_img(t.get("photo")), "quote": t.get("_body", ""),
            "specialties": specs, "facts": _facts(t),
        }, ensure_ascii=False).replace('"', "&quot;")
        cards += (f'<button class="card trainer-card" type="button" data-trainer="{payload}">'
                  f'<div class="card__media"><img src="{cms_img(t.get("photo"))}" '
                  f'alt="{t.get("name","")}, personal trainer at GHF" loading="lazy">'
                  f'<div class="card__label"><h3>{t.get("name","")}</h3>'
                  f'<span class="go">Read profile &rarr;</span></div></div>'
                  f'<div class="card__below"><p>{", ".join(specs[:3])}</p></div></button>')
    return f"""
<section class="section" id="trainers">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Meet our trainers</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">The people you'll actually <span class="serif">work with</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:36ch">{len(TRAINERS)} certified trainers, each with their own specialties. Click anyone to see their background.</p>
    </div>
    <div class="card-grid card-grid--4" data-stagger>{cards}</div>
  </div>
</section>

<div class="trainer-panel" role="dialog" aria-modal="true" aria-label="Trainer profile">
  <div class="trainer-panel__scrim"></div>
  <div class="trainer-panel__inner">
    <button class="trainer-panel__close" type="button" aria-label="Close profile">&#10005;</button>
    <div class="trainer-panel__media"><img data-t-photo src="" alt=""></div>
    <div class="trainer-panel__body">
      <h3 data-t-name></h3>
      <span class="trainer-panel__role" data-t-role></span>
      <blockquote class="trainer-quote" data-t-quote></blockquote>
      <div class="trainer-tags" data-t-tags></div>
      <dl class="trainer-facts" data-t-facts></dl>

      <div class="trainer-panel__request">
        <p class="eyebrow">Train with <span data-t-request></span></p>
        <form class="form-grid trainer-panel__form" method="post" action="{KEAP_PT_ACTION}" accept-charset="UTF-8">
          <input type="hidden" name="inf_form_xid" value="{KEAP_PT_XID}">
          <input type="hidden" name="inf_form_name" value="Web Form submitted">
          <input type="hidden" name="infusionsoft_version" value="{KEAP_PT_VERSION}">
          <input type="hidden" name="inf_custom_TrainerName" data-t-trainer value="">
          <input type="hidden" name="inf_custom_SelectAProgram" value="Free Assessment">
          {KEAP_TRAPS}
          <div class="field"><input type="text" name="inf_field_FirstName" id="tp-first" placeholder=" " required><label for="tp-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="tp-last" placeholder=" " required><label for="tp-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="tp-email" placeholder=" " required><label for="tp-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="tp-phone" placeholder=" " required><label for="tp-phone">Phone</label></div>
          <button class="btn field--full" type="submit" style="justify-content:center">Request This Trainer <span class="arr">&rarr;</span></button>
        </form>
      </div>
    </div>
  </div>
</div>
"""


V = str(int(time.time()))  # cache-bust CSS/JS on every build
# Join API (intellipay/server.py). Override per environment: GHF_JOIN_API=https://join.ghfc.com python3 build.py
import json as _json
JOIN_API_JSON = _json.dumps(os.environ.get("GHF_JOIN_API", "https://ghf-join-demo.azurewebsites.net"))

# Modern GHF mark — the raised-arms figure from the original logo, geometrized
def mark_svg(cls):
    # small circular "i" glyph (used only inside the AI chat orb)
    return f"""<svg class="{cls}" viewBox="0 0 64 64" fill="none" aria-hidden="true">
<circle cx="32" cy="13" r="7" fill="currentColor"/>
<path d="M13 24 L32 37 L51 24" stroke="currentColor" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M32 37 L32 56" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>
<path d="M14 56 A 26 26 0 0 0 50 56" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.45"/>
</svg>"""

LOGO_MARK = "assets/img/brand/logo-mark.png"      # Gainesville H&F lockup, no tagline (header/menu)
LOGO_FULL = "assets/img/brand/logo-lockup.png"    # full lockup with tagline (footer)

# intrinsic pixel sizes, so the aspect-ratio hint matches the file and the
# browser reserves the right box before the image loads
LOGO_SIZES = {LOGO_MARK: (1000, 400), LOGO_FULL: (1000, 451)}

def brand_logo(src=LOGO_MARK, cls=""):
    w, h = LOGO_SIZES[src]
    return (f'<img class="brand__logo {cls}" src="{src}?v={V}" '
            f'alt="Gainesville Health &amp; Fitness" width="{w}" height="{h}" />')

NAV = [
    ("Classes", "group-fitness.html"),
    ("Training", "training.html"),
    ("Amenities", "amenities.html"),
    ("Locations", "locations.html"),
]

MENU = [
    ("Join Online", "join.html"),
    ("Free All-Access Pass", "ghf-pass.html#claim"),
    ("Class Schedule", "group-fitness.html#schedule"),
    ("Locations", "locations.html"),
    ("GHF Main", "main-center.html"),
    ("GHF Women", "womens-center.html"),
    ("GHF Tioga", "tioga-center.html"),
    ("Amenities", "amenities.html"),
    ("J-Bar Smoothie Cafe", "jbar.html"),
    ("Court Sports &mdash; Basketball &amp; Volleyball", "court-sports.html"),
    ("Echo Outdoor Pavilion", "echo.html"),
    ("Pool &amp; Aqua Center", "pool.html"),
    ("Post Workout Recovery", "recovery.html"),
    ("Chill Studio &mdash; HydroMassage &amp; CryoLounge+", "chill.html"),
    ("Strength Training Equipment", "strength-training.html"),
    ("Cardio Selections", "cardio.html"),
    ("Hot Yoga", "hot-yoga.html"),
    ("Kids Club", "kids-club.html"),
    ("Personal Training", "personal-training.html"),
    ("Pilates", "pilates.html"),
    ("Hyrox", "hyrox.html"),
    ("CrossFit", "crossfit.html"),
    ("X-Force Fat Loss", "xforce.html"),
    ("Team Strong Training", "team-strong-training.html"),
    ("Why GHF", "why-ghf.html"),
    ("Home", "index.html"),
    ("Weight Loss", "weight-loss.html"),
    ("Blog", "blog.html"),
    ("Contact", "contact.html"),
    ("TRIBE Team Training", "tribe.html"),
]


def head(title, desc):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" href="assets/img/favicon.ico?v={V}" sizes="16x16 32x32 48x48">
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/favicon-32.png?v={V}">
<link rel="icon" type="image/png" sizes="16x16" href="assets/img/favicon-16.png?v={V}">
<link rel="icon" type="image/png" sizes="192x192" href="assets/img/favicon-192.png?v={V}">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png?v={V}">
<link rel="stylesheet" href="assets/css/main.css?v={V}">
<script>(function(){{try{{
  if(sessionStorage.getItem("ghf-intro"))document.documentElement.classList.add("no-preloader");
}}catch(e){{}}}})();</script>
</head>
<body>
<div class="preloader" aria-hidden="true">
  <img class="preloader__logo" src="assets/img/brand/logo-mark.png?v={V}" alt="Gainesville Health &amp; Fitness" width="1000" height="400" />
  <div class="preloader__bar"><i></i></div>
  <div class="preloader__count">0</div>
</div>
"""


def header_html(active=""):
    links = ""
    for label, href in NAV:
        cls = ' class="is-active"' if href == active else ""
        links += f'<a href="{href}"{cls}>{label}</a>'
    menu_links = ""
    for i, (label, href) in enumerate(MENU, 1):
        menu_links += f'<a href="{href}"><span class="idx">{i:02d}</span>{label}</a>'
    return f"""
<header class="site-header">
  <div class="site-header__inner">
    <a class="brand" href="index.html" aria-label="Gainesville Health &amp; Fitness — home">
      {brand_logo()}
    </a>
    <nav class="nav-desktop" aria-label="Primary">{links}</nav>
    <div class="header-cta">
      <a class="btn btn--solid btn--sm" href="join.html#start">Join Online</a>
      <a class="btn btn--solid btn--sm" href="ghf-pass.html#claim">Free Pass</a>
      <a class="btn btn--solid btn--sm header-pricing" href="contact.html#pricing">Get Pricing</a>
      <button class="menu-toggle" aria-expanded="false" aria-label="Open menu">
        <span>Menu</span>
        <span class="menu-toggle__icon"><i></i><i></i></span>
      </button>
    </div>
  </div>
</header>

<div class="menu-overlay" role="dialog" aria-label="Site menu">
  <div class="menu-overlay__grid">
    <nav class="menu-list" aria-label="All pages">{menu_links}</nav>
    <aside class="menu-side">
      <div class="menu-side__pass">
        <p>"There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired."</p>
        <a class="btn btn--solid btn--sm" href="ghf-pass.html#claim">Free All-Access Pass <span class="arr">→</span></a>
      </div>
      <div class="menu-side__group">
        <h6>More at GHF</h6>
        <a href="training.html">Signature Training</a>
        <a href="crossfit.html">CrossFit</a>
        <a href="xforce.html">X-Force Body</a>
        <a href="seniors.html">Seniors</a>
        <a href="sports-activities.html">Sports Activities</a>
        <a href="special-needs-fitness.html">FIT For All</a>
        <a href="bring-a-guest.html">Bring a Guest</a>
        <a href="member-savings.html">Member Savings</a>
        <a href="faq.html">FAQ</a>
      </div>
      <div class="menu-side__group">
        <h6>Visit</h6>
        <a href="locations.html">GHF Main — 4820 W Newberry Road</a>
        <a href="locations.html">GHF Women — 2441 NW 43rd Street</a>
        <a href="locations.html">GHF Tioga — 12830 SW 1st Lane</a>
      </div>
      <div class="menu-side__group">
        <h6>Talk to us</h6>
        <a href="tel:3523774955">(352) 377-4955</a>
        <a href="mailto:memberservices@ghfc.com">memberservices@ghfc.com</a>
      </div>
    </aside>
  </div>
</div>

<main id="mainContent">
"""


def footer_html():
    return f"""
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="site-footer__top">
      <div class="site-footer__brand">
        <a class="brand brand--footer" href="index.html">
          {brand_logo(LOGO_FULL)}
        </a>
        <p>The gym that's best at helping beginners — with staff to guide your journey. One membership, three locations.</p>
        <div class="socials">
          <a href="https://www.facebook.com/gainesvillefit" aria-label="Facebook">FB</a>
          <a href="https://www.instagram.com/gainesvillehealth" aria-label="Instagram">IG</a>
          <a href="https://www.youtube.com/user/GHFCadmin" aria-label="YouTube">YT</a>
          <a href="https://www.linkedin.com/company/gainesville-health-&amp;-fitness" aria-label="LinkedIn">IN</a>
        </div>
      </div>
      <div>
        <h5>Explore</h5>
        <div class="site-footer__links">
          <a href="join.html">Join Online</a>
          <a href="ghf-pass.html#claim">Free All-Access Pass</a>
          <a href="blog.html">Blog</a>
          <a href="why-ghf.html">Why GHF</a>
          <a href="group-fitness.html">Group Classes</a>
          <a href="personal-training.html">Personal Training</a>
          <a href="strength-training.html">Strength Training</a>
          <a href="amenities.html">Amenities</a>
          <a href="recovery.html">Recovery</a>
          <a href="chill.html">Chill Studio</a>
          <a href="chill-cancel.html">Cancel Chill</a>
          <a href="jbar.html">J-Bar Smoothies</a>
          <a href="court-sports.html">Court Sports</a>
          <a href="echo.html">Echo Outdoor Pavilion</a>
          <a href="kids-club.html">Kid's Club</a>
          <a href="member-savings.html">Member Savings</a>
          <a href="bring-a-guest.html">Bring a Guest</a>
          <a href="faq.html">FAQ</a>
        </div>
      </div>
      <div>
        <h5>Programs</h5>
        <div class="site-footer__links">
          <a href="training.html">Signature Training</a>
          <a href="hot-yoga.html">Hot Yoga</a>
          <a href="pilates.html">Pilates</a>
          <a href="tribe.html">TRIBE Team Training</a>
          <a href="crossfit.html">CrossFit</a>
          <a href="xforce.html">X-Force Body</a>
          <a href="seniors.html">Seniors</a>
          <a href="pool.html">Pool &amp; Aqua Center</a>
          <a href="locations.html">Locations &amp; Hours</a>
        </div>
      </div>
      <div class="site-footer__contact">
        <h5>Stay connected with GHF</h5>
        <a class="tel" href="tel:3523774955">(352) 377-4955</a>
        <a href="mailto:memberservices@ghfc.com">memberservices@ghfc.com</a>
        <a href="contact.html">Email Directory</a>
        <form class="news-form" data-demo>
          <input type="email" placeholder="Sign up for our newsletter" aria-label="Email address" required>
          <button type="submit">Join</button>
        </form>
      </div>
    </div>
  </div>
  <div class="site-footer__mega" aria-hidden="true">GAINESVILLE</div>
  <div class="wrap">
    <div class="site-footer__bottom">
      <span>©2026 Gainesville Health &amp; Fitness. All Rights Reserved.</span>
      <div class="legal">
        <a href="contact.html">Contact Us</a>
        <a href="contact.html">Careers</a>
        <a href="contact.html">Privacy Policy</a>
        <a href="contact.html">Accessibility</a>
      </div>
    </div>
  </div>
</footer>
<script src="assets/js/main.js?v={V}"></script>
<script src="assets/js/chat-config.js?v={V}"></script>
<script src="assets/js/chat.js?v={V}" defer></script>
</body>
</html>
"""


def hero(kicker, lines, sub="", img=None, video=None, poster=None, crumb=None,
         actions=None, meta=None, promo=None, page=False, hero_cls=""):
    lns = ""
    for i, ln in enumerate(lines):
        lns += f'<span class="ln"><span style="transition-delay:{0.12 + i * 0.09:.2f}s">{ln}</span></span>'
    media = ""
    if video:
        media = f'<video src="{video}" poster="{poster or ""}" autoplay muted loop playsinline></video>'
    elif img:
        media = f'<img src="{img}" alt="" fetchpriority="high">'
    acts = ""
    if actions:
        acts = '<div class="hero__actions">'
        for a in actions:
            label, href, solid = a[0], a[1], a[2]
            extra = (" " + a[3]) if len(a) > 3 else ""
            cls = ("btn btn--solid" if solid else "btn") + extra
            acts += f'<a class="{cls}" href="{href}">{label} <span class="arr">→</span></a>'
        acts += "</div>"
    crumb_html = ""
    if crumb:
        crumb_html = f'<div class="hero__crumb"><div><a href="index.html">Home</a> &nbsp;/&nbsp; {crumb}</div></div>'
    meta_html = ""
    if meta:
        meta_html = '<div class="hero__meta">' + "".join(f"<span>{m}</span>" for m in meta) + "</div>"
    promo_html = ""
    if promo:
        subs = "".join(f"<span>{s}</span>" for s in promo[1:])
        promo_html = ('\n    <div class="hero__promo">'
                      f'<p class="hero__promo-lead">{promo[0]}</p>'
                      f'<div class="hero__promo-sub">{subs}</div></div>')
    sub_html = f'<p class="hero__sub">{sub}</p>' if sub else ""
    return f"""
<section class="hero{' hero--page' if page else ''}{' ' + hero_cls if hero_cls else ''}">
  <div class="hero__media">{media}</div>
  {crumb_html}
  <div class="hero__inner">
    <p class="hero__kicker">{kicker}</p>
    <h1 class="hero__title">{lns}</h1>
    {sub_html}{promo_html}
    {acts}
  </div>
  {meta_html}
  <div class="hero__scroll" aria-hidden="true"></div>
</section>
"""


def marquee(words, accent=False, ghost=False):
    cls = "marquee"
    if accent:
        cls += " marquee--accent"
    if ghost:
        cls += " marquee--ghost"
    seg = "".join(f"<span>{w} <i>●</i></span>" for w in words)
    return f"""
<div class="{cls}" aria-hidden="true">
  <div class="marquee__track">{seg}</div>
  <div class="marquee__track">{seg}</div>
</div>
"""


def stats_band(items, light=False):
    cells = ""
    for num, sfx, label in items:
        cells += f"""
      <div class="stat">
        <div class="stat__num"><span data-count="{num}">0</span><span class="sfx">{sfx}</span></div>
        <div class="stat__label">{label}</div>
      </div>"""
    return f"""
<section class="section--flush{' section--light' if light else ''}">
  <div class="stats"><div class="wrap" style="padding:0"><div class="stats__grid">{cells}</div></div></div>
</section>
"""


def split(eyebrow, num, title, paras, img, alt, rev=False, cta=None, tag=None, light=False,
          wide=False, name=None, href=None):
    """name= promotes the program name to the display heading and demotes `title`
    beneath it. href= makes the whole block a link — which means the CTA must stop
    being an <a>, since nesting anchors is invalid and browsers unnest it."""
    body_paras = "".join(f'<p class="body-copy">{p}</p>' for p in paras)
    if cta:
        cta_inner = (f'<span class="inline-link">{cta[0]} →</span>' if href
                     else f'<a class="inline-link" href="{cta[1]}">{cta[0]} →</a>')
        cta_html = f'<div class="split__cta">{cta_inner}</div>'
    else:
        cta_html = ""
    tag_html = f'<span class="tag">{tag}</span>' if tag else ""

    if name:
        heading = (f'<h2 class="h-display split__name">{name}</h2>'
                   f'<p class="h-mid split__lead">{title}</p>')
    else:
        heading = f'<h2 class="h-display" style="font-size:clamp(30px,3.8vw,58px)">{title}</h2>'

    tag_open = f'<a class="split split--link{{rev}}" href="{href}">' if href else '<div class="split{rev}">'
    tag_open = tag_open.format(rev=' split--rev' if rev else '')
    tag_close = "</a>" if href else "</div>"

    return f"""
<section class="section{' section--light' if light else ''}">
  <div class="wrap">
    {tag_open}
      <div class="split__media{' split__media--wide' if wide else ''} reveal-img">
        <img src="{img}" alt="{alt}" loading="lazy">{tag_html}
      </div>
      <div class="split__body">
        <p class="eyebrow">{eyebrow}</p>
        {heading}
        <div class="reveal">{body_paras}{cta_html}</div>
      </div>
    {tag_close}
  </div>
</section>
"""


def cta_band(title_html, text, img, primary=("Claim Your Free Pass", "ghf-pass.html#claim"),
             secondary=("Free All-Access Pass", "ghf-pass.html#claim")):
    sec = ""
    if secondary:
        sec = f'<a class="btn" href="{secondary[1]}">{secondary[0]} <span class="arr">→</span></a>'
    return f"""
<section class="cta-band">
  <div class="cta-band__media"><img src="{img}" alt="" loading="lazy"></div>
  <div class="wrap">
    <h2 class="reveal">{title_html}</h2>
    <p class="reveal">{text}</p>
    <div class="hero__actions reveal">
      <a class="btn btn--solid" href="{primary[1]}">{primary[0]} <span class="arr">→</span></a>
      {sec}
    </div>
  </div>
</section>
"""


def form_section(sec_id, num, eyebrow, title_html, text, btn, fields=None, light=True,
                 extra="", select=None):
    fields = fields or [
        ("text", "first", "First name"), ("text", "last", "Last name"),
        ("email", "email", "Email address"), ("tel", "phone", "Phone"),
    ]
    f_html = ""
    for ftype, name, label in fields:
        f_html += f"""
        <div class="field"><input type="{ftype}" name="{name}" id="{sec_id}-{name}" placeholder=" " required><label for="{sec_id}-{name}">{label}</label></div>"""
    sel_html = ""
    if select:
        s_name, s_label, s_opts = select
        opts = "".join(f"<option>{o}</option>" for o in s_opts)
        sel_html = f"""
          <div class="field field--full">
            <select name="{s_name}" id="{sec_id}-{s_name}" aria-label="{s_label}">
              <option value="">&nbsp;</option>{opts}
            </select>
            <label for="{sec_id}-{s_name}">{s_label}</label>
          </div>"""
    return f"""
<section class="section{' section--light' if light else ''}" id="{sec_id}">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">{eyebrow}</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">{title_html}</h2>
        <p class="lede reveal" style="margin-top:28px">{text}</p>
        {extra}
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" data-demo>
          {f_html}{sel_html}
          <div class="field field--full">
            <select name="location" id="{sec_id}-loc" aria-label="Preferred location">
              <option value="">&nbsp;</option>
              <option>GHF Main</option>
              <option>GHF Women</option>
              <option>GHF Tioga</option>
            </select>
            <label for="{sec_id}-loc">Preferred location</label>
          </div>
          <button class="btn {'btn--dark' if light else ''} field--full" type="submit" style="justify-content:center">{btn} <span class="arr">→</span></button>
        </form>
        <p class="form-note">We will contact you via phone, email, or text. There is no charge, no obligation and no risk.</p>
      </div>
    </div>
  </div>
</section>
"""


def embed(src, title, tall=False, allow_yt=False, cls="", eager=False):
    """Responsive third-party frame. Styling lives in .embed / .embed--tall / .embed--fixed."""
    extra = ('allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
             'gyroscope; picture-in-picture; web-share" allowfullscreen ') if allow_yt else ""
    mods = (" embed--tall" if tall else "") + ((" " + cls) if cls else "")
    return (f'<div class="embed{mods}">'
            f'<iframe src="{src}" title="{title}" loading="{"eager" if eager else "lazy"}" {extra}'
            f'referrerpolicy="strict-origin-when-cross-origin"></iframe></div>')


GX_ENDPOINT = "https://perch-platform-api.onrender.com/public/gx/schedule?orgSlug=ghf"


def schedule_block(sec_id, eyebrow, heading, blurb, room=None):
    """The Perch-backed class schedule. `room` scopes it to a single studio
    (schedule.js filters on data-room and hides the location chips and the
    now-single-option studio select)."""
    room_attr = f' data-room="{room}"' if room else ""
    return f"""<section class="section section--light" id="{sec_id}">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">{eyebrow}</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">{heading}</h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">{blurb}</p>
    </div>
    <div class="gx" data-endpoint="{GX_ENDPOINT}"{room_attr}>

      <div class="gx__filters">
        <div class="gx__search">
          <input type="search" id="gxSearch" placeholder="Search class name or instructor" aria-label="Search classes by name or instructor" autocomplete="off">
          <button type="button" class="gx__search-clear" aria-label="Clear search" hidden>&times;</button>
        </div>

        <div class="gx__chips" role="group" aria-label="Filter by location"></div>

        <div class="gx__selects">
          <label class="gx__select"><span>Type</span>
            <select id="gxType" aria-label="Filter by class type"><option value="">All types</option></select>
          </label>
          <label class="gx__select"><span>Studio</span>
            <select id="gxRoom" aria-label="Filter by studio"><option value="">All studios</option></select>
          </label>
          <label class="gx__select"><span>Day</span>
            <select id="gxDay" aria-label="Filter by day"><option value="">All days</option></select>
          </label>
          <label class="gx__select"><span>Instructor</span>
            <select id="gxInstructor" aria-label="Filter by instructor"><option value="">All instructors</option></select>
          </label>
        </div>

        <div class="gx__bar">
          <p class="gx__count" aria-live="polite"></p>
          <div class="gx__bar-actions">
            <button type="button" class="gx__now" hidden>Jump to now</button>
            <button type="button" class="gx__reset" hidden>Clear filters</button>
          </div>
        </div>
      </div>

      <div class="gx__status" role="status" aria-live="polite">
        <span class="gx__dots" aria-hidden="true"><i></i><i></i><i></i></span>
        <p>Loading this week&rsquo;s classes&hellip;</p>
      </div>

      <div class="gx__days"></div>

      <div class="gx-lb" role="dialog" aria-modal="true" aria-label="Instructor photo" hidden>
        <div class="gx-lb__scrim"></div>
        <div class="gx-lb__inner">
          <button type="button" class="gx-lb__close" aria-label="Close photo">&times;</button>
          <img class="gx-lb__img" src="" alt="">
          <p class="gx-lb__name"></p>
        </div>
      </div>

      <noscript>
        <p class="gx__noscript">Our class schedule needs JavaScript to load.
        You can view it directly at <a href="https://app.perchteams.com/public/gx/ghf" rel="noopener">app.perchteams.com</a>,
        or call us at <a href="tel:3523774955">(352) 377-4955</a>.</p>
      </noscript>
    </div>
  </div>
  <script src="assets/js/schedule.js?v={V}" defer></script>
</section>"""


def accordion(items, open_first=True):
    out = '<div class="acc reveal">'
    for i, (q, a) in enumerate(items):
        out += f"""
      <div class="acc__item{' is-open' if (open_first and i == 0) else ''}">
        <button class="acc__head" aria-expanded="{'true' if (open_first and i == 0) else 'false'}">
          <h3>{q}</h3><span class="acc__icon"></span>
        </button>
        <div class="acc__body" {'style="max-height:600px"' if (open_first and i == 0) else ''}><div class="acc__body-inner">{a}</div></div>
      </div>"""
    out += "</div>"
    return out


def rows_expand(items):
    """Numbered rows that open to a photo and fuller copy. Emits the class names
    main.js's accordion already binds (.acc / .acc__item / .acc__head / .acc__body),
    so no new JS — .acc--rows only restyles the heads as rows.

    Panel images carry explicit width/height on purpose: main.js sizes an open
    panel from body.scrollHeight at click time, and an unsized image that hasn't
    loaded yet measures ~0, which opens the panel clipped."""
    out = '<div class="acc acc--rows reveal">'
    for i, it in enumerate(items, 1):
        title, teaser, img, alt, w, h, body = it
        out += f"""
      <div class="acc__item">
        <button class="acc__head" aria-expanded="false">
          <span class="acc__idx">{i:02d}</span>
          <span class="acc__row-title">{title}</span>
          <span class="acc__row-desc">{teaser}</span>
          <span class="acc__icon"></span>
        </button>
        <div class="acc__body"><div class="acc__body-inner">
          <div class="acc__media"><img src="{img}" alt="{alt}" width="{w}" height="{h}" loading="lazy"></div>
          <div class="acc__text">{body}</div>
        </div></div>
      </div>"""
    out += "</div>"
    return out


SAVINGS = json.load(open(os.path.join(CONTENT, "member-savings.json"))) \
    if os.path.exists(os.path.join(CONTENT, "member-savings.json")) else []


def esc_attr(v):
    return (str(v or "").replace("&", "&amp;").replace('"', "&quot;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def savings_directory(items):
    """The Member Savings partner directory.

    Every business is rendered into the HTML — the category select and the search
    box only show and hide, so with JavaScript off this is still the complete,
    readable directory rather than an empty shell."""
    if not items:
        return ""
    cats = sorted({b["category"] for b in items}, key=str.lower)
    opts = "".join(f'<option value="{esc_attr(c)}">{c}</option>' for c in cats)

    cards = ""
    for b in items:
        logo = (f'<div class="biz__logo"><img src="{IMG}/savings/{b["logo"]}" alt="" '
                f'loading="lazy" decoding="async"></div>') if b.get("logo") else ""
        offers = "".join(f'<li>{o}</li>' for o in b["offers"])
        offers_html = f'<ul class="biz__offers">{offers}</ul>' if offers else ""
        meta = []
        if b.get("phone"):
            tel = _re.sub(r"[^0-9]", "", b["phone"])
            meta.append(f'<a href="tel:{tel}">{b["phone"]}</a>')
        if b.get("address"):
            meta.append(f'<span>{b["address"]}</span>')
        if b.get("website"):
            meta.append(f'<a href="{esc_attr(b["website"])}" target="_blank" rel="noopener">Visit website</a>')
        meta_html = f'<p class="biz__meta">{" <i>&middot;</i> ".join(meta)}</p>' if meta else ""
        # without a logo the body would otherwise land in the 74px logo column
        nologo = "" if b.get("logo") else " biz--nologo"
        cards += f"""
        <article class="biz{nologo}" data-cat="{esc_attr(b["category"])}" data-find="{esc_attr((b["name"] + " " + " ".join(b["offers"]) + " " + b["category"]).lower())}">
          {logo}
          <div class="biz__body">
            <p class="biz__cat">{b["category"]}</p>
            <h3 class="biz__name">{b["name"]}</h3>
            {offers_html}
            {meta_html}
          </div>
        </article>"""

    return f"""
<section class="section section--light" id="directory">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Participating businesses</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Where your card <span class="serif">works</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Show your GHF membership card to claim these offers. No coupons, no apps &mdash; just your card.</p>
    </div>

    <div class="sv" data-total="{len(items)}">
      <div class="sv__filters">
        <div class="sv__search">
          <input type="search" id="svSearch" placeholder="Search a business, an offer or a category" aria-label="Search participating businesses" autocomplete="off">
          <button type="button" class="sv__clear" aria-label="Clear search" hidden>&times;</button>
        </div>
        <label class="gx__select sv__cat"><span>Category</span>
          <select id="svCat" aria-label="Filter by category"><option value="">All categories</option>{opts}</select>
        </label>
        <div class="sv__bar">
          <p class="sv__count" aria-live="polite">{len(items)} businesses</p>
          <button type="button" class="sv__reset" hidden>Clear filters</button>
        </div>
      </div>
      <p class="sv__empty" hidden>No businesses match that search. <button type="button" class="gx__link" data-sv-reset>Clear it</button> to see all {len(items)}.</p>
      <div class="sv__grid">{cards}
      </div>
    </div>
  </div>
  <script src="assets/js/savings.js?v={V}" defer></script>
</section>
"""


def page(filename, title, desc, active, body):
    html = head(title, desc) + header_html(active) + body + footer_html()
    with open(os.path.join(OUT, filename), "w") as f:
        f.write(html)
    print("built", filename)


# ============================================================ CMS PAGE BUILDER
# Staff-editable pages: content/pages/*.json → rendered with the same design-
# system components as the hand-authored pages. New pages are created in the CMS.
def _accent(t):
    """Wrap *word* in the serif accent span used across headlines."""
    return _re.sub(r"\*([^*]+)\*", r'<span class="serif">\1</span>', t or "")


def _img_or_none(v):
    return cms_img(v) if v else None


def render_block(b):
    """Map one CMS block dict → HTML via the existing component helpers."""
    t = (b.get("type") or "").strip()
    if t == "hero":
        lines = [_accent(x) for x in (b.get("lines") or []) if x]
        actions = [(a.get("label", ""), a.get("href", "#"), bool(a.get("solid", True)))
                   for a in (b.get("actions") or []) if a.get("label")]
        return hero(
            b.get("kicker", ""), lines, sub=b.get("sub", ""),
            img=_img_or_none(b.get("image")), video=(b.get("video") or None),
            poster=_img_or_none(b.get("poster")), crumb=(b.get("crumb") or None),
            actions=(actions or None), meta=(b.get("meta") or None),
            page=not bool(b.get("tall")),
        )
    if t == "split":
        cta = (b["cta_label"], b.get("cta_href", "#")) if b.get("cta_label") else None
        return split(
            b.get("eyebrow", ""), b.get("num", ""), _accent(b.get("title", "")),
            (b.get("paragraphs") or []), cms_img(b.get("image")), b.get("alt", ""),
            rev=bool(b.get("reversed")), cta=cta, tag=(b.get("tag") or None),
            light=bool(b.get("light")), wide=bool(b.get("wide")),
        )
    if t == "stats":
        items = [(i.get("number", "0"), i.get("suffix", ""), i.get("label", ""))
                 for i in (b.get("items") or [])]
        return stats_band(items, light=bool(b.get("light")))
    if t == "cta":
        primary = (b.get("primary_label", "Claim Your Free Pass"),
                   b.get("primary_href", "contact.html#pricing"))
        secondary = ((b.get("secondary_label"), b.get("secondary_href", "#"))
                     if b.get("secondary_label") else None)
        return cta_band(_accent(b.get("title", "")), b.get("text", ""),
                        cms_img(b.get("image")), primary=primary, secondary=secondary)
    if t == "accordion":
        items = [(i.get("q", ""), _md_to_html(i.get("a", ""))) for i in (b.get("items") or [])]
        head_html = ""
        if b.get("title"):
            head_html = (f'<div class="cards-head"><div><p class="eyebrow">{b.get("eyebrow", "")}</p>'
                         f'<h2 class="h-display reveal" style="font-size:clamp(30px,3.8vw,58px)">'
                         f'{_accent(b.get("title", ""))}</h2></div></div>')
        return (f'\n<section class="section{" section--light" if b.get("light") else ""}">'
                f'<div class="wrap" style="max-width:960px">{head_html}{accordion(items)}</div></section>\n')
    if t == "marquee":
        return marquee((b.get("words") or []), accent=bool(b.get("accent")), ghost=bool(b.get("ghost")))
    if t == "form":
        return form_section(b.get("id", "lead"), b.get("num", "01"), b.get("eyebrow", ""),
                            _accent(b.get("title", "")), b.get("text", ""),
                            b.get("button", "Get Started"), light=bool(b.get("light", True)))
    if t == "checklist":
        lis = "".join(f"<li>{_inline(x)}</li>" for x in (b.get("items") or []) if x)
        return (f'\n<section class="section{" section--light" if b.get("light") else ""}">'
                f'<div class="wrap"><div class="intro-grid"><div>'
                f'<p class="eyebrow">{b.get("eyebrow", "")}</p>'
                f'<h2 class="h-display reveal">{_accent(b.get("title", ""))}</h2>'
                f'<p class="body-copy reveal" style="margin-top:26px">{b.get("text", "")}</p></div>'
                f'<div class="intro-grid__right reveal"><ul class="checklist">{lis}</ul></div>'
                f'</div></div></section>\n')
    if t == "richtext":
        eyebrow = (f'<p class="eyebrow">{b.get("eyebrow", "")}</p>'
                   if b.get("eyebrow") else "")
        title = (f'<h2 class="h-display reveal" style="font-size:clamp(30px,3.8vw,58px);margin-bottom:22px">'
                 f'{_accent(b.get("title", ""))}</h2>' if b.get("title") else "")
        body = _md_to_html(b.get("body", ""))
        return (f'\n<section class="section{" section--light" if b.get("light") else ""}">'
                f'<div class="wrap" style="max-width:820px">{eyebrow}{title}'
                f'<div class="reveal" style="font-size:16px;line-height:1.75">{body}</div></div></section>\n')
    return f"<!-- unknown block type: {t} -->"


def render_blocks(blocks):
    return "".join(render_block(b) for b in (blocks or []))


def load_pages():
    """Read content/pages/*.json into page dicts (filename, nav settings, blocks)."""
    items = []
    for p in sorted(_glob.glob(os.path.join(CONTENT, "pages", "*.json"))):
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print("!! skipping bad page JSON", os.path.basename(p), e)
            continue
        data["_slug"] = os.path.splitext(os.path.basename(p))[0]
        slug = (data.get("slug") or data["_slug"]).strip().replace(".html", "")
        data["_filename"] = slug + ".html"
        items.append(data)
    return items


# ============================================================ HOME
home_steps = f"""
<section class="section section--tight">
  <div class="wrap">
    <figure class="quote-band reveal">
      <span class="quote-band__mark">“</span>
      <blockquote>I lost 55lbs and found the confidence to keep it off.</blockquote>
      <figcaption>— Carol, GHF member</figcaption>
    </figure>
  </div>
</section>

<section class="section section--light">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Getting started is the easy part</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Your first visit, <span class="serif">mapped out</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:36ch">No contracts to sign, no sales pitch to survive. Just show up and see how it feels.</p>
    </div>
    <div class="steps reveal">
      <div class="step"><span class="step__num">01</span><h3><a href="ghf-pass.html#claim">Claim your free pass</a></h3><p>One day, full access, zero obligation. Every class, the pool, the sauna, the coaches — on us.</p></div>
      <div class="step"><span class="step__num">02</span><h3>Meet your coach</h3><p>A real human gives you the tour, learns your goal, and walks you through your first workout — so you're never guessing.</p></div>
      <div class="step"><span class="step__num">03</span><h3>Make it a habit</h3><p>A plan that fits your life, people who notice when you show up, and results you can see. That's how one visit becomes a routine.</p></div>
    </div>
  </div>
</section>
"""

home_body = hero(
    "Gainesville's most-loved gym — 45 years strong",
    ["Walk in unsure.", 'Walk out <span class="serif">stronger</span>.'],
    "Starting is the hardest part — so we made it the easiest. From your very first visit, a real coach walks the floor with you, builds your plan, and shows you the ropes. No guesswork. No intimidation. Just results.",
    video=f"assets/video/ghf-walkthrough.mp4",
    poster=f"{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg",
    actions=[
        ("Claim Your Free Fitness Pass", "ghf-pass.html#claim", True),
        ("See What's Inside", "amenities.html", False),
    ],
    meta=["Free coaching on every visit", "Open 24/7 at GHF Main", "900+ classes included"],
) + marquee(["Strength", "Cardio", "Hot Yoga", "Pilates", "Indoor Pool", "Sauna", "Recovery", "Fitness Classes", "Personal Training"]) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">The reason members stay</p>
        <h2 class="h-display reveal">Finally, a gym that<br>doesn't leave you <span class="serif">guessing</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">You'll never stand in the middle of the floor wondering what to do next. A coach shows you the beginner strength circuit, sets up every machine, and points you to the classes, pool, and recovery spaces that fit your goals — every time you come in, at no extra charge.</p>
        <p class="body-copy reveal">Most gyms hand you a key card and wish you luck. We hand you a team. It's the reason people who were nervous to start become members who never want to leave.</p>
        <div class="reveal"><a class="inline-link" href="why-ghf.html">See why people choose GHF →</a></div>
      </div>
    </div>
  </div>
</section>
""" + stats_band([
    (45, "+", "Years perfecting how beginners start"),
    (300, "", "Coaches on the floor to help you — free"),
    (900, "+", "Classes included, never an upcharge"),
    (3, "", "Locations, one membership, zero excuses"),
]) + f"""
<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Find what you'll love</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Every way to <span class="serif">move</span></h2>
      </div>
      <a class="inline-link reveal" href="group-fitness.html">View all classes →</a>
    </div>
    <div class="card-grid" data-stagger>
      <a class="card" href="strength-training.html">
        <div class="card__media"><img src="{IMG}/GHF_Benches_Free_Weight_Expansion_2025.jpg" alt="GHF Strength training benches" loading="lazy"><span class="card__num">01</span>
        <div class="card__label"><h3>Strength<br>Training</h3><span class="go">Explore →</span></div></div>
      </a>
      <a class="card" href="group-fitness.html">
        <div class="card__media"><img src="{IMG}/GHF_GroupFit_Les_Mills_Body_Pump_Squats.jpg" alt="Group fitness class at GHF" loading="lazy"><span class="card__num">02</span>
        <div class="card__label"><h3>Group<br>Classes</h3><span class="go">Explore →</span></div></div>
      </a>
      <a class="card" href="pool.html">
        <div class="card__media"><img src="{IMG}/GHF_Gainesville_Health_and_Fitness_Swimming_Pool_Aqua_Aquix.jpg" alt="Indoor lap pool at GHF" loading="lazy"><span class="card__num">03</span>
        <div class="card__label"><h3>Pool &amp;<br>Aqua Center</h3><span class="go">Explore →</span></div></div>
      </a>
      <a class="card" href="hot-yoga.html">
        <div class="card__media"><img src="{IMG}/GHF_Gainesville_Hot_Yoga_GHF_Yoga_Classes_Group_Fitness_Stretching_Flow_2025-10.jpg" alt="Hot yoga classes in Gainesville studio" loading="lazy"><span class="card__num">04</span>
        <div class="card__label"><h3>Hot<br>Yoga</h3><span class="go">Explore →</span></div></div>
      </a>
      <a class="card" href="cardio.html">
        <div class="card__media"><img src="{IMG}/Cardio_Running_Most_Cardio_in_Gainesville_Gym_2022.jpg" alt="Treadmill cardio equipment" loading="lazy"><span class="card__num">05</span>
        <div class="card__label"><h3>Cardio</h3><span class="go">Explore →</span></div></div>
      </a>
      <a class="card" href="recovery.html">
        <div class="card__media"><img src="{IMG}/Aqua_GHF_Aquix_Cold_Plunge_Cold_Therapy_Pool_2023_1.jpg" alt="Cold therapy pool at GHF Main" loading="lazy"><span class="card__num">06</span>
        <div class="card__label"><h3>Recovery</h3><span class="go">Explore →</span></div></div>
      </a>
    </div>
  </div>
</section>
""" + marquee(["New Leg Den", "The EndZone", "Functional Turf", "10,000 sq ft expansion"], ghost=True) + split(
    "New at GHF Main", "03",
    'Don\'t wait. Work out in the new <span class="serif">Leg Den</span>',
    ["Welcome to the gym near you with more ways to lift so you don't have to wait. Our brand new leg den at GHF Main has double the squat and deadlift platforms in a bigger studio (more than twice the size of the former leg den).",
     "Enjoy MORE of everything including amenities, classes, 3 locations, and hours — all for your best results. Try out all of our lifting spaces."],
    f"{IMG}/GHF_Leg_Den_Leg_Day_Exercise_Fitness_Squats_Deadlifts_2025-2.jpg",
    "Squat and deadlift platforms in the new Leg Den at GHF Main",
    cta=("Strength Training Options", "strength-training.html"), tag="GHF Main",
) + split(
    "Lower body, upgraded", "04",
    'The EndZone: your lower body\'s new <span class="serif">home turf</span>',
    ["A dedicated space packed with all the best equipment to target hips and glutes. Hip thrust platforms, belted squat platform, booty builder abductor, and glute hamstring developer (GHD).",
     "These muscles act as your body's powerhouse, stabilizing the pelvis to relieve lower back pain, improving your athletic \"explosiveness,\" and protecting your knees from injury during everyday movement."],
    f"{IMG}/GHF_Legs_Lower_Body_Workout_EndZone_Gainesville_Gyms_GHF_Main_Glutes_2025_3.jpg",
    "EndZone area at GHF Main with machines targeting glutes and hips",
    rev=True, cta=("More Ways To Lift", "strength-training.html"), tag="The EndZone",
) + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Recover like you mean it</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Soak away <span class="serif">the sore</span></h2>
      </div>
      <a class="inline-link reveal" href="recovery.html">More about recovery →</a>
    </div>
    <div class="card-grid card-grid--2" data-stagger>
      <div class="card">
        <div class="card__media card__media--wide"><img src="{IMG}/Aqua_GHF_Aquix_Hot_Tube_Pool_2023_1.jpg" alt="Friends in hot tub pool and spa area at Gainesville Health and Fitness" loading="lazy">
        <div class="card__label"><h3>The Hot Tub</h3></div></div>
        <div class="card__below"><p>Indulge in the therapeutic benefits as the hot water eases tension, promotes muscle relaxation, relieves pain, and improves sleep. Let the hot tub become your personal oasis of tranquility. Available at GHF Main and GHF Women — the Gainesville, FL gyms offering the most recovery options including cold plunge, hot tub, steam, pool, yoga and stretch. Included in every gym membership.</p></div>
      </div>
      <div class="card">
        <div class="card__media card__media--wide"><img src="{IMG}/Aqua_GHF_Aquix_Cold_Plunge_Cold_Therapy_Pool_2023_1.jpg" alt="Two people soaking in the cold therapy pool at GHF Main" loading="lazy">
        <div class="card__label"><h3>The Cold Plunge</h3></div></div>
        <div class="card__below"><p>Wake up your nervous system and feel alive again. Step into a transformative chill in our cold therapy pool that instantly triggers a powerful surge of endorphins and increased circulation. You'll hit the ultimate reset button on your stress levels, leaving GHF with a renewed sense of energy that caffeine simply can't match. Included in membership!</p></div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">When you're ready for more</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Go further with a <span class="serif">coach in your corner</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:34ch">Want faster results, real accountability, or a body that surprises you? Pick the program that fits your goal — your first session is free.</p>
    </div>
    <div class="rows reveal">
      <a class="row-item" href="personal-training.html">
        <span class="row-item__idx">01</span>
        <span class="row-item__title">Personal Training</span>
        <span class="row-item__desc">A certified trainer who knows your name, your history, and your goal — and takes it personally.</span>
        <span class="row-item__arrow">→</span>
      </a>
      <a class="row-item" href="xforce.html">
        <span class="row-item__idx">02</span>
        <span class="row-item__title">X-Force Body</span>
        <span class="row-item__desc">Shed fat with one or two short workouts a week. The busy person's secret weapon.</span>
        <span class="row-item__arrow">→</span>
      </a>
      <a class="row-item" href="pilates.html">
        <span class="row-item__idx">03</span>
        <span class="row-item__title">Pilates</span>
        <span class="row-item__desc">Stand taller, move easier, build a core that carries you — on the Reformer.</span>
        <span class="row-item__arrow">→</span>
      </a>
      <a class="row-item" href="crossfit.html">
        <span class="row-item__idx">04</span>
        <span class="row-item__title">CrossFit</span>
        <span class="row-item__desc">Camaraderie, competition, and results you'll want to brag about.</span>
        <span class="row-item__arrow">→</span>
      </a>
      <a class="row-item" href="tribe.html">
        <span class="row-item__idx">05</span>
        <span class="row-item__title">TRIBE Team Training</span>
        <span class="row-item__desc">Same crew, eight weeks, real accountability. Teams don't let you quit.</span>
        <span class="row-item__arrow">→</span>
      </a>
    </div>
  </div>
</section>

<section class="section section--flush">
  <div class="video-feature">
    <video src="assets/video/ghf-walkthrough.mp4" autoplay muted loop playsinline></video>
    <div class="video-feature__overlay"><span>Step inside<br>GHF Main</span></div>
  </div>
</section>
""" + home_steps + cta_band(
    'Your first day is <span class="serif">free</span>',
    "Full access for a day: every class, the pool, the sauna, the coaches — no charge, no obligation, no sales pitch. The only risk is falling in love with the place.",
    f"{IMG}/Echo_GroupFit_Outdoor_Classes_Fun_Classes_2021.jpg",
    secondary=("Join Online Today", "join.html#start"),
)

# ============================================================ WHY GHF
why_body = hero(
    "Why GHF",
    ["The gym you'll", 'actually <span class="serif">stick with</span>'],
    "Anyone can sell you a membership. GHF is engineered so you'll use yours — more coaching, more variety, more recovery, and more reasons to keep showing up than any gym in Gainesville.",
    img=f"{IMG}/Tioga_Carrie_Grotto_Arm_Cross_Facility_2022.jpg",
    crumb="Why GHF",
    actions=[("Free All-Access Pass", "ghf-pass.html#claim", True)],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="pillars" data-stagger>
      <div class="pillar"><span class="pillar__num">Your First Day</span><h3>A coach teaches you everything — you'll never feel lost on the floor</h3></div>
      <div class="pillar"><span class="pillar__num">Your Routine</span><h3>900+ classes, 3 clubs, 24/7 hours — skipping is harder than showing up</h3></div>
      <div class="pillar"><span class="pillar__num">Your Results</span><h3>Programs engineered for visible change, and a team that keeps you on track</h3></div>
      <div class="pillar"><span class="pillar__num">Your Life</span><h3>Free childcare, free coaching, a full recovery spa — built around real life</h3></div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">45 years of helping beginners</p>
        <h2 class="h-display reveal">You're going to feel <span class="serif">good</span> here</h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">Tired of not feeling your best? You're exactly who this place was built for. For 45 years, GHF has been designed around one person: the one walking in for the first time.</p>
        <p class="body-copy reveal">You'll feel it everywhere — in the layout that never makes you guess, the classes with a spot for every level, a private club just for women, and coaches hired for how well they teach, not how loud they yell. You get shown how to exercise — not just on day one, but every single visit.</p>
        <p class="body-copy reveal">And you just got 10,000 more square feet of it: free hot yoga in a state-of-the-art studio, a functional training turf, a new Personal Training Studio, double the leg studio and bench space, plus the EndZone — a whole zone for glutes and hips. More room to find your thing. More reasons to come back.</p>
      </div>
    </div>
  </div>
</section>
""" + marquee(["Better People", "Better Programs", "Better Facilities", "Better Benefits", "Better Members"], accent=True) + split(
    "Better People", "02",
    'A team of 300, on <span class="serif">your side</span>',
    ["Three hundred coaches, instructors and trainers learn your name, fix your form, and celebrate your wins — every visit, at no extra charge. You'll never wonder if you're doing it right, because someone's already walking over to help."],
    f"{IMG}/GHF_Careers_Floor_Instructor_Fitness_Jobs_Service.jpg",
    "GHF floor instructor helping a member",
    cta=("Contact Us", "contact.html"),
) + split(
    "Better Programs", "03",
    'Boredom is how routines <span class="serif">die</span>',
    ["So you'll never run out of new: basketball, lap swimming, 700+ classes from Zumba to yoga to cycle, and the area's deepest bench of cardio and strength equipment. There's hardly ever a wait — and never a reason to plateau."],
    f"{IMG}/GHF_Basketball_5.jpg",
    "Indoor basketball and volleyball court at GHF",
    rev=True, cta=("Fitness Programs", "group-fitness.html"),
) + split(
    "Better Facilities", "04",
    'A club for every version of <span class="serif">you</span>',
    ["The 24/7 flagship for early birds and night owls. A private, women-only club where you can fully be you. A family-friendly Tioga center with kids' programs. One membership opens all three — pick by mood, not by contract."],
    f"{IMG}/GHF_Tioga_Gainesville_Health_Gainesville_Gyms_TIoga_Strength_Gyms_Nearby_2026-2.jpg",
    "Strength training at GHF Tioga",
    cta=("See Our Gyms", "locations.html"),
) + split(
    "Better Benefits", "05",
    'Every excuse, <span class="serif">handled</span>',
    ["No time? Open 24/7. No sitter? Free Kid's Club. Wrong side of town? Three locations. Too sore? Hot tub, sauna and cold plunge are included. The membership is built to remove every reason you'd skip — so you don't."],
    f"{IMG}/Pool_at_GHF.jpg",
    "Pool at GHF — better gym benefits",
    rev=True, cta=("See the added benefits", "amenities.html"),
) + stats_band([
    (45, "", "Years of expertise"),
    (700, "+", "Group classes monthly"),
    (3, "", "Locations / 1 membership"),
    (24, "/7", "Hours at GHF Main"),
]) + f"""
<section class="section section--tight">
  <div class="wrap">
    <figure class="quote-band reveal">
      <span class="quote-band__mark">“</span>
      <blockquote>GHF is filled with people just like you, ready to make a change to live a better life.</blockquote>
      <figcaption>Better Members — Gainesville Health &amp; Fitness</figcaption>
    </figure>
  </div>
</section>
""" + cta_band(
    'Come feel it for <span class="serif">yourself</span>',
    "A day pass costs you nothing and shows you everything. Bring your gym clothes — leave the doubts at home.",
    f"{IMG}/GroupFit_Echo_Yoga_Class_Outdoor_Classes_2021.jpg",
)

# ============================================================ AMENITIES
amenities_body = hero(
    "Amenities",
    ["Everything you'd pay extra for,", '<span class="serif">included</span>'],
    "Hot yoga studio. Cold plunge. Sauna, steam and hot tub. A 75-foot pool. Free babysitting. Basketball. 900+ classes. Stop piecing together five subscriptions — one membership covers it all.",
    img=f"{IMG}/GHF_Aquix_Pool_2018.jpg",
    crumb="Amenities",
    actions=[("Try Our Amenities for Free", "ghf-pass.html#claim", True)],
    page=True,
) + f"""
<section class="section section--tight">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">A premium fitness experience</p>
        <h2 class="h-display reveal">Beyond the <span class="serif">basics</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">Your membership isn't a key card — it's an all-access pass. Train, take a class, drop the kids at Kid's Club, shoot hoops, then end in the sauna with a smoothie on the way out.</p>
        <p class="body-copy reveal">Add it up elsewhere and you'd need a gym, a yoga studio, a spa, a pool membership and a babysitter. Here it's one roof, one price, three locations — with a staffed Kid's Club while you train, 24/7 access at Main, indoor courts, an outdoor fitness pavilion, and a full recovery suite of sauna, steam, hot tub, cold plunge and warm therapy pools.</p>
      </div>
    </div>
  </div>
</section>
""" + marquee(["24/7 Access", "Free Babysitting", "Indoor Pools", "Outdoor Fitness", "Basketball", "J-Bar Smoothies", "3 Locations"]) + split(
    "Open 24/7", "02",
    'The flagship that never <span class="serif">sleeps</span>',
    ["GHF Main makes it easy to get fit, strong and lean, with 24-hour access, pool and spa studio, free babysitting, expansive cardio selections, state-of-the-art strength training equipment, the largest free weight area, access to all three facilities, and more."],
    f"{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg",
    "Open free weight space with benches, dumbbells, and barbells at Gainesville's largest gym",
    cta=("Explore GHF Main", "main-center.html"), tag="GHF Main",
    name="GHF Main", href="main-center.html",
) + split(
    "Women only", "03",
    'The only gym in Gainesville just for <span class="serif">women</span>',
    ["We believe nothing is more essential than women supporting and empowering one another. Experience and enjoy the most advanced fitness center for women in Gainesville with unique fitness classes, sauna, steam, and hot tub, free babysitting, and lots of cardio and weight equipment to lead your healthiest, happiest life and make your wellness goals come true."],
    f"{IMG}/GHF_GHF_Women_Womens_Center_SWEAT_2023_1.jpg",
    "Group fitness instructor teaching HIIT for women at the Women's Center",
    rev=True, cta=("Explore GHF For Women", "womens-center.html"), tag="Women's Center",
    name="GHF Women", href="womens-center.html",
) + split(
    "Tioga Town Center", "04",
    'Your family-friendly <span class="serif">gym</span>',
    ["From the moment you walk through the door, you will encounter friendly GHF Tioga staff, dedicated to making your health club experience remarkable. They will guide you to the right space whether you want to take a group fitness class, walk on the treadmill, or sweat it out on our outdoor fitness turf, there is always someone happy to show you how.",
     "Bring the kids to the Kid's Club for complimentary babysitting or to CrossFit for Kids — there's a place for everyone in the family!"],
    f"{IMG}/GHF_CrossFit_Kids_Exercise_CrossFit_for_Kids_Tioga_2026.jpg",
    "Kids CrossFit class bear crawl exercise at GHF Tioga",
    cta=("Explore GHF Tioga", "tioga-center.html"), tag="GHF Tioga",
    name="GHF Tioga", href="tioga-center.html",
) + split(
    "Outdoor fitness pavilion", "05",
    'The largest open-air fitness <span class="serif">destination</span>',
    ["The largest open-air fitness destination will give you a line of new ways to move, lift, train and sweat. Located at GHF's Main campus, Echo is a multi-purpose location that offers fitness classes, functional training equipment, and community events.",
     "Echo offers specialty workshops, GroupFit classes and lifestyle events. We have open gym times for members to use the functional training equipment like tires, sleds, ropes, TRX, rowers and ski ergs, and more. These classes are included in your membership."],
    f"{IMG}/Echo_GroupFit_Outdoor_Classes_Fun_Classes_2021.jpg",
    "Fitness classes in an outdoor gym setting at Echo",
    rev=True, cta=("Explore Echo", "echo.html"), href="echo.html", tag="Echo",
    name="Echo Outdoor Pavilion",
) + f"""
<section class="section section--light">
  <div class="wrap">
    <a class="split split--link" href="pool.html">
      <div class="split__media reveal-img"><img src="{IMG}/sports-activities-pool-wide-700x467.jpg" alt="Indoor lap pool at GHF" loading="lazy"><span class="tag">Aquix by GHF</span></div>
      <div class="split__body">
        <p class="eyebrow">Indoor pool &amp; spa</p>
        <h2 class="h-display split__name">Aquix</h2>
        <p class="h-mid split__lead">Dive into a world of <span class="serif">wellness</span></p>
        <p class="body-copy reveal">The gentle embrace of water has long been revered for its healing properties. As you glide through the water, the buoyancy relieves joint stress, promoting flexibility and strengthening muscles. The hydrostatic pressure encourages blood circulation, reducing inflammation and promoting healing.</p>
        <ul class="checklist reveal" style="margin-top:26px">
          <li>75-foot Indoor Lap Pool</li>
          <li>Himalayan Salt Wall Sauna</li>
          <li>Cleansing Steam Room</li>
          <li>Arctic Cold Pool</li>
          <li>Warm Thermal Pool</li>
          <li>Massage-like Hot Tub</li>
          <li>Aqua Classes</li>
        </ul>
        <div class="split__cta"><span class="inline-link">Dive Into Aquix →</span></div>
      </div>
    </a>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">And so much more</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Included in your <span class="serif">membership</span></h2>
      </div>
    </div>
    <div class="card-grid" data-stagger>
      <a class="card" href="group-fitness.html">
        <div class="card__media"><img src="{IMG}/Body_Balance_Les_Mills_Yoga_Group_Fitness_Tioga_2023_2.jpg" alt="Group classes at GHF" loading="lazy">
        <div class="card__label"><h3>800+ Classes Monthly</h3><span class="go">See the classes →</span></div></div>
      </a>
      <a class="card" href="kids-club.html">
        <div class="card__media"><img src="{IMG}/kids_club.jpg" alt="Kids Club at GHF" loading="lazy">
        <div class="card__label"><h3>Free Babysitting</h3><span class="go">Check out Kid's Club →</span></div></div>
      </a>
      <a class="card" href="court-sports.html">
        <div class="card__media"><img src="{IMG}/GHF_Basketball_5.jpg" alt="Regulation-size indoor basketball court at GHF" loading="lazy">
        <div class="card__label"><h3>Indoor Basketball</h3></div></div>
        <div class="card__below"><p>Regulation-size indoor basketball court with six hoops and hardwood flooring. Full-court play six days a week, half-court play every day, and volleyball twice a week (Wednesdays 6–11p &amp; Sundays 5–10p).</p></div>
      </a>
      <a class="card" href="jbar.html">
        <div class="card__media"><img src="{IMG}/smoothie_girls_web.png" alt="Real fruit smoothies at J Bar" loading="lazy">
        <div class="card__label"><h3>J-Bar Smoothies</h3></div></div>
        <div class="card__below"><p>Real fruit smoothies, made to order with superior fresh ingredients — the perfect fuel for your workout or recovery. See the full menu.</p></div>
      </a>
      <a class="card" href="pool.html">
        <div class="card__media"><img src="{IMG}/cropped_sauna.jpg" alt="Salt room sauna at GHF" loading="lazy">
        <div class="card__label"><h3>Sauna, Steam &amp; Spa</h3></div></div>
        <div class="card__below"><p>Relax and recover in our sauna, steam room, hot tub — or experience our cold plunge and warm therapy pools.</p></div>
      </a>
      <a class="card" href="member-savings.html">
        <div class="card__media"><img src="{IMG}/Family_Membership_Plans.jpg" alt="Member savings program" loading="lazy">
        <div class="card__label"><h3>Member Savings</h3></div></div>
        <div class="card__below"><p>The Member Savings Program offers GHF members discounts at many local businesses — to save the cost of your dues. See all 136 participating businesses.</p></div>
      </a>
    </div>
  </div>
</section>
""" + form_section(
    "pass", "08", "Request your free guest pass",
    'Your free gym pass is <span class="serif">waiting</span>',
    "With your free guest pass, you will have full membership privileges for one day at any Gainesville Health &amp; Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired.",
    "Claim Your Free Pass",
) + cta_band(
    'More of <span class="serif">everything</span>',
    "Ready to start a more fit life? Become a GHF member today for $15 per week.",
    f"{IMG}/GHF_Functional_Training_Turf_Indoor_Turf_Gainesville_Gyms_Strength_2025.jpg",
)

# ============================================================ GROUP FITNESS
groupfit_body = hero(
    "GroupFit at GHF",
    ["The hour you'll look", 'forward to <span class="serif">all day</span>'],
    "900+ classes a month means there's always one that fits your schedule, your level, and your mood. Dance it out, find your zen, or sweat with a roomful of people cheering you on — your first class is free.",
    img=f"{IMG}/GHF_GroupFit_Les_Mills_Body_Pump_Squats.jpg",
    crumb='<a href="group-fitness.html">Fitness</a> &nbsp;/&nbsp; Group Classes',
    actions=[("View Class Schedule", "#schedule", True), ("Try a Free Class", "#pass", False)],
    meta=["900+ classes / month", "Included in membership", "All levels welcome"],
    page=True,
) + marquee(["Zumba", "Body Pump", "Indoor Cycle", "Yoga", "HIIT", "Pilates Mat", "Tai Chi", "Aqua", "Hot Yoga", "Body Combat"]) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">A few examples of the classes we offer</p>
        <h2 class="h-display reveal">Something for <span class="serif">everyone</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">From beginner to advanced — and classes are included in your membership. Come as often as you want. We're here to help you reach your potential.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>Aqua Strength and Balance</li>
          <li>Les Mills classes (Body Pump, Flow, Combat, Core)</li>
          <li>Circuit Training/HIIT</li>
          <li>Club Seniors (Sit To Be Fit, balance, gentle joints)</li>
          <li>Hot Yoga (85&deg;, 95&deg;, 105&deg;)</li>
          <li>Pilates Mat</li>
          <li>SkyCycle Indoor Cycling</li>
          <li>Yoga</li>
          <li>Zumba, Cardio Party MashUp, Dance Attack</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section section--flush">
  <div class="gallery wrap">
    <div class="g-item g-item--a reveal-img"><img src="{IMG}/GHF_GroupFit_SkyCycle_Classes_Cycle_Cardio_2024.jpg" alt="Participants in indoor cycle studio" loading="lazy"></div>
    <div class="g-item g-item--b reveal-img"><img src="{IMG}/GHF_GHF_Women_Womens_Center_Body_Pump_2023_1.jpg" alt="Body Pump group fitness class" loading="lazy"></div>
    <div class="g-item g-item--c reveal-img"><img src="{IMG}/GHF_Group_Fitness_Yoga_Tioga.jpg" alt="Group fitness yoga class at Tioga" loading="lazy"></div>
  </div>
</section>

<section class="section" id="popular">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Unsure where to start?</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Our most <span class="serif">popular</span> classes</h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">We recommend trying all kinds of classes to find what best suits you, your style and your vibe. Most classes are offered at a variety of times and days with different instructors.</p>
    </div>
    <div class="rows reveal">
      <div class="row-item"><span class="row-item__idx">01</span><span class="row-item__title">Zumba</span><span class="row-item__desc">Dance-party cardio that never feels like a workout.</span><span class="row-item__arrow">&rarr;</span></div>
      <div class="row-item"><span class="row-item__idx">02</span><span class="row-item__title">Body Combat</span><span class="row-item__desc">Strike, punch and kick your way to total-body fitness.</span><span class="row-item__arrow">&rarr;</span></div>
      <div class="row-item"><span class="row-item__idx">03</span><span class="row-item__title">Body Pump</span><span class="row-item__desc">The original barbell class &mdash; tone and condition every major muscle group.</span><span class="row-item__arrow">&rarr;</span></div>
      <div class="row-item"><span class="row-item__idx">04</span><span class="row-item__title">Cardio Party MashUp</span><span class="row-item__desc">A mashup of dance and cardio styles set to music you already love.</span><span class="row-item__arrow">&rarr;</span></div>
      <div class="row-item"><span class="row-item__idx">05</span><span class="row-item__title">Aqua HIIT &amp; HIIT</span><span class="row-item__desc">High-intensity intervals &mdash; in and out of the water.</span><span class="row-item__arrow">&rarr;</span></div>
      <div class="row-item"><span class="row-item__idx">06</span><span class="row-item__title">S.W.E.A.T.</span><span class="row-item__desc">Exactly what it sounds like. Bring a towel.</span><span class="row-item__arrow">&rarr;</span></div>
      <div class="row-item"><span class="row-item__idx">07</span><span class="row-item__title">Yoga or Stretch</span><span class="row-item__desc">Find your zen, restore your range of motion.</span><span class="row-item__arrow">&rarr;</span></div>
      <div class="row-item"><span class="row-item__idx">08</span><span class="row-item__title">Pilates Mat</span><span class="row-item__desc">Core strength and control &mdash; no machines required.</span><span class="row-item__arrow">&rarr;</span></div>
      <div class="row-item"><span class="row-item__idx">09</span><span class="row-item__title">Cycle</span><span class="row-item__desc">Indoor cycling classes every day of the week in our Sky Cycle studio.</span><span class="row-item__arrow">&rarr;</span></div>
    </div>
  </div>
</section>

{schedule_block("schedule", "Class schedule",
                 'Find your <span class="serif">class</span>',
                 "Filter by location, class type, studio, day or instructor. Every class below is included in your membership.")}
""" + split(
    "Classes for every body", "04",
    'Beginners and seniors <span class="serif">welcome</span>',
    ["There is something for everyone from beginner to advanced and classes are included in your membership. You may also select from indoor cycling classes every day of the week in our Sky Cycle studio or take classes designed just for seniors.",
     "Enjoy more than 700 classes per month including Zumba, Pilates mat, yoga, sports conditioning, H.I.I.T, Les Mills programs, aqua, and more."],
    f"{IMG}/Strength_GroupFit_Seniors_GHF_Tioga_2023_1.jpg",
    "Senior GHF members in a strength group fitness class",
    cta=("Classes for Seniors", "group-fitness.html"), tag="All Levels",
) + form_section(
    "pass", "05", "Request your free fitness class pass",
    'Your free class pass is <span class="serif">waiting</span>',
    "With your free class pass, you will have full membership privileges for one day at any Gainesville Health &amp; Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired.",
    "Get My Free Class Pass",
) + cta_band(
    'Come as often as you <span class="serif">want</span>',
    "And best of all, these classes are included in your GHF membership. We're here to help you reach your potential.",
    f"{IMG}/stockhiphop.jpg",
)

# ============================================================ PERSONAL TRAINING
testimonials = [
    ("I finally see changes in my body and I can run again.", "Sindia"),
    ("I've experienced the results that personal training can give you and it's life-enhancing.", "Phyllis"),
    ("I lost 55lbs and found the confidence to keep it off.", "Carol"),
    ("I am proud to say I have lost nearly 80lbs with the expertise of my trainer who pushed me to heights I never thought possible and never gave up on me.", "Anita"),
    ("I added 20 yards to my golf drive and lowered my A1C.", "Steber"),
    ("Through my trainer's leadership and motivational skills, I was able to lose over 30 pounds.", "Jared C."),
    ("I dropped five dress sizes and 45 pounds with personal training. You can too!", "Kimmy C."),
    ("I'm pain-free. Personal training has me hiking trails again.", "Scott F."),
]
slides = "".join(
    f"""<div class="t-slide"><figure class="quote-band"><span class="quote-band__mark">“</span><blockquote>{q}</blockquote><figcaption>— {n}</figcaption></figure></div>"""
    for q, n in testimonials
)
pt_body = hero(
    "GHF Personal Training",
    ["I train", 'for <span class="serif">life</span>'],
    "Lose the weight. Fix the back pain. Add 20 yards to your drive. 35 nationally certified trainers who treat your goal like a promise — and your first assessment is free.",
    img=f"{IMG}/Hero_Shot_PT_Page_Debra_and_Adam_Personal_Training_2021.jpg",
    crumb='<a href="personal-training.html">Training</a> &nbsp;/&nbsp; Personal Training',
    actions=[("Schedule Your Free Assessment", "#assessment", True), ("Training Options", "#options", False)],
    meta=["35+ certified trainers", "Olympic athletes trained", "Free first assessment"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">One-on-one personal training</p>
        <h2 class="h-display reveal">Make real results <span class="serif">happen</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">It all starts with you and your GHF trainer who will design a program to support your unique goals, passions, and personality.</p>
        <p class="body-copy reveal">Clients of all fitness levels benefit from the combined knowledge, training and practice of 35 specialized, nationally certified trainers. You won't find this anywhere else in the region. We will customize your workout to help you feel great and enjoy life to the fullest.</p>
        <div class="reveal"><a class="inline-link" href="#assessment">Schedule Your FREE Assessment →</a></div>
      </div>
    </div>
  </div>
</section>
""" + f"""
<section class="section section--flush" id="options">
  <div class="wrap" style="padding-bottom:clamp(80px,11vw,170px)">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Personal training that fits your life</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Three ways to <span class="serif">train</span></h2>
      </div>
    </div>
    <div class="card-grid" data-stagger>
      <div class="card">
        <div class="card__media"><img src="{IMG}/Personal_Training_Legs_Training_2021_1.jpg" alt="Personal trainer training athlete in goblet squat one on one" loading="lazy"><span class="card__num">01</span>
        <div class="card__label"><h3>Private</h3></div></div>
        <div class="card__below"><p>Achieve your fitness goals through 1-on-1 workouts personalized to match your abilities. Your personal trainer will inspire, guide and motivate.</p></div>
      </div>
      <div class="card">
        <div class="card__media"><img src="{IMG}/Personal_Training_Hamstring_Stretch_Certified_Trainer_Flexibility_PT_2022.jpg" alt="Personal training at GHF one on one hamstring stretch" loading="lazy"><span class="card__num">02</span>
        <div class="card__label"><h3>Express</h3></div></div>
        <div class="card__below"><p>Enjoy the individual attention and proven benefits of personal training in half the time. 25-minute sessions to fit your busy life.</p></div>
      </div>
      <div class="card">
        <div class="card__media"><img src="{IMG}/pt_seth_and_lisa_home.jpg" alt="Personal trainer Seth with personal training clients" loading="lazy"><span class="card__num">03</span>
        <div class="card__label"><h3>Semi-Private</h3></div></div>
        <div class="card__below"><p>Workout with a friend. Semi-private personal training matches you and a friend with a trainer eager to help you succeed together.</p></div>
      </div>
    </div>
  </div>
</section>
""" + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="split">
      <div class="split__media reveal-img"><img src="{IMG}/GHF_Personal_Training_Trainers_one_on_one_clients_2025-2.jpg" alt="GHF trainer working one on one with a client" loading="lazy"><span class="tag">GHF PT Studio</span></div>
      <div class="split__body">
        <p class="eyebrow">Why train at GHF</p>
        <h2 class="h-display" style="font-size:clamp(30px,3.8vw,58px)">The best in the <span class="serif">industry</span></h2>
        <ul class="checklist reveal" style="margin-top:10px">
          <li>40 personal trainers on staff</li>
          <li>Certified and accredited</li>
          <li>Thousands of clients trained</li>
          <li>Multiple Olympic athletes trained</li>
          <li>120,000 sq ft of the world's most innovative training equipment</li>
        </ul>
        <div class="split__cta"><a class="inline-link" href="#assessment">Schedule Your FREE Assessment →</a></div>
      </div>
    </div>
  </div>
</section>
""" + trainers_section("04") + f"""
<section class="section">
  <div class="wrap" style="padding-left:0;padding-right:0">
    <p class="eyebrow wrap" style="margin-bottom:clamp(30px,4vw,60px)">Real members. Real results.</p>
    <div class="t-slider">
      <div class="t-slider__track">{slides}</div>
      <div class="t-slider__nav">
        <button data-dir="prev" aria-label="Previous testimonial">←</button>
        <button data-dir="next" aria-label="Next testimonial">→</button>
      </div>
    </div>
  </div>
</section>
""" + f"""
<section class="section section--light" id="assessment">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Free fitness assessment &amp; training session</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Your first session is on <span class="serif">us</span></h2>
        <p class="lede reveal" style="margin-top:28px">You will be matched with a certified personal trainer to assess your abilities, determine your action plan and guide your complimentary training session. Your assessment features the InBody 570 Body Composition Analyzer &mdash; a detailed snapshot of your body's makeup: body fat, lean muscle, metabolic rate, total body water, and visceral fat &mdash; helping you make informed decisions about your fitness and wellness journey.</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_PT_ACTION}" accept-charset="UTF-8">
          <input type="hidden" name="inf_form_xid" value="{KEAP_PT_XID}">
          <input type="hidden" name="inf_form_name" value="Web Form submitted">
          <input type="hidden" name="infusionsoft_version" value="{KEAP_PT_VERSION}">
          {KEAP_TRAPS}
          <div class="field"><input type="text" name="inf_field_FirstName" id="assessment-first" placeholder=" " required><label for="assessment-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="assessment-last" placeholder=" " required><label for="assessment-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="assessment-email" placeholder=" " required><label for="assessment-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="assessment-phone" placeholder=" " required><label for="assessment-phone">Phone</label></div>
          <div class="field field--full">
            <select name="inf_custom_SelectAProgram" id="assessment-program" aria-label="What are you interested in?">
              <option value="Free Assessment" selected>Free Assessment</option>
              <option value="1 on 1 Personal Training">1 on 1 Personal Training</option>
              <option value="Semi-Private Personal Training">Semi-Private Personal Training</option>
              <option value="Express Training Sessions">Express Training Sessions</option>
            </select>
            <label for="assessment-program">What are you interested in?</label>
          </div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Schedule Your Assessment <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">We will contact you via phone, email, or text. There is no charge, no obligation and no risk.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Now is the time. <span class="serif">Start training for life.</span>',
    "Complete the form and we will contact you via phone, email, or text. We look forward to meeting you!",
    f"{IMG}/Personal_Training_Legs_Training_2021_1.jpg",
    primary=("Get Started", "#assessment"),
)

# ============================================================ STRENGTH
strength_body = hero(
    "Strength Training",
    ["Never wait for a", '<span class="serif">platform</span> again'],
    "Gainesville's largest strength floor just doubled. More racks, more benches, more bars than anywhere in town — and a coach to teach you every lift, free, every single visit.",
    img=f"{IMG}/GHF_Leg_Den_Leg_Day_Exercise_Fitness_Squats_Deadlifts_2025-2.jpg",
    crumb='Fitness &nbsp;/&nbsp; Strength Training',
    actions=[("Try For Free", "#pass", True), ("The Expansion", "#expansion", False)],
    meta=["10,000 sq ft expansion", "Largest free weight area", "Staff help at no charge"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">The equipment</p>
        <h2 class="h-display reveal">Train smarter, build stronger, move <span class="serif">better</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">Our state-of-the-art strength training machines make it easy to target every muscle group safely and effectively, whether you're new to lifting or an experienced athlete.</p>
        <p class="body-copy reveal">Featuring industry-leading brands like Hammer Strength, Precor, Matrix, X-Force Negative machines, and MedX, each piece of equipment is designed to help you maximize performance with precision and control. You'll also find functional strength training stations both indoors and outdoors at GHF Main and GHF Tioga — train on the turf to push your limits in new ways. With selectorized, cable-based, plate-loaded machines, and Gainesville's largest free weight areas, Gainesville Health &amp; Fitness gives you the tools to train smarter, build stronger, and move better every day.</p>
      </div>
    </div>
  </div>
</section>
""" + marquee(["Hammer Strength", "Precor", "Matrix", "X-Force", "MedX", "Free Weights", "Functional Turf"], ghost=True) + f"""
<section class="section" id="expansion">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Free weight &amp; functional training studio</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">More steel, more space, <span class="serif">no waiting</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">We didn't just add a few plates; we doubled our footprint. GHF now offers the largest free weight selection in Gainesville, specifically designed to eliminate the "gym rush" bottlenecks.</p>
    </div>
    <div class="pillars" data-stagger>
      <div class="pillar"><span class="pillar__num">01</span><h3>Double the Real Estate</h3><p>Massive expansion means you aren't tripping over someone else's bench.</p></div>
      <div class="pillar"><span class="pillar__num">02</span><h3>The Iron Standard</h3><p>Gainesville's largest selection of bars, dumbbells, and kettlebells.</p></div>
      <div class="pillar"><span class="pillar__num">03</span><h3>Specialized Platforms</h3><p>Dedicated squat and deadlift platforms designed for heavy pulls and deep squats.</p></div>
      <div class="pillar"><span class="pillar__num">04</span><h3>The Bench Gallery</h3><p>An expanded lineup of flat and incline benches so you can get to work immediately.</p></div>
    </div>
  </div>
</section>
""" + split(
    "The EndZone &amp; functional training", "03",
    'Specialized zones for specific <span class="serif">goals</span>',
    ["We know that modern training requires more than just a rack. Our new expansion introduces specialized zones to target specific goals:",
     "<strong>The EndZone:</strong> A dedicated area packed with specialized equipment focusing exclusively on hips and glutes.<br><strong>Functional Turf:</strong> 10,000 sq. ft. of open turf featuring TRX units, pull-up stations, jump boxes, and assault bikes.<br><strong>Plate-Loaded Power:</strong> A comprehensive selection of plate-loading equipment for total-body strength and hypertrophy.",
     "Whether you are a powerlifter, a functional athlete, or just starting your journey, we have the space you deserve."],
    f"{IMG}/GHF_Functional_Training_Turf_Indoor_Turf_Gainesville_Gyms_Strength_2025.jpg",
    "Indoor functional training turf area at GHF",
    tag="Functional Turf",
) + split(
    "A circuit for beginners", "04",
    'How to start strength training — with help, <span class="serif">every time</span>',
    ["This strength training circuit, available in each gym location, is perfect for the first time exerciser who is unfamiliar with how to lift weights. Newcomers enjoy a structured way to get the best strength results in the shortest amount of time. You'll move through a series of nine weight machines, working all your major muscle groups along the way. We teach you how to use the machine, how much weight, and the best form.",
     "The most important feature of the circuit is our staff. Just look for the friendly people in the blue shirts. They will help set up each weight machine for you, and assist you with every workout, at no extra charge. This service is included in every membership."],
    f"{IMG}/Tioga_Carrie_Grotto_Arm_Cross_Facility_2022.jpg",
    "GHF member getting help on a strength training machine by a fitness instructor",
    rev=True, tag="The Line",
) + split(
    "X-Force negative training", "05",
    'Accentuate the <span class="serif">negative</span>',
    ["X-Force is the most meaningful advance in strength training in the last 30 years. A patented \"tilting\" weight stack allows for a 40% heavier resistance on the \"negative\" (lowering) part of the exercise. This heavier negative resistance allows for a greater intensity of effort through a higher quality of resistance. Great strength gains in less time!",
     "Results that previously required several workouts a week can now be stimulated in 1-2 workouts a week. By doing the lowering (or negative) part of a lift slowly, you can activate key hormones in your body that enhance fat burn."],
    f"{IMG}/XForce_Body_by_GHF_Build_Strength_Lean_Muscle_Chest_Workouts_2023.jpg",
    "Coach training one-on-one negative training weights in X-Force Body studio",
    tag="X-Force",
) + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Benefits of strength training</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">The science is <span class="serif">clear</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:40ch">Strength training is one of the most powerful tools available for transforming your health and extending your lifespan — with benefits that extend far beyond just building stronger muscles.</p>
    </div>
    {accordion([
        ("You'll literally live longer (and better)",
         "Okay, this is wild: adults who strength train 2-3 times a week have a 20% lower risk of dying prematurely from any cause. But it gets better—90 minutes of weekly resistance training is linked to slowing your biological aging by almost four years. This is legit science showing that muscle-strengthening exercise is one of the most effective ways to not just live longer, but stay active and independent as you age."),
        ("Your heart will thank you",
         "Plot twist: weight training is actually amazing for your cardiovascular health. We're talking lower blood pressure, decreased bad cholesterol (LDL) and triglycerides, and increased good cholesterol (HDL). And here's where it gets really interesting for women—muscle-strengthening activities provide up to a 30% reduction in cardiovascular mortality. That's one of the strongest protective effects documented in all of exercise research."),
        ("Build muscle, boost your metabolism (even while Netflix-ing)",
         "Here's something cool: one of the best benefits of lifting weights is that more muscle = higher metabolism. We're talking up to 7% higher resting metabolic rate, which means you're burning more calories literally just existing. And this metabolic boost is especially clutch for women over 40 who are dealing with the natural metabolic slowdown that comes with age."),
        ("Stronger bones = future you will be so grateful",
         "Real talk: the bone-strengthening benefits of resistance training are critical, especially for women. When you lift weights, you're putting controlled stress on your bones, which signals your body to make them stronger. During menopause, women can lose up to 20% of their bone mass in just 5-7 years. Regular resistance exercise increases bone mineral density and significantly cuts your risk of osteoporosis, which affects about 8 million women in the US."),
        ("Better mental health than most things your therapist recommends",
         "The mental health benefits of weight training are honestly incredible. Large-scale studies from 2024 show that resistance training significantly reduces depression and anxiety across all ages—from teens to post-menopausal women. In fact, strength training is now recognized as a legit treatment option for mild to moderate depression, right alongside therapy and medication. Plus, it boosts self-esteem, improves body image, and may even reduce your risk of cognitive decline and Alzheimer's as you age."),
    ])}
  </div>
</section>
""" + form_section(
    "pass", "07", "Request your free guest pass",
    'Enjoy our wide variety of strength training <span class="serif">equipment</span>',
    "Check out the gym with the most weight equipment — from benches and barbells to platforms and cables. Your guest pass gives you full membership privileges for one day at any Gainesville Health &amp; Fitness location. There is no charge, no obligation and no risk — just a great workout.",
    "Get My Free Pass", light=False,
) + cta_band(
    'Built to make you <span class="serif">stronger</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/GHF_Strength_Free_Weights_Dumbbells_2025-2.jpg",
)

# ============================================================ CARDIO
cardio_body = hero(
    "Cardio at GHF",
    ["Cardio you won't", '<span class="serif">dread</span>'],
    "Hundreds of machines means you never wait. 225 personal TVs means you never clock-watch. Treadmill, rower, stair climber or a SkyCycle class — pick your pace and watch the miles disappear.",
    img=f"{IMG}/Cardio_Running_Most_Cardio_in_Gainesville_Gym_2022.jpg",
    crumb='Fitness &nbsp;/&nbsp; Cardio',
    actions=[("Get Your Free All-Access Pass", "#pass", True)],
    meta=["225 personal TVs", "Hundreds of machines", "3 centers"],
    page=True,
) + stats_band([
    (225, "", "Personal TVs on cardio equipment"),
    (700, "+", "Classes per month"),
    (3, "", "Centers to choose from"),
    (7, "", "Days of SkyCycle every week"),
]) + split(
    "The equipment", "01",
    'The most cardio in <span class="serif">Gainesville</span>',
    ["We are the largest fitness company in Gainesville with more state-of-the-art equipment including treadmills, AMTs, rowers, ellipticals, ARC trainers, stair climbers, more. You have access to 225 personal TV's on cardio equipment for your entertainment.",
     "Having a consistent cardio routine is crucial for maintaining good health and overall fitness. Cardiovascular exercises such as running, cycling, swimming, or brisk walking elevate your heart rate, which helps improve heart and lung function, blood circulation, and oxygen transport throughout your body."],
    f"{IMG}/upstairs_cardio.JPG",
    "Upstairs cardio equipment at the gym",
    tag="Cardio Deck",
) + split(
    "Why it matters", "02",
    'Your heart will <span class="serif">thank you</span>',
    ["By consistently engaging in cardio workouts, you can also increase your endurance and stamina, allowing you to perform daily activities with greater ease and efficiency. Cardio also burns calories and can aid in weight management, which is essential for maintaining a healthy body weight and reducing the risk of chronic diseases.",
     "Cardio workouts have been shown to release endorphins, which can improve mood and reduce stress levels. Ultimately, including cardio in your workout routine is an excellent way to improve your overall health and well-being."],
    f"{IMG}/rower.JPG",
    "Row cardio equipment",
    rev=True, tag="Endorphins Inside",
) + split(
    "Fitness classes", "03",
    '700+ ways to get your heart <span class="serif">rate up</span>',
    ["Enjoy more than 700 classes per month including Zumba, Pilates mat, yoga, sports conditioning, H.I.I.T, Les Mills programs, aqua, and more. You may also select from indoor cycling classes every day of the week in our Sky Cycle studio or take classes designed just for seniors.",
     "There is something for everyone from beginner to advanced and classes are included in your membership. With three centers to choose from, hundreds of cardio machines, an exciting variety of group exercise classes, and a caring staff to help you every step of the way, now is the time to get started."],
    f"{IMG}/GHF_GroupFit_SkyCycle_Classes_Cycle_Cardio_2024.jpg",
    "Participants in indoor cycle studio",
    cta=("Check out the GroupFit Class schedule", "group-fitness.html#schedule"), tag="SkyCycle",
) + form_section(
    "pass", "04", "Request your free guest pass",
    'Your free all-access pass is <span class="serif">waiting</span>',
    "With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health &amp; Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired.",
    "Claim My Free Pass",
) + cta_band(
    'Now is the time to get <span class="serif">started</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/overhead_cardio.jpg",
)

# ============================================================ POOL / AQUA
# The seven Aquix spaces. Long copy is GHF's own, from ghfc.com/pool — our page had
# condensed it, and the detail it dropped is exactly the benefit detail worth surfacing.
# NOTE: 05 and 06 are both warm-water shots; 05 keeps the file this page already
# captioned "Warm therapy pool at GHF". Worth a human eye on which pool is which.
POOL_SPACES = [
    ("75-Foot Indoor Lap Pool",
     "Lap swimming, technique work and endurance, all year round.",
     f"{IMG}/sports-activities-pool-wide-700x467.jpg", "The 75-foot indoor lap pool at GHF", 700, 467,
     "<p class=\"body-copy\">Dive into a world-class swimming experience with our 75-foot indoor lap pool. Whether you're a seasoned swimmer or just starting out, our pool provides the perfect environment to improve your technique, build endurance, and achieve your aquatic fitness goals.</p>"
     "<p class=\"body-copy\">Indoors and heated, so the weather never costs you a session.</p>"),
    ("Himalayan Salt Wall Sauna",
     "Dry heat and a wall of Himalayan salt.",
     f"{IMG}/sports-activities-pool-sauna-700x467.jpg", "Himalayan salt wall sauna at GHF", 700, 467,
     "<p class=\"body-copy\">Indulge in the soothing warmth of our Himalayan Salt Wall Sauna. With its dry heat, this sauna offers a rejuvenating experience that can help alleviate chronic pain, reduce joint stiffness, and strengthen your immune system.</p>"
     "<p class=\"body-copy\">Step inside and let the natural properties of Himalayan salt envelop you in relaxation.</p>"),
    ("Cleansing Steam Room",
     "Warm steam to open up and clear out.",
     f"{IMG}/sports-activities-pool-steam-room-700x467.jpg", "Steam room at GHF", 700, 467,
     "<p class=\"body-copy\">Experience the cleansing power of our steam room. Set at a comfortable temperature, our steam room promotes circulation, lowers blood pressure, reduces stress, and clears congestion.</p>"
     "<p class=\"body-copy\">It's the perfect place to unwind and let the healing steam envelop your body, leaving you refreshed and revitalized.</p>"),
    ("Arctic Cold Pool",
     "A cold plunge for recovery and a genuine jolt of energy.",
     f"{IMG}/Aqua_GHF_Aquix_Cold_Plunge_Cold_Therapy_Pool_2023_1.jpg", "Cold plunge pool at GHF", 1800, 1199,
     "<p class=\"body-copy\">Awaken your senses and elevate your energy with a plunge into our invigorating cold pool. Cold plunging is known to provide an instant pick-me-up, increase your baseline dopamine levels, aid in muscle recovery, support your immune system, and provide relief from pain.</p>"
     "<p class=\"body-copy\">Embrace the chill and discover the numerous benefits of cold water therapy.</p>"),
    ("Warm Thermal Pool",
     "Therapeutic warmth for joints, injuries and low-impact movement.",
     f"{IMG}/sports-activities-pool-hot-tub-700x467.jpg", "Warm thermal pool at GHF", 700, 467,
     "<p class=\"body-copy\">Immerse yourself in our warm thermal pool, where therapeutic benefits abound. The warm water helps relax muscles, increases blood flow to injured areas, and provides a low-impact environment for exercise.</p>"
     "<p class=\"body-copy\">Whether you're seeking relief from muscle spasms, back pain, arthritis, or fibromyalgia, our warm thermal pool is a haven of healing.</p>"),
    ("Hot Whirlpool",
     "Heat plus massaging jets, at the end of a long day.",
     f"{IMG}/Aqua_GHF_Aquix_Hot_Tube_Pool_2023_1.jpg", "Hot whirlpool at GHF", 1800, 1199,
     "<p class=\"body-copy\">Melt away the stresses of the day in our hot whirlpool. The soothing warmth and massaging action offer a sanctuary for physical, emotional, and mental relaxation.</p>"
     "<p class=\"body-copy\">Indulge in the therapeutic benefits as the hot water eases tension, promotes muscle relaxation, relieves pain, and improves sleep. Let the whirlpool become your personal oasis of tranquility.</p>"),
    ("Aqua Classes &amp; Swimming",
     "Low-impact training for every age and ability.",
     f"{IMG}/GHF_Aquix_Pool_2018.jpg", "Aqua group fitness class in the pool at GHF", 1200, 800,
     "<p class=\"body-copy\">Dive into the refreshing world of aqua fitness and swimming. The buoyancy of water reduces joint impact, making it an ideal low-impact exercise for all ages and abilities.</p>"
     "<p class=\"body-copy\">Whether you're looking to improve flexibility, build cardiovascular endurance, strengthen your core, or simply enjoy the supportive community, our aqua classes and swimming opportunities will leave you feeling energized and accomplished.</p>"),
]


pool_body = hero(
    "Aquix by GHF",
    ["The spa day hiding in your", '<span class="serif">gym membership</span>'],
    "A 75-foot heated lap pool. Himalayan salt sauna. Steam, hot tub, warm therapy pool and an arctic plunge. Gainesville's only full-service aqua center — included with membership, every single day.",
    img=f"{IMG}/GHF_Gainesville_Health_and_Fitness_Swimming_Pool_Aqua_Aquix.jpg",
    crumb='Fitness &nbsp;/&nbsp; Indoor Pool &amp; Aquatics Center',
    actions=[("Try For Free", "#pass", True), ("Explore the Studio", "#features", False)],
    meta=["75-ft indoor lap pool", "Salt wall sauna", "Cold + warm pools"],
    page=True,
) + marquee(["Lap Pool", "Salt Sauna", "Steam Room", "Cold Pool", "Warm Pool", "Whirlpool", "Aqua Classes"]) + f"""
<section class="section" id="features">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Take a close look at what awaits you</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Seven ways to <span class="serif">soak it in</span></h2>
      </div>
    </div>
    {rows_expand(POOL_SPACES)}
  </div>
</section>

<section class="section section--flush">
  <div class="gallery wrap">
    <div class="g-item g-item--a reveal-img"><img src="{IMG}/sports-activities-pool-wide-700x467.jpg" alt="Indoor lap pool at GHF" loading="lazy"></div>
    <div class="g-item g-item--b reveal-img"><img src="{IMG}/sports-activities-pool-sauna-700x467.jpg" alt="Sauna at GHF" loading="lazy"></div>
    <div class="g-item g-item--c reveal-img"><img src="{IMG}/sports-activities-pool-hot-tub-700x467.jpg" alt="Warm therapy pool at GHF" loading="lazy"></div>
  </div>
</section>
""" + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="split">
      <div class="split__media reveal-img"><img src="{IMG}/GHF_Aquix_Pool_2018.jpg" alt="Aqua group fitness class in the pool" loading="lazy"><span class="tag">GroupFit Aqua</span></div>
      <div class="split__body">
        <p class="eyebrow">Aqua group classes</p>
        <h2 class="h-display" style="font-size:clamp(30px,3.8vw,58px)">A few of the aqua classes we <span class="serif">offer</span></h2>
        <ul class="checklist reveal" style="margin-top:10px">
          <li>Aqua HIIT</li>
          <li>Aqua Barre</li>
          <li>Aqua Yoga Flow</li>
          <li>Aqua Zumba</li>
          <li>Gentle Joints</li>
          <li>Stretch &amp; Tone</li>
        </ul>
        <p class="body-copy reveal" style="margin-top:26px">And best of all, these classes are included in your GHF membership. Come as often as you want. We're here to help you reach your potential.</p>
        <div class="split__cta"><a class="inline-link" href="group-fitness.html#schedule">See Our Complete Class Schedule →</a></div>
      </div>
    </div>
  </div>
</section>
""" + schedule_block("schedule", "In the water this week",
                 'Every class in the <span class="serif">pool</span>',
                 "The live schedule for our lap pool and warm therapy pool at GHF Main. Filter by class type, studio, day or instructor &mdash; every class is included in your membership.",
                 room="LAP POOL,WARM THERAPY POOL") + form_section(
    "pass", "03", "Your relaxation experience is a click away",
    'Your free guest pass is <span class="serif">waiting</span>',
    "Your guest pass gives you one day privileges to check out the recovery services and studios and gives you access to each gym to try out GHF. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired.",
    "Get My Guest Pass", light=False,
) + cta_band(
    'Feel <span class="serif">good</span> here',
    "From the invigorating cold plunge to the soothing warmth of our facilities and the dynamic energy of our group fitness classes, every aspect of our facility is designed to make you feel good.",
    f"{IMG}/Aqua_GHF_Aquix_Hot_Tube_Pool_2023_1.jpg",
)

# ============================================================ HOT YOGA
hotyoga_body = hero(
    "Hot Yoga at GHF",
    ["Three temperatures.", 'One stunning <span class="serif">studio</span>.'],
    "Pick your heat: 85° to ease in, 95° to flow, 105° to find your edge. Gainesville's largest, most advanced hot yoga studio lives inside GHF — and every class is included with membership.",
    img=f"{IMG}/GHF_Gainesville_Hot_Yoga_GHF_Yoga_Classes_Group_Fitness_Stretching_Flow_2025-10.jpg",
    crumb='Class Schedule &nbsp;/&nbsp; Hot Yoga',
    actions=[("Free Hot Yoga Pass", "#pass", True), ("Why Hot Yoga?", "#benefits", False)],
    meta=["Largest hot yoga space in the area", "Included in membership", "All levels"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Unlimited potential</p>
        <h2 class="h-display reveal">The best hot yoga in <span class="serif">Gainesville</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">Our studio is the largest hot yoga space in the Gainesville area, providing ample room for movement, breath, and community connection.</p>
        <p class="body-copy reveal">From gentle warm flow to intense hot vinyasa, our expert instructors guide you through powerful mind-body classes designed to build strength, flexibility, and inner peace. Whether you're new to yoga or a seasoned yogi, our studio offers a customized heated yoga experience you won't find anywhere else. If you're searching for hot yoga near me, look no further — tailored to every level, every body, and every intention.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--flush">
  <div class="wrap" style="padding-bottom:clamp(80px,11vw,170px)">
    <p class="eyebrow">Our three signature temperatures</p>
    <div class="temps" data-stagger>
      <div class="temp"><span class="temp__bar"></span>
        <div class="temp__deg">85<sup>°</sup></div>
        <h4>Cozy Yin Yoga</h4>
        <p>Ideal for hot yoga beginners or those who prefer a gentler heat, this inviting temperature allows for increased flexibility without overwhelming your system. It's the perfect entry point to experience the benefits of warm movement and mindfulness.</p>
      </div>
      <div class="temp"><span class="temp__bar"></span>
        <div class="temp__deg">95<sup>°</sup></div>
        <h4>Hot Yoga Flow</h4>
        <p>Offers a classic hot yoga experience at a lower temperature. The moderate heat helps to warm muscles, promoting deeper stretches and an invigorating sweat, fostering both physical and mental resilience.</p>
      </div>
      <div class="temp"><span class="temp__bar"></span>
        <div class="temp__deg">105<sup>°</sup></div>
        <h4>Hot Yoga</h4>
        <p>For the advanced yogi or those craving an intense challenge, our hottest studio pushes your limits. This temperature maximizes detoxification through profuse sweating and dramatically enhances flexibility and cardiovascular conditioning.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--flush">
  <div class="gallery wrap">
    <div class="g-item g-item--a reveal-img"><img src="{IMG}/GHF_Gainesville_Hot_Yoga_GHF_Yoga_Classes_Group_Fitness_Stretching_Flow_2025-3.jpg" alt="Gainesville yoga studio couples poses" loading="lazy"></div>
    <div class="g-item g-item--b reveal-img"><img src="{IMG}/GHF_Gainesville_Hot_Yoga_GHF_Yoga_Classes_Group_Fitness_Stretching_Flow_2025-6.jpg" alt="Yoga studio Gainesville" loading="lazy"></div>
    <div class="g-item g-item--c reveal-img"><img src="{IMG}/GHF_Group_Fitness_Yoga_Tioga.jpg" alt="Group fitness yoga class" loading="lazy"></div>
  </div>
</section>

<section class="section" id="benefits">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Why hot yoga?</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">A wealth of <span class="serif">benefits</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">Step into a world of profound wellness at Gainesville Health &amp; Fitness's brand-new, spacious hot yoga studio. More than just a workout, our beautifully designed sanctuary offers a unique mind/body experience that revitalizes, strengthens, and calms.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li><strong>Enhanced Flexibility</strong> — safely loosen muscles for deeper stretches in hips, hamstrings, shoulders, and spine</li>
          <li><strong>Stress Reduction</strong> — quiet the mind, reduce anxiety, find mental clarity</li>
          <li><strong>Detoxification</strong> — flush out toxins through healthy perspiration</li>
          <li><strong>Cardiovascular Health</strong> — strengthen your heart and improve circulation</li>
          <li><strong>Strength &amp; Muscle Toning</strong> — build lean muscle throughout your body</li>
          <li><strong>Better Balance &amp; Stability</strong> — refine coordination with greater ease</li>
          <li><strong>Boosted Mood &amp; Energy</strong> — reduce symptoms of depression and anxiety</li>
          <li><strong>Deeper Mind-Body Connection</strong> — connect breath, movement, and mental state</li>
        </ul>
      </div>
    </div>
  </div>
</section>

{schedule_block("schedule", "Hot yoga schedule",
                'Find your <span class="serif">heat</span>',
                "Every class in the hot studio at GHF Main, updated live. Filter by class type, day or instructor &mdash; and remember every one of them is included in your membership.",
                room="HOT YOGA")}

<section class="section section--light">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Before you arrive</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Studio <span class="serif">guidelines</span></h2>
      </div>
    </div>
    {accordion([
        ("Bring your own mat and full-length towel",
         "Both are required to attend class. Mats and towels are not provided."),
        ("Wear comfortable, moisture-wicking clothing",
         "Choose clothing that allows for ease of movement. Shirts required for everyone."),
        ("Arrive before class begins",
         "Once class has started, the studio doors will close (no entry) to maintain the flow and energy of the session. Class capacity is 30, first come, first served."),
        ("Remove shoes before entering the studio",
         "There are cubbies inside the studio to store shoes."),
        ("Skip the scents",
         "Avoid wearing perfumes, colognes, or strong-smelling products."),
        ("Check with your doctor first",
         "Avoid hot yoga if you are pregnant, have cardiovascular/circulatory conditions, asthma, some skin conditions, or pre-existing conditions."),
    ])}
  </div>
</section>
""" + form_section(
    "pass", "05", "Get your hot yoga class pass",
    'Relax, recover, <span class="serif">rejuvenate</span>',
    "Relax, recover, and rejuvenate with Gainesville's best hot yoga classes in Gainesville's most unique studio. GHF members, you do not need a class pass to attend classes — they are included in your membership!",
    "Get My Hot Yoga Pass", light=False,
) + cta_band(
    'Join Gainesville\'s most spacious hot yoga <span class="serif">community</span>',
    "Our larger-than-average studio space ensures you have ample room to move and breathe freely. This is more than just a place to sweat; it's a community dedicated to mind/body wellness and holistic health right here in Gainesville.",
    f"{IMG}/GroupFit_Echo_Yoga_Class_Outdoor_Classes_2021.jpg",
)

# ============================================================ PILATES
pilates_classes = [
    ("Pilates Foundations", "Perfect for beginners or anyone wanting to strengthen their understanding of Pilates fundamentals. This 50-minute Pilates Reformer class focuses on core principles and prepares you for more advanced routines."),
    ("Pilates Reformer", "Strengthen your core, improve posture, balance, and flexibility with the most popular Pilates machine: the Reformer. All skill levels are welcome as the instructors will provide step-by-step guidance while still allowing each participant to be challenged to their level of participation."),
    ("Pilates Advanced", "The most advanced level of Pilates Reformer. Building upon the fundamental knowledge and strength developed in our weekly Pilates Reformer classes, Advanced Pilates will add more balance, strength and fluidity to your practice."),
    ("Pilates Tower Circuit", "A dynamic mix of Pilates Tower and Reformer exercises for a 50-minute, full-body workout that blends Mat Pilates, Barre, and Cadillac-inspired moves."),
    ("Pilates Tower/Reformer", "This class combines Reformer and Tower for advanced core strength, flexibility, and postural alignment. Ideal for experienced Pilates enthusiasts."),
    ("Pilates Chair", "Build core strength, balance, and muscle control using the Pilates Wunda Chair. A unique and challenging 50-minute class."),
    ("Pilates Chair Fusion", "Incorporate the benefits of both the Pilates Chair and Reformer in a 55-minute combination class. The Chair provides a challenging way to build strength, improve balance and increase muscle coordination and control while the Reformer focuses on posture, pelvic stability, breathing, abdominal strength, and flexibility."),
    ("Pilates Sculpt", "Combine the power of Pilates with strength training. This dynamic, full-body workout with a concentration on legs, arms, and abs uses weights, bands, and Pilates springs for maximum toning."),
    ("Pilates Jump and Pump", "A fun and intense Pilates jumpboard class combined with strength training using weights, bands, and springs for a cardio and sculpting boost — in 50 minutes."),
    ("Pilates Suspension Circuit", "Strengthen and challenge your body in a 50-minute Pilates suspension training class using Bodhi suspension straps, Pilates ring, and apparatus like the Reformer, Chair, and Tower."),
    ("Pilates Stretch and Recover", "A gentle 50-minute Pilates stretch class designed for mobility, relaxation, and pain relief. Great for recovery days and self-care. It is a perfect addition to any workout."),
]
# Keap endpoint for Pilates leads, from the hosted form behind the embed script. Two
# things here differ from the other integrations and must not be "tidied" into the
# shared constants: the version string is newer, and Keap's honeypot field name has
# rotated tenant-wide. The five forms deployed before this one still send the older
# inf_eGYY1p7FcL3TD8b6 in KEAP_TRAPS; leave them as they are.
KEAP_PILATES_ACTION = "https://pv228.infusionsoft.com/app/form/process/811a031399f3283a80897d00234b1b59"
KEAP_PILATES_XID = "811a031399f3283a80897d00234b1b59"
KEAP_PILATES_VERSION = "1.70.0.1010026"
KEAP_PILATES_TRAPS = ('<input type="text" name="inf_3Ht2uaf45U0YMzrh" value="" tabindex="-1" autocomplete="off" style="display:none !important">'
                      '<input type="text" name="inf-sbt" value="" tabindex="-1" autocomplete="off" style="display:none !important">')
pilates_body = hero(
    "Pilates at GHF",
    ["Stand taller.", 'Move <span class="serif">easier</span>.'],
    "A stronger core changes how everything feels — your posture, your back, your confidence. Reformer, Tower, Chair and Cadillac with certified instructors who fit the workout to your body. First session free.",
    img=f"{IMG}/GHF_Pilates_Reformers_Group_Lulu_Promo_Tioga_2024_9.jpg.jpg",
    crumb='Training &nbsp;/&nbsp; Pilates',
    actions=[("First Session Free", "#pass", True), ("Class Descriptions", "#classes", False)],
    meta=["Studios at Main & Tioga", "Certified instructors", "First session free"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">The best Pilates classes in Gainesville, FL</p>
        <h2 class="h-display reveal">An environment of complete <span class="serif">focus</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">Develop a lean, toned body while enjoying an environment of complete focus. Our Certified Pilates Instructors will guide you towards body awareness, flexibility and strength, all while helping you achieve your fitness goals.</p>
        <p class="body-copy reveal">We offer the best in Pilates Reformer, Pilates Tower, Pilates Chair, and Pilates Cadillac. It's the recommended training method to strengthen, lengthen, and restore. Our fully equipped Pilates studios inside Gainesville Health &amp; Fitness Main and Tioga locations feature the latest in Pilates Reformer machines, Tower, Chair, and suspension straps to help you build strength, improve flexibility, and enhance your overall wellness.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--flush">
  <div class="gallery wrap">
    <div class="g-item g-item--a reveal-img"><img src="{IMG}/GHF_Pilates_Pilates_at_GHF_Pilates_GHF_Main_Gyms_with_Pilates_Pilates_Studio_2025-2.jpg" alt="Pilates pose in studio" loading="lazy"></div>
    <div class="g-item g-item--b reveal-img"><img src="{IMG}/Pilates_at_GHF_Pilates_Group_Split_2021.jpg" alt="Pilates stretch and lengthen" loading="lazy"></div>
    <div class="g-item g-item--c reveal-img"><img src="{IMG}/Pilates_Reformer_2022.jpg" alt="Pilates studio reformer" loading="lazy"></div>
  </div>
</section>

<section class="section" id="classes">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Pilates class descriptions</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Find your <span class="serif">class</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Whether you're a beginner or advanced practitioner, you'll find a class that meets your needs.</p>
    </div>
    {accordion(pilates_classes)}
  </div>
</section>
""" + f"""
<section class="section section--light" id="pass">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Try Pilates &mdash; first session free!</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Experience the Pilates <span class="serif">difference</span></h2>
        <p class="lede reveal" style="margin-top:28px">Try the Pilates Reformer under the direction of our trained Pilates instructors. They will teach you how to use the reformer, the best technique, and ways to adjust the workout to your own level. Pilates studios are located at GHF Main and GHF Tioga. Complete this form and we will be in touch to schedule your first session.</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_PILATES_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-pilates.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_PILATES_XID}">
          <input type="hidden" name="inf_form_name" value="NEW - pilates - master">
          <input type="hidden" name="infusionsoft_version" value="{KEAP_PILATES_VERSION}">
          {KEAP_PILATES_TRAPS}
          <div class="field"><input type="text" name="inf_field_FirstName" id="pil-first" placeholder=" " required><label for="pil-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="pil-last" placeholder=" " required><label for="pil-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="pil-email" placeholder=" " required><label for="pil-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="pil-phone" placeholder=" " required><label for="pil-phone">Phone</label></div>
          <div class="field field--full">
            <select name="inf_option_PickYourPilatesLocation" id="pil-loc" aria-label="Pick your Pilates location">
              <option value="">&nbsp;</option>
              <option value="3216">GHF Main &mdash; 4820 W Newberry Road</option>
              <option value="3218">GHF Tioga &mdash; Tioga Town Center</option>
            </select>
            <label for="pil-loc">Pick your Pilates location</label>
          </div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Book My Free Session <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">We will contact you via phone, email, or text. There is no charge, no obligation and no risk.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Love the way your body <span class="serif">feels</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/GHF_Pilates_Pilates_at_GHF_Pilates_GHF_Main_Gyms_with_Pilates_Pilates_Studio_2025-3.jpg",
)

# ============================================================ TRIBE
# Keap endpoint for TRIBE leads, from the hosted form behind the embed script. As with
# the PT form the hosted markup writes the .app host; we use .com to match the other
# integrations on the same pv228 tenant. Note inf_form_name carries a typo — "maseter"
# — which is reproduced verbatim because it is the string Keap matches on.
KEAP_TRIBE_ACTION = "https://pv228.infusionsoft.com/app/form/process/3e45803f6628cd4cd0b69b29d0350926"
KEAP_TRIBE_XID = "3e45803f6628cd4cd0b69b29d0350926"
tribe_body = hero(
    "TRIBE Team Training",
    ["Together we", 'achieve <span class="serif">more</span>'],
    "Train with the same crew of ten for an eight-week season. When your team expects you Tuesday at six, you show up — and showing up is where results live. Your first session is free.",
    img=f"{IMG}/GHF_Tribe_Team_Training_Small_Group_Training_Tribe_Core_Abs_Group_Fitness_Fitness_2026-1_1.jpg",
    crumb='Training &nbsp;/&nbsp; Tribe Team Training',
    actions=[("Your First Session Free", "#pass", True), ("The Programs", "#programs", False)],
    meta=["8-week seasons", "Max 10 per team", "Certified TRIBE coaches"],
    page=True,
) + marquee(["One Body", "One Unit", "One Team", "One Tribe"], accent=True) + f"""
<section class="section" id="programs">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">TRIBE program descriptions</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Choose your <span class="serif">tribe</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Each TRIBE program has a certified TRIBE Coach and up to 10 participants. The motivation and accountability you get with this team will challenge you to work harder and exceed your expectations.</p>
    </div>
  </div>
</section>
""" + split(
    "TribePUNCH", "02",
    'Lean. Fit. <span class="serif">Skilled.</span>',
    ["Introducing TribePUNCH™, a comprehensive tribe team training program designed to turn you into a formidable, lean, and skilled fighter. Boxing has earned its reputation as a top fitness trend for good reason: it's a high-energy workout that burns calories, boosts endurance, sculpts muscles, and instills unwavering confidence that extends to every aspect of your life.",
     "TribePUNCH™ caters to all fitness levels, from beginners to seasoned athletes. Our expert instructors will guide you, ensuring you not only learn the techniques but also develop mental resilience. It's time to unleash your inner fighter and become the best version of yourself — one punch at a time."],
    f"{IMG}/GHF_Tribe_Tribe_Team_Training_Tribe_Fit_Strong_Tribe_Punch_2025.jpg",
    "Tribe Punch small group training",
    tag="TribePUNCH",
) + split(
    "TribeFitSTRONG", "03",
    'Fast. Strong. <span class="serif">Fit.</span>',
    ["Welcome to FitSTRONG™, the ultimate fitness program designed to elevate your functional fitness to new heights. With a potent blend of athletic aerobic movements and functional strength exercises, FitSTRONG™ is your ticket to looking and feeling incredibly fit.",
     "Our inspirational FitSTRONG™ Coaches are your guiding lights — providing expert coaching and relentless motivation to propel you toward new levels of strength and fitness season after season. The pulse-pounding, powerful music sets the rhythm for your fitness odyssey, infusing every session with energy and intensity."],
    f"{IMG}/GHF_Tribe_Tribe_Team_Training_Tribe_Fit_Strong_Tribe_Fit_2025-2.jpg",
    "TribeFit Strong small group training",
    rev=True, tag="FitSTRONG",
) + split(
    "TribeCORE", "04",
    'Toned. Strong. <span class="serif">Powerful.</span>',
    ["TribeCORE™: Unleash Your Core Power. A comprehensive program meticulously designed to fortify the essential muscle groups encompassing your pelvis, hips, back, shoulders, and abdomen. With an initial emphasis on deep core muscles, this program not only sculpts a sleek waistline but also forges a sturdy core radiating strength and stability.",
     "Whether your goals involve perfecting your golf swing, enhancing athletic prowess, or achieving a svelte physique, TribeCORE™ is your ideal fitness companion. Expect heightened core strength, improved posture, reduced injury risk, and enhanced functional fitness."],
    f"{IMG}/GHF_Tribe_Team_Training_Small_Group_Training_Tribe_Core_Abs_Group_Fitness_Fitness_2026-3_1.jpg",
    "Tribe Core abs training",
    tag="TribeCORE",
) + split(
    "TribeLIFE", "05",
    'Active. Fit. <span class="serif">Energized.</span>',
    ["TribeLIFE™: Elevating Your Life's Fitness. A dynamic program engineered to empower you with functional fitness, ensuring you're prepared for any curveball life may hurl your way. By blending low-impact aerobic movements, functional strength exercises, and comprehensive core and flexibility training, TribeLIFE™ equips you with the vigor and resilience to tackle life's myriad challenges head-on.",
     "Whether you're a seasoned athlete looking to maintain peak performance or someone seeking to regain energy and vitality for daily activities, this program is tailored to meet your unique needs. Imagine waking up each day with boundless energy and a renewed zest for life."],
    f"{IMG}/GHF_Tribe_Team_Training_Small_Group_Training_Tribe_Core_Abs_Group_Fitness_Fitness_2026-4_1.jpg",
    "Cardio exercise in TRIBE team training",
    rev=True, tag="TribeLIFE",
) + f"""
<section class="section section--light section--tight">
  <div class="wrap">
    <figure class="quote-band reveal">
      <span class="quote-band__mark">“</span>
      <blockquote>Total Body Blast | Affordable | New Workouts Every Week</blockquote>
      <figcaption>Small Group Training at GHF Main</figcaption>
    </figure>
  </div>
</section>
""" + f"""
<section class="section" id="pass">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Realize your greatest strength &mdash; train with a team</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Get a free sesh for you <span class="serif">&amp; a friend</span></h2>
        <p class="lede reveal" style="margin-top:28px">TRIBE Team Training&trade; gives you a free session to see what it's all about. Pick from LIFE, CORE, PUNCH or FitSTRONG. Complete the form and we will contact you to schedule your free session. You are a click away from better results!</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_TRIBE_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-tribe.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_TRIBE_XID}">
          <input type="hidden" name="inf_form_name" value="tribe maseter weblead form">
          <input type="hidden" name="infusionsoft_version" value="1.70.0.1003601">
          {KEAP_TRAPS}
          <div class="field"><input type="text" name="inf_field_FirstName" id="tribe-first" placeholder=" " required><label for="tribe-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="tribe-last" placeholder=" " required><label for="tribe-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="tribe-email" placeholder=" " required><label for="tribe-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="tribe-phone" placeholder=" " required><label for="tribe-phone">Phone</label></div>
          <button class="btn field--full" type="submit" style="justify-content:center">Claim My Free Session <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">We will contact you via phone, email, or text. There is no charge, no obligation and no risk.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'One body. One unit. <span class="serif">One tribe.</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/GHF_Tribe_Tribe_Team_Training_Tribe_Fit_Strong_Tribe_Fit_2025-3.jpg",
)

# ============================================================ RECOVERY
recovery_body = hero(
    "Recovery at GHF",
    ["Recovery is part of", 'the <span class="serif">workout</span>'],
    "Cold plunge, hydromassage, sauna, steam, restorative classes and on-site physical therapy — the tools that turn sore into strong. Train hard, recover harder, and feel better than you have in years.",
    img=f"{IMG}/Chill_by_GHF_hydromassage_room_Gainesville_health_and_fitness_copy.jpg",
    crumb='Fitness &nbsp;/&nbsp; Recovery',
    actions=[("Free Guest Pass", "ghf-pass.html#claim", True)],
    meta=["The holistic approach", "Body, mind, and spirit"],
    page=True,
) + f"""
<section class="section section--tight">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">The holistic recovery approach</p>
        <h2 class="h-display reveal">That elevates every aspect of your <span class="serif">life</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">Recovery is the new face of total wellness that will transform your fitness experience beyond the ordinary and will bring you full circle to living your best life with a healthy body, mind, and spirit.</p>
      </div>
    </div>
  </div>
</section>
""" + split(
    "Indoor pool &amp; spa area", "02",
    'The restorative power of <span class="serif">water</span>',
    ["Discover the restorative power of water in our newly remodeled AQUIX Studio. Swim your way fit in our indoor lap pool, take an aqua class for a joint-friendly workout, and let your muscles and mind recover in the sauna, steam, whirlpool, and cold pool."],
    f"{IMG}/sports-activities-pool-steam-room-700x467.jpg",
    "Indoor steam room at GHF",
    cta=("Dive Into Aquix", "pool.html"), tag="Aquix Studio",
) + split(
    "Hydro massage", "03",
    'The Chill <span class="serif">Studio</span>',
    ["Relax, reduce stress, and recover from workouts and hectic schedules in our Chill Studio. Eight warm water massage lounges relax your muscles and your mind for a one-of-a-kind post-workout recovery. You will leave the gym feeling like a new person."],
    f"{IMG}/Chill_by_GHF_hydromassage_room_Gainesville_health_and_fitness_copy.jpg",
    "Hydro massage at the gym to relax and recover",
    rev=True, cta=("Explore The Chill Studio", "chill.html"), tag="Chill by GHF",
) + split(
    "ReQuest Physical Therapy", "04",
    'Experts in back <span class="serif">pain</span>',
    ["Experts in back pain with highly specialized spine strengthening equipment, researched and proven, to significantly reduce and eliminate your pain."],
    f"{IMG}/ReQuest_Physical_Therapy_Physical_Therapy_Therapists_Back_Pain_Neck_Pain_Recovery.jpg",
    "ReQuest Physical Therapy",
    tag="ReQuest PT",
) + split(
    "Group exercise classes", "05",
    'Restore and <span class="serif">repair</span>',
    ["Incorporate recovery-focused classes into your routine to work on restoring and repairing muscle to avoid injury or overuse. Offered in our GroupFit Studios, these classes allow the body and mind to slow down, which is a nice way to balance out high-intensity workouts.",
     "You will find healing and restorative elements in all levels of Yoga, Simply Stretch, Tai Chi, Body Flow, Gentle Joints, and Breathing For Life."],
    f"{IMG}/Simply_Stretch_GHF_Tioga_GroupFit_Flexibility_2023_1_1.jpg",
    "Senior fitness stretch class",
    rev=True, cta=("See class schedule", "group-fitness.html#schedule"), tag="GroupFit",
) + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="card-grid card-grid--2" data-stagger>
      <a class="card" href="jbar.html">
        <div class="card__media card__media--wide"><img src="{IMG}/smoothie_girls_web.png" alt="Smoothie bar at GHF" loading="lazy">
        <div class="card__label"><h3>J-Bar Smoothie Cafe</h3></div></div>
        <div class="card__below"><p>The J-Bar Smoothie Cafe menu is filled with healthy snacks, food and smoothies that make for the perfect fuel for your workout or enhance your recovery. Smoothies are made to order with superior fresh ingredients, including all real fruit. Enhancements such as whey protein and branched chain amino acids are available.</p></div>
      </a>
      <div class="card">
        <div class="card__media card__media--wide"><img src="{IMG}/Javi_Percussion_Gun_Massage_Gun_Massage_Therapy_2021_2.jpg" alt="Percussion massage gun recovery" loading="lazy">
        <div class="card__label"><h3>Cancer Recovery Program</h3></div></div>
        <div class="card__below"><p>Your no-charge cancer recovery program is designed to improve your physical strength and endurance and empower you to gain control of your life. You will be introduced to strength training, aerobic, and flexibility training at a gradual pace as you work with a fitness counselor to monitor your progress.</p></div>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Rest is part of the <span class="serif">work</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/Aqua_GHF_Aquix_Cold_Plunge_Cold_Therapy_Pool_2023_1.jpg",
)

# ============================================================ KIDS CLUB
kids_body = hero(
    "Kid's Club at GHF",
    ["You work out.", "We've got the <span class=\"serif\">kids</span>."],
    "Two free hours of trained, attentive childcare every day, at all three clubs — ages 6 weeks to 12 years. The class, the weights, the sauna: they're yours again. Included with every membership.",
    img=f"{IMG}/kids_club.jpg",
    crumb="Kid's Club",
    actions=[("Get Your Free Pass", "#pass", True), ("Kids Club Hours", "#hours", False)],
    meta=["Ages 6 weeks – 12 years", "Up to 2 hours per day", "No extra charge"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Included in every membership</p>
        <h2 class="h-display reveal">At no extra <span class="serif">charge</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">GHF Kid's Club is a fun, active space your kids will look forward to visiting. Kid's Club staff are specially trained to provide a caring and educational environment. Every precaution is taken to ensure your children will be safe and well cared for.</p>
        <p class="body-copy reveal">As a GHF member, Kid's Club rules allow your children ages 6-weeks to 12-years-old to enjoy the Kid's Club for up to two hours per day while you take advantage of the other amenities of our world-class fitness facility.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--flush">
  <div class="gallery wrap">
    <div class="g-item g-item--a reveal-img"><img src="{IMG}/kids_club2.jpg" alt="Babysitting at GHF Kid's Club" loading="lazy"></div>
    <div class="g-item g-item--b reveal-img"><img src="{IMG}/just-families-kids-club-fun1-700x467.jpg" alt="Kids having fun at Kid's Club" loading="lazy"></div>
    <div class="g-item g-item--c reveal-img"><img src="{IMG}/just-families-kids-club-baby-xylophone-576-260.jpg" alt="Baby playing xylophone at Kid's Club" loading="lazy"></div>
  </div>
</section>

<section class="section" id="hours">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Kids Club hours</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Three locations, all <span class="serif">covered</span></h2>
      </div>
    </div>
    <div class="sched" data-stagger>
      <div class="sched__col">
        <h4>GHF Main</h4><span class="where">4820 W Newberry Road</span>
        <dl>
          <div><dt>Mon–Fri</dt><dd>8am–1pm, 3pm–8:30pm</dd></div>
          <div><dt>Saturday</dt><dd>8am–2pm</dd></div>
          <div><dt>Sunday</dt><dd>10am–5pm</dd></div>
        </dl>
      </div>
      <div class="sched__col">
        <h4>GHF Tioga</h4><span class="where">12830 SW 1st Lane</span>
        <dl>
          <div><dt>Mon–Fri</dt><dd>8am–1pm, 3pm–8pm</dd></div>
          <div><dt>Saturday</dt><dd>8am–3pm</dd></div>
          <div><dt>Sunday</dt><dd>10am–5pm</dd></div>
        </dl>
      </div>
      <div class="sched__col">
        <h4>GHF Women</h4><span class="where">2441 NW 43rd Street</span>
        <dl>
          <div><dt>Mon–Thu</dt><dd>8am–1pm, 3pm–8pm</dd></div>
          <div><dt>Friday</dt><dd>8am–1pm, 3pm–7pm</dd></div>
          <div><dt>Saturday</dt><dd>8am–1pm</dd></div>
          <div><dt>Sunday</dt><dd>Closed</dd></div>
        </dl>
      </div>
    </div>
  </div>
</section>
""" + form_section(
    "pass", "03", "Request your free guest pass",
    'Your free all-access pass is <span class="serif">waiting</span>',
    "With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health &amp; Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired.",
    "Claim My Free Pass",
) + cta_band(
    'Your kids will bring <span class="serif">you</span> to the gym',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/just-families-kids-club-fun2-700x467.jpg",
)

# ============================================================ WEIGHT LOSS
weightloss_body = hero(
    "Weight Loss at GHF",
    ["Lose it for the", '<span class="serif">last time</span>'],
    "Diets end. Plans built around your real life don't. Pick your path — one-on-one training, X-Force, TRIBE, CrossFit or 800+ classes — with coaches who keep you honest until the mirror agrees.",
    img=f"{IMG}/GHF_F2F_Face_2_Face_Weight_Loss_Fitness_Progress.jpg",
    crumb='Fitness &nbsp;/&nbsp; Weight Loss',
    actions=[("Try GHF For Free", "ghf-pass.html#claim", True)],
    meta=["Programs for every level", "Experts included"],
    page=True,
) + split(
    "Personal Training", "01",
    'One-on-one support and <span class="serif">accountability</span>',
    ["Benefit from the guidance and motivation of a certified personal trainer. One-on-one personal training sessions provide the individual support and accountability you need to lose weight safely and effectively. We have the industry's best, most compassionate personal trainers."],
    f"{IMG}/Personal_Training_Hamstring_Stretch_Certified_Trainer_Flexibility_PT_2022.jpg",
    "Personal training at GHF one on one",
    cta=("Personal Training", "personal-training.html"), tag="Personal Training",
) + split(
    "X-Force Body", "02",
    'Outstanding results, 1–2 workouts a <span class="serif">week</span>',
    ["Combining negative training with a strategic carb-rich eating plan, the innovative X-Force Body system helps you shed fat, build muscle and reshape your body. Experience outstanding results with just 1-2 workouts a week."],
    f"{IMG}/XForce_XForce_Body_GHF_Gain_Muscle_Leg_Exercises_2023.jpg",
    "X-Force Body fat loss leg machine",
    rev=True, cta=("X-Force Body", "xforce.html"), tag="X-Force Body",
) + split(
    "TRIBE Team Training", "03",
    'The team approach to a higher level of <span class="serif">fitness</span>',
    ["A small group training program that focuses on the team approach to reach a higher level of fitness. Experience support, belonging and challenge in a dynamic motivating environment that will respect your individuality to achieve more. We are one body, one unit, one team, one tribe."],
    f"{IMG}/GHF_Tribe_Team_Training_Small_Group_Training_Tribe_Core_Abs_Group_Fitness_Fitness_2026-1_1.jpg",
    "Tribe strength training",
    cta=("TRIBE Team Training", "tribe.html"), tag="TRIBE",
) + split(
    "CrossFit at GHF", "04",
    'Results you never <span class="serif">imagined</span>',
    ["CrossFit at Gainesville Health &amp; Fitness thrives on the pursuit of optimal fitness. The combination of high intensity, camaraderie and competition will give you the motivation to achieve results you never imagined possible."],
    f"{IMG}/GHF_CrossFit_at_GHF_CrossFit_in_Gainesville_Gainesville_Gyms_Gyms_Workout_Fitness_Cardio_Strength_2025-1.jpg",
    "CrossFit turf at Gainesville Health & Fitness — athletes warming up",
    rev=True, cta=("CrossFit at GHF", "crossfit.html"), tag="CrossFit",
) + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="card-grid card-grid--2" data-stagger>
      <div class="card">
        <div class="card__media card__media--wide"><img src="{IMG}/stockhiphop.jpg" alt="Lose weight with group fitness" loading="lazy">
        <div class="card__label"><h3>Group Classes</h3></div></div>
        <div class="card__below"><p>At Gainesville Health &amp; Fitness, we offer more than 800 group exercise classes per month across our three locations. There's something for everyone, from beginner to the advanced, including yoga, Zumba, step, body pump and so much more.</p></div>
      </div>
      <div class="card">
        <div class="card__media card__media--wide"><img src="{IMG}/tioga_line.jpg" alt="The Line strength training circuit at GHF Tioga" loading="lazy">
        <div class="card__label"><h3>Cardio and Strength</h3></div></div>
        <div class="card__below"><p>Mixing cardiovascular exercise with strength training is the surest way to lose weight and keep it off. We offer the area's largest selection of state-of-the-art equipment, with friendly staff who are always available to explain how everything works. Our strength training circuit, "The Line," provides an ideal workout structure for rookie exercisers.</p></div>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Reaching your goal doesn\'t have to be a <span class="serif">struggle</span>',
    "With three centers to choose from, Gainesville Health & Fitness is here to help you succeed. Become a GHF member today for as little as $15 per week.",
    f"{IMG}/punch1.jpg",
)

# ============================================================ LOCATIONS
locations_body = hero(
    "Locations &amp; Hours",
    ["Three clubs.", 'Zero <span class="serif">excuses</span>.'],
    "One membership unlocks all three: the 24/7 flagship on Newberry Road, Gainesville's only women-only club, and the family-friendly Tioga center. Wherever your day takes you, your gym is already there.",
    img=f"{IMG}/GHF_Tioga_Gainesville_Health_Gainesville_Gyms_TIoga_Strength_Gyms_Nearby_2026-2.jpg",
    crumb="Locations and Hours",
    actions=[("Get Your Free All-Access Pass", "ghf-pass.html#claim", True)],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="loc">
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg" alt="Free weight area at GHF Main" loading="lazy"></div>
        <div>
          <span class="loc-badge">Open 24/7</span>
          <h3><a href="main-center.html">GHF Main</a></h3>
          <a class="phone" href="tel:3523774955">(352) 377-4955</a>
          <div class="loc-hours">
            <div><dt>Every day</dt><dd>Open 24 hours</dd></div>
          </div>
          <address>4820 W Newberry Road, Gainesville, FL 32607<br>General Manager — Adrian Antigua</address>
          <div class="hero__actions" style="opacity:1;transform:none;margin-top:26px">
            <a class="btn btn--sm" href="main-center.html">Explore GHF Main <span class="arr">→</span></a>
          </div>
        </div>
      </div>
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/GHF_GHF_Women_Womens_Center_Body_Pump_2023_1.jpg" alt="Body Pump class at GHF Women" loading="lazy"></div>
        <div>
          <span class="loc-badge">Women Only</span>
          <h3><a href="womens-center.html">GHF Women</a></h3>
          <a class="phone" href="tel:3523744634">(352) 374-4634</a>
          <div class="loc-hours">
            <div><dt>Mon–Thurs</dt><dd>5am–9pm</dd></div>
            <div><dt>Friday</dt><dd>5am–8pm</dd></div>
            <div><dt>Saturday</dt><dd>8am–6pm</dd></div>
            <div><dt>Sunday</dt><dd>Closed</dd></div>
          </div>
          <address>2441 NW 43rd Street, Gainesville, FL 32606<br>Manager — Jordan Heitzler</address>
          <div class="hero__actions" style="opacity:1;transform:none;margin-top:26px">
            <a class="btn btn--sm" href="womens-center.html">Explore GHF Women <span class="arr">→</span></a>
          </div>
        </div>
      </div>
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/GHF_Tioga_Gainesville_Health_Gainesville_Gyms_TIoga_Strength_Gyms_Nearby_2026-2.jpg" alt="Strength training at GHF Tioga" loading="lazy"></div>
        <div>
          <span class="loc-badge">Family Friendly</span>
          <h3><a href="tioga-center.html">GHF Tioga</a></h3>
          <a class="phone" href="tel:3526922180">(352) 692-2180</a>
          <div class="loc-hours">
            <div><dt>Mon–Thurs</dt><dd>5am–10pm</dd></div>
            <div><dt>Friday</dt><dd>5am–9pm</dd></div>
            <div><dt>Saturday</dt><dd>8am–8pm</dd></div>
            <div><dt>Sunday</dt><dd>10am–5pm</dd></div>
          </div>
          <address>12830 SW 1st Lane, Suite 100, Newberry, FL 32669<br>Manager — Darrius Powell</address>
          <div class="hero__actions" style="opacity:1;transform:none;margin-top:26px">
            <a class="btn btn--sm" href="tioga-center.html">Explore GHF Tioga <span class="arr">→</span></a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
""" + stats_band([
    (3, "", "Gyms in greater Gainesville"),
    (1, "", "Membership covers them all"),
    (24, "/7", "Access at GHF Main"),
    (300, "+", "Staff across all locations"),
]) + cta_band(
    'Find the gym that\'s right for <span class="serif">you</span>',
    "Each location is unique and offers a different experience and value. You have access to all 3 locations (GHF Women is women only).",
    f"{IMG}/Echo_GroupFit_Outdoor_Classes_Fun_Classes_2021.jpg",
    primary=("Claim Your Free Fitness Pass", "ghf-pass.html#claim"),
    secondary=("Get Membership Pricing", "contact.html#pricing"),
)

# ============================================================ CONTACT
# Keap / Infusionsoft endpoint for the "Request Pricing" campaign, copied from the
# live form at ghfc.com/request-prices. That page's customFormAction carries a
# 31-character id while its inf_form_xid is the full 32 — Keap ids are 32 hex chars
# and the working pass form uses the xid as its action path, so we use the xid.
KEAP_PRICING_ACTION = "https://pv228.infusionsoft.com/app/form/process/02baff34d43e7db270bb0297c1bcc05e"
KEAP_PRICING_XID = "02baff34d43e7db270bb0297c1bcc05e"

contact_body = hero(
    "Contact GHF",
    ["Let's talk", '<span class="serif">fitness</span>'],
    "Tell us your goal and we'll map the membership to match — classes, pool, training, all of it. No pressure, no scripts. Just real people who'd love to show you around.",
    img=f"{IMG}/GHF_Careers_Floor_Instructor_Fitness_Jobs_Service.jpg",
    crumb="Contact Us",
    actions=[("Request Gym Pricing", "#pricing", True), ("Call (352) 377-4955", "tel:3523774955", False)],
    page=True,
) + f"""
<section class="section section--light" id="pricing">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Request gym pricing</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Get pricing for Gainesville's best <span class="serif">gym</span></h2>
        <ul class="checklist reveal" style="margin-top:34px">
          <li>24-hour access at GHF Main</li>
          <li>Staff to help you every time</li>
          <li>800+ fitness classes each month</li>
          <li>One membership, 3 locations</li>
          <li>GHF Women only location</li>
          <li>Indoor basketball and volleyball</li>
          <li>Renovated indoor heated pools</li>
          <li>Sauna, steam, hot tub, cold pool</li>
          <li>Full-time housekeeping</li>
          <li>Free lockers</li>
          <li>Free babysitting</li>
          <li>Member savings program</li>
          <li>Largest variety of cardio &amp; weight machines</li>
        </ul>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_PRICING_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-pricing.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_PRICING_XID}">
          <input type="hidden" name="inf_form_name" value="Request Pricing">
          <input type="hidden" name="infusionsoft_version" value="1.70.0.119516">
          <input type="hidden" name="inf_IntegrationName" value="pv228">
          <input type="hidden" name="inf_CallName" value="RequestPricing">
          <input type="hidden" name="inf_api_enabled" value="true">
          <div class="field"><input type="text" name="inf_field_FirstName" id="p-first" placeholder=" " required><label for="p-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="p-last" placeholder=" " required><label for="p-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="p-email" placeholder=" " required><label for="p-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="p-phone" placeholder=" "><label for="p-phone">Phone</label></div>
          <div class="field field--full">
            <select name="inf_custom_Facility" id="p-loc" aria-label="Preferred location">
              <option value="">&nbsp;</option>
              <option value="Main">GHF Main &mdash; 4820 Newberry Road</option>
              <option value="Women&#39;s Center">GHF Women &mdash; 2441 NW 43rd Street</option>
              <option value="Tioga">GHF Tioga &mdash; Tioga Town Center</option>
            </select>
            <label for="p-loc">Preferred location</label>
          </div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Request Pricing <span class="arr">→</span></button>
        </form>
        <p class="form-note">Complete the form and we will set up a convenient time to present your options. We will contact you via phone, email, or text. One gym membership. Three locations.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Directory of staff</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Talk to a real <span class="serif">person</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">For membership inquiries please contact <a href="mailto:memberservices@ghfc.com" style="color:var(--accent)">memberservices@ghfc.com</a> or call <a href="tel:3523774955" style="color:var(--accent)">(352) 377-4955</a>.</p>
    </div>
    {accordion([
        ("Fitness Counselors — GHF Main",
         '<ul><li>Karen Coley-Cannon — karen.coley-cannon@ghfc.com</li><li>Debra Johnson-Meisel — debra.johnson-meisel@ghfc.com</li><li>Donte Jones — donte.jones@ghfc.com</li><li>Chris Adam — chris.adam@ghfc.com</li><li>Jayson Hoac — jayson.hoac@ghfc.com</li></ul>'),
        ("Fitness Counselors — GHF Tioga",
         '<ul><li>Jan Campbell — jan.campbell@ghfc.com</li><li>Sam Moore — sam.moore@ghfc.com</li><li>Kaaren Gillmore — kaaren.gillmore@ghfc.com</li><li>Corinne Jacobs — corinne.jacobs@ghfc.com</li><li>Erin Coleman — erin.coleman@ghfc.com</li></ul>'),
        ("Center Managers",
         '<ul><li>Ann Raulerson — GHF Main — ann.raulerson@ghfc.com</li><li>Darrius Powell — GHF Tioga — darrius.powell@ghfc.com</li><li>Jordan Heitzler — GHF Women — jordan.heitzler@ghfc.com</li><li>Adrian Antigua — adrian.antigua@ghfc.com</li></ul>'),
        ("Program Directors",
         '<ul><li>Matt Mallard — Personal Training — matt.mallard@ghfc.com</li><li>Robin Zukowski — Pilates — robin.zukowski@ghfc.com</li><li>Lauren Rohrs — CrossFit — lauren.rohrs@ghfc.com</li><li>Shelly Ward — Tribe Team Training — shelly.ward@ghfc.com</li><li>Shawn Hinds — GroupFit — shawn.hinds@ghfc.com</li><li>Kyle Morgan — X-Force Body — kyle.morgan@ghfc.com</li><li>Gracie Dexter — Kids Club — gracie.dexter@ghfc.com</li></ul>'),
        ("Leadership &amp; Services",
         '<ul><li>Joe Cirulli — joe.cirulli@ghfc.com</li><li>Sally Martyniak — sally.martyniak@ghfc.com</li><li>Debbie Lee — debbie.lee@ghfc.com</li><li>Paula Fraisse — paula.fraisse@ghfc.com</li><li>Pete Dougherty — pete.dougherty@ghfc.com</li><li>Adrienne Vihlen — Retail Manager — adrienne.vihlen@ghfc.com</li><li>Gabriel Castlen — JBar — gabriel.castlen@ghfc.com</li></ul>'),
    ], open_first=False)}
  </div>
</section>
""" + cta_band(
    'We look forward to <span class="serif">meeting you</span>',
    "Get ready for an experience that will help you get the most out of life and inspire you to become your best.",
    f"{IMG}/GHF_Careers_Floor_Instructor_Fitness_Jobs_Service.jpg",
    primary=("Request Pricing", "#pricing"), secondary=None,
)

# ============================================================ JOIN ONLINE
join_body = hero(
    "Join Online — Memberships from $29.99 + tax",
    ["Join Gainesville's", 'best gym — <span class="serif">online</span>'],
    'Be part of Gainesville\'s largest, state-of-the-art fitness community, where your membership connects you to expert guidance, innovative programs, and top-tier amenities for both physical and mental well-being. <em>Must be 18 years or older to join without parent or guardian. Not quite ready to join? <a href="ghf-pass.html#claim" style="color:var(--accent-soft)">Try GHF with a free gym pass</a>.</em>',
    img=f"{IMG}/join-today-bg.jpg",
    crumb="Join Online",
    actions=[("Start My Membership", "#start", True), ("Or Call (352) 377-4955", "tel:3523774955", False)],
    promo=[
        'All memberships are less than <strong>$16</strong> a week',
        "One membership, 3 locations",
    ],
    page=True,
) + f"""
<div class="jn-modal" id="joinModal" hidden role="dialog" aria-modal="true" aria-label="Join online">
  <div class="jn-modal__bar">
    <div class="jn-modal__brand">Gainesville Health &amp; Fitness <em>join</em></div>
    <div class="jn-modal__sec">Secure enrollment</div>
    <button class="jn-modal__close" type="button" data-join-close aria-label="Close">&times;</button>
  </div>
<section class="jn" id="wizard" aria-label="Join online">
  <div class="jn-rail" role="list" aria-label="Steps">
    <div class="rl on" id="s1" role="listitem"><b>01</b><span>Home club</span></div>
    <div class="rl" id="s2" role="listitem"><b>02</b><span>Membership</span></div>
    <div class="rl" id="s3" role="listitem"><b>03</b><span>Your details</span></div>
    <div class="rl" id="s4" role="listitem"><b>04</b><span>Recurring dues</span></div>
    <div class="rl" id="s5" role="listitem"><b>05</b><span>Due today</span></div>
  </div>
  <div class="jn-wrap">
    <div>
      <section id="c1"><p class="kick">Step one</p>
        <h1>Pick your <span class="serif">home</span> club</h1>
        <p class="jn-lede">One membership opens all three. Train wherever the day takes you.</p>
        <div class="panel" id="clubs"></div>
        <button class="jn-btn" type="button" data-go="2">Continue</button></section>

      <section id="c2" class="hide"><p class="kick">Step two</p>
        <h1>Choose your <span class="serif">membership</span></h1>
        <p class="jn-lede">Every plan is $29.99 + tax every other Wednesday — and there is no maintenance fee, ever.</p>
        <div class="panel" id="plans"></div>
        <p class="kick" style="margin-top:34px">Optional add-ons</p><div id="addons"></div>
        <button class="jn-btn ghost" type="button" data-go="1">Back</button>
        <button class="jn-btn" type="button" data-go="3">Continue</button></section>

      <section id="c3" class="hide"><p class="kick">Step three</p>
        <h1>Tell us <span class="serif">about you</span></h1>
        <p class="jn-lede">Must be 18 years or older to join without a parent or guardian.</p>
        <form class="panel" id="detailsForm" novalidate>
          <div class="g2"><div><label for="firstName">First name</label><input id="firstName" name="firstName" autocomplete="given-name" required></div>
            <div><label for="lastName">Last name</label><input id="lastName" name="lastName" autocomplete="family-name" required></div></div>
          <div class="g2"><div><label for="email">Email</label><input id="email" name="email" type="email" autocomplete="email" required></div>
            <div><label for="phone">Mobile</label><input id="phone" name="phone" type="tel" autocomplete="tel" required></div></div>
        </form>
        <div class="field-err" id="detailsErr" hidden></div>
        <button class="jn-btn ghost" type="button" data-go="2">Back</button>
        <button class="jn-btn" type="button" id="toPay">Continue to payment</button>
        <div id="mOut"></div></section>

      <section id="c4" class="hide"><p class="kick">Step four · nothing is charged now</p>
        <h1>Set up your <span class="serif">recurring</span> dues</h1>
        <p class="jn-lede">Choose how we draft your dues every other Wednesday. You'll pay today's total on the next step.</p>
        <div class="panel" id="recChoice">
          <label class="opt sel" data-m="CC"><span class="tick"></span>
            <div class="nm">Credit / debit card</div>
            <div class="nt">Can also cover today's total — nothing to re-enter.</div></label>
          <label class="opt" data-m="ACH"><span class="tick"></span>
            <div class="nm">Bank draft · ACH</div>
            <div class="nt">Simplest for ongoing dues. A card is still required for today's total.</div></label>
        </div>
        <input class="ipayfield" data-ipayname="account"   type="hidden" id="ipay-account">
        <input class="ipayfield" data-ipayname="amount"    type="hidden" id="ipay-amount" value="0.00">
        <input class="ipayfield" data-ipayname="firstname" type="hidden" id="ipay-first">
        <input class="ipayfield" data-ipayname="lastname"  type="hidden" id="ipay-last">
        <input class="ipayfield" data-ipayname="email"     type="hidden" id="ipay-email">
        <input class="ipayfield" data-ipayname="phone"     type="hidden" id="ipay-phone">
        <input class="ipayfield" data-ipayname="invoice"   type="hidden" id="ipay-invoice">
        <button class="jn-btn" type="button" id="vaultBtn" disabled>Save payment method</button>
        <div class="lock"><span id="tstatus">Preparing secure window…</span></div>
        <p class="lock">🔒 Entered directly with our payment processor. GHF never sees your card or account number.</p>
        <div id="recOut"></div></section>

      <section id="c5" class="hide"><p class="kick">Step five</p>
        <h1>Total due <span class="serif">today</span></h1>
        <div class="panel" id="todayBox"></div><div id="payOut"></div></section>

      <section id="c6" class="hide"><p class="kick">Welcome to GHF</p>
        <h1>You're <span class="serif">in</span>.</h1>
        <div class="panel" id="done"></div>
        <a class="jn-btn" href="group-fitness.html">Browse classes</a>
        <a class="jn-btn ghost" href="index.html">Back to home</a></section>
    </div>
    <aside><div class="jn-cart"><h3>Your cart</h3><div class="in" id="cart"><div class="ln">Pick a plan to see today's total</div></div></div></aside>
  </div>
</section>
</div>

<section class="section section--light">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Every GHF membership includes</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">The benefits and amenities of Gainesville's best <span class="serif">gym</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">With a strong culture of service, every employee goes above and beyond to help you reach your full potential. You're going to feel good here.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>24-hour access at GHF Main</li>
          <li>Fitness staff to help you every time</li>
          <li>900+ free fitness classes each month</li>
          <li>Free hot yoga classes</li>
          <li>Largest variety of cardio &amp; weight training machines</li>
          <li>One membership, 3 locations</li>
          <li>GHF Women only fitness location</li>
          <li>Indoor basketball and volleyball</li>
          <li>Renovated indoor heated pools</li>
          <li>Sauna, steam, hot tub, cold pool</li>
          <li>Full-time housekeeping</li>
          <li>Free lockers</li>
          <li>Free babysitting</li>
          <li>Member savings program</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="pillars" data-stagger style="grid-template-columns:repeat(3,1fr)">
      <div class="pillar"><span class="pillar__num">Our Expertise</span><h3>Helping beginners get started</h3></div>
      <div class="pillar"><span class="pillar__num">Our Passion</span><h3>Guiding you to break out of your comfort zone and unleash your fullest potential</h3></div>
      <div class="pillar"><span class="pillar__num">Our Promise</span><h3>You're going to feel good here</h3></div>
    </div>
  </div>
</section>

<script>window.GHF_JOIN_API={JOIN_API_JSON};</script>
<script src="assets/js/join.js?v={V}" defer></script>
""" + cta_band(
    'Or call <span class="serif">(352) 377-4955</span> today',
    "Not quite ready to join? Try GHF with a free gym pass — there is no charge, no obligation and no risk.",
    f"{IMG}/GHF_Careers_Floor_Instructor_Fitness_Jobs_Service.jpg",
    primary=("Try GHF For Free", "ghf-pass.html#claim"),
    secondary=("Request Pricing &amp; More Info", "contact.html#pricing"),
)

# ============================================================ TRAINING OVERVIEW
training_body = hero(
    "GHF Signature Training Programs",
    ["You bring the goal.", "We'll match the <span class=\"serif\">program</span>."],
    "Six coached paths to your strongest self — one-on-one, small team, reformer, negative training, CrossFit, or HYROX. Different styles, same outcome: you, with a coach, getting somewhere. First sessions are free.",
    img=f"{IMG}/GHF_Gainesville_Health_Gyms_Gainesville_Personal_Training_Training_Fitness_2026-4.jpg",
    crumb="Training",
    actions=[("Request Your Free Trial Workout", "#trial", True)],
    meta=["6 signature programs", "Expert coaches", "Free trial session"],
    page=True,
) + split(
    "One-on-one coaching", "01",
    'Find motivation through customized <span class="serif">training</span>',
    ["One-on-one experts in motivation, accountability and program design to help you re-start your exercise routine, get to the gym regularly, or get in shape with orthopedic or medical limitations. A perfect choice when you need your own exercise program written every week to balance strength and weaknesses for best results.",
     "You will benefit from the combined knowledge, training and practice of 40 specialized, nationally certified Personal Trainers. Let us customize your workout to help you enjoy life to the fullest."],
    f"{IMG}/Personal_Training_Legs_Training_2021_1.jpg",
    "Personal trainer working one on one with a client",
    cta=("Get A Free Assessment", "personal-training.html"), tag="Personal Training",
    name="Personal Training", href="personal-training.html",
) + split(
    "Reformer &amp; mat", "02",
    'Sculpt your body and restore your <span class="serif">mind</span>',
    ["Pilates is a comprehensive movement program that speaks to everyone, helping clients develop proper alignment and stabilization, giving all bodies the gift of freedom in movement. A strong core radiates, bringing strength to the whole self.",
     "Develop a lean, toned body while enjoying an environment of complete focus. Our Certified Pilates Instructors will guide you towards body awareness, flexibility and strength, all while helping you achieve your fitness goals."],
    f"{IMG}/pilatescrop.jpg",
    "Private Pilates at GHF",
    rev=True, cta=("New To Pilates Package", "pilates.html"), tag="Pilates",
    name="Pilates", href="pilates.html",
) + split(
    "Train with a community", "03",
    'Find motivation through <span class="serif">community</span>',
    ["Become a part of a fitness community that creates a balance of camaraderie and competition to help you reach your fitness goals that are difficult to achieve on your own. Our coaches are committed to making our members stronger, better, and more self-confident through their fitness journey.",
     "GHF CrossFit is now open to the community. You do not have to be a GHF member to enroll."],
    f"{IMG}/crossfitcrop.jpg",
    "CrossFit at GHF",
    cta=("Explore CrossFit — Your First Class Is Free", "crossfit.html"), tag="CrossFit",
    name="CrossFit", href="crossfit.html",
) + split(
    "Negative training", "04",
    'Shed some serious fat in 6 <span class="serif">weeks</span>',
    ["The only fat loss and muscle gain program in the country delivering results with just two 25-minute workout sessions a week. Experience a combination of negative training, carb-friendly diet plan, super-hydration, and stress reduction practices to shed fat, build muscle, and reshape your body with remarkable self-confidence.",
     "Get ready, your journey to a leaner, stronger, healthier body is beginning now."],
    f"{IMG}/xforce_body_daryl_and_client_with_logo_for_website.jpg",
    "Coach and client on X-Force negative weight machines",
    rev=True, cta=("Schedule A Discovery Session", "xforce.html"), tag="X-Force Body",
    name="X-Force Body", href="xforce.html",
) + split(
    "Small team training", "05",
    'Find motivation through <span class="serif">teamwork</span>',
    ["TRIBE Team Training™ offers the best in small team training to deliver the promise \"together everyone will achieve more.\" You will work with a team of up to 10 members and one coach for 8 weeks to motivate and to be motivated for better results.",
     "Experience support, belonging and challenge in a dynamic motivating environment that will respect your individuality to achieve more. Choose between TRIBE Core, TRIBE Life, TRIBE Punch or TRIBE Fit."],
    f"{IMG}/tribe_line.jpg",
    "TRIBE small team training at GHF",
    cta=("Find Your Tribe", "tribe.html"), tag="TRIBE",
    name="TRIBE Team Training", href="tribe.html",
) + split(
    "Official training club", "06",
    'Run, lift, repeat — eight <span class="serif">times</span>',
    ["Gainesville Health &amp; Fitness is an official HYROX Training Club — the world's fastest-growing fitness format, right here in Gainesville. Eight one-kilometre runs, eight functional stations, the same every time, so you always know what's coming and exactly how much you have improved.",
     "Train on the exact equipment used on race day, coached for every level. Chasing a podium finish or just after the most effective workout you have ever done — both belong here."],
    f"{IMG}/hyrox-sled.jpg",
    "Athlete pushing a HYROX sled at GHF",
    rev=True, cta=("Explore HYROX Training", "hyrox.html"), tag="HYROX",
    name="HYROX", href="hyrox.html",
) + form_section(
    "trial", "07", "Request your free trial workout",
    'Your complimentary workout is a click <span class="serif">away</span>',
    "The best way to pick the signature program best for you is to try a complimentary session. Experience the style of workout, environment, and trainer to see if it's right for you. Accelerate your results with the experts of Personal Training, X-Force Body, Pilates, CrossFit, and TRIBE Team Training. They will guide you to the results you want to reconnect with life!",
    "Request Free Trial",
    select=("program", "Which program interests you?", [
        "Personal Training", "Pilates", "CrossFit", "X-Force Body",
        "TRIBE Team Training", "Hyrox", "Team Strong Training",
    ]),
) + cta_band(
    'The expertise you need to get <span class="serif">better results</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/Hero_Shot_PT_Page_Debra_and_Adam_Personal_Training_2021.jpg",
)

# ============================================================ CROSSFIT
# Keap endpoint for CrossFit leads, from the hosted form behind the embed script. As
# with the other integrations the hosted markup writes the .app host; we use .com to
# match them. Note Keap marks none of these four fields required — we require all four
# client-side anyway, since a lead with no email or phone is not actionable.
KEAP_CF_ACTION = "https://pv228.infusionsoft.com/app/form/process/64b5d74a95b373f9169385e579053258"
KEAP_CF_XID = "64b5d74a95b373f9169385e579053258"
crossfit_body = hero(
    "CrossFit at GHF Tioga",
    ["The best hour of", 'your <span class="serif">day</span>'],
    "Workouts you'd never finish alone become the thing you can't stop talking about. Coaches scale every WOD to your level, and the community learns your name by week one. Open to everyone — no GHF membership required.",
    img=f"{IMG}/GHF_CrossFit_at_GHF_CrossFit_in_Gainesville_Gainesville_Gyms_Gyms_Workout_Fitness_Cardio_Strength_2025-1.jpg",
    crumb='Training &nbsp;/&nbsp; CrossFit',
    actions=[("Try A Free Class", "#pass", True), ("What To Expect", "#expect", False)],
    meta=["Open to the community", "Certified coaches", "Free first class"],
    page=True,
) + f"""
<section class="section" id="expect">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Try a free CrossFit class</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Your first time on the <span class="serif">turf</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Want to see what CrossFit is all about? Try a free trial class and one of our coaches will guide you through a CrossFit workout. Here's what to expect:</p>
    </div>
    <div class="steps reveal">
      <div class="step"><span class="step__num">01</span><h3>Introduction</h3><p>We'll learn about your goals, current workout regimen, and any injuries or pre-existing conditions you may have.</p></div>
      <div class="step"><span class="step__num">02</span><h3>Warm-Up</h3><p>10 minutes of mobility movements to get you warm and prepared for the work ahead.</p></div>
      <div class="step"><span class="step__num">03</span><h3>Exercise Review</h3><p>Moving safely and effectively is always our top goal and you will be led through the workout with a coach's guidance from beginning to end.</p></div>
      <div class="step"><span class="step__num">04</span><h3>The WOD</h3><p>WOD stands for Workout Of The Day. CrossFit WODs typically start with a strength portion that leads into a cardio training segment performed circuit-style. We'll give you a WOD to meet your current fitness level — rest assured there will be no pressure to over-do it.</p></div>
      <div class="step"><span class="step__num">05</span><h3>Cool-Down</h3><p>A few finishing stretches and accessory movements to bring your heart rate back down safely. Bring a water bottle and a towel, wear comfortable gym attire and shoes, and check in at the lobby desk before heading out to the CrossFit Turf.</p></div>
    </div>
  </div>
</section>
""" + split(
    "Private CrossFit sessions", "02",
    'Get one-on-one <span class="serif">training</span>',
    ["Unlock your full potential with our 1-on-1 personal training sessions tailored to your individual goals. Whether you're looking to build strength, master gymnastics skills, improve your cardio, or enhance overall fitness, our expert coaches are here to guide you every step of the way.",
     "Each session is customized to address your unique needs and help you achieve results faster. Contact Lauren at lauren.rohrs@ghfc.com for more information."],
    f"{IMG}/Crossfit_at_GHF_Coaches_2026_1.jpg",
    "CrossFit coaches at the outdoor covered turf at GHF",
    cta=("Get Your Free Session", "#pass"), tag="1-On-1",
) + split(
    "Olympic lifting by GHF CrossFit", "03",
    'Master the snatch and clean &amp; <span class="serif">jerk</span>',
    ["<strong>Monday &amp; Wednesday at 5:30p.</strong> Our Olympic lifting class focuses on developing proficiency in the Olympic lifts through a combination of mobility work, technique refinement, and strength building.",
     "Whether you're aiming to enhance your CrossFit performance or simply want to master the snatch and clean and jerk, this class offers targeted training to help you succeed. Our CrossFit coaches guide you through every phase of the lift."],
    f"{IMG}/GHF_CrossFit_Fitness_Exercise_Outdoors_Group_Fitness_Crossfit_Gainesville_2024-07.jpg",
    "CrossFit athletic weight training",
    rev=True, tag="Oly Lifting",
) + split(
    "Youth fitness — ages 6–12", "04",
    'CrossFit for <span class="serif">kids</span>',
    ["<strong>Monday, Tuesday &amp; Thursday 4:30–5:15p.</strong> This class is designed to prepare young people to perform proper movement and create healthy habits for their future.",
     "Participants will learn to prioritize form and gain more control and awareness of their body within a fun group environment. Once your CrossFit Youth Athlete turns 13, we will transition him/her to adult CrossFit."],
    f"{IMG}/GHF_CrossFit_Kids_Exercise_CrossFit_for_Kids_Tioga_2026.jpg",
    "Kids CrossFit class bear crawl exercise",
    tag="Youth Camp",
) + f"""
<section class="section section--light" id="pass">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Your free CrossFit class</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Try CrossFit for <span class="serif">free</span></h2>
        <p class="lede reveal" style="margin-top:28px">Try CrossFit under the direction of certified CrossFit coaches to teach you the mechanics and safety of W.O.D.s. Try CrossFit in our newly renovated, covered space at GHF Tioga. New equipment and classes too. Simply complete the form and we will contact you to set up your free class.</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_CF_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-crossfit.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_CF_XID}">
          <input type="hidden" name="inf_form_name" value="CrossFit web form">
          <input type="hidden" name="infusionsoft_version" value="1.70.0.1003601">
          {KEAP_TRAPS}
          <div class="field"><input type="text" name="inf_field_FirstName" id="cf-first" placeholder=" " required><label for="cf-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="cf-last" placeholder=" " required><label for="cf-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="cf-email" placeholder=" " required><label for="cf-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="cf-phone" placeholder=" " required><label for="cf-phone">Phone</label></div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Try A Free Class <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">We will contact you via phone, email, or text. There is no charge, no obligation and no risk.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Stronger. Fitter. More <span class="serif">confident</span>.',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/GHF_CrossFit_Fitness_Exercise_Outdoors_Group_Fitness_Crossfit_Gainesville_2024-01_1.jpg",
)

# ============================================================ X-FORCE
# Keap endpoint for X-Force leads, from the hosted form behind ghfc.com/xforce-workout.
# Note that page posts to a DIFFERENT form than it declares: its customFormAction points at
# 2beb523a… ("Try Us For Free") while its inf_form_xid is cc18df1f… ("x-force web form").
# We post to the x-force form's own endpoint, which is what inf_form_xid names and what the
# other integrations here do. Its embedded version string (1.70.0.561498) is also stale; the
# live hosted form serves 1.70.0.1010026, used below.
#
# Keap marks none of the four fields required — we require all four client-side anyway, as
# on CrossFit. Unlike Pilates/TRIBE/HYROX, reCAPTCHA is NOT enabled on this form.
KEAP_XF_ACTION = "https://pv228.infusionsoft.com/app/form/process/cc18df1fd187e78148222ce4891a4e53"
KEAP_XF_XID = "cc18df1fd187e78148222ce4891a4e53"
KEAP_XF_VERSION = "1.70.0.1010026"
KEAP_XF_TRAPS = ('<input type="text" name="inf_3Ht2uaf45U0YMzrh" value="" tabindex="-1" autocomplete="off" style="display:none !important">'
                 '<input type="text" name="inf-sbt" value="" tabindex="-1" autocomplete="off" style="display:none !important">')

xforce_body_page = hero(
    "X-Force Body",
    ["Twenty minutes.", 'Twice a <span class="serif">week</span>.'],
    "X-Force's negative-training machines plus a carb-smart eating plan strip fat and build muscle faster than hours of cardio ever did. Designed by exercise scientist Dr. Ellington Darden — built for people with real schedules.",
    img=f"{IMG}/XForce_Body_by_GHF_Build_Strength_Lean_Muscle_Chest_Workouts_2023.jpg",
    crumb='Training &nbsp;/&nbsp; X-Force Fat Loss Program',
    actions=[("Schedule A Discovery Session", "#discovery", True), ("The Science", "#science", False)],
    meta=["2 × 25-minute workouts weekly", "6-week program", "Clinically validated"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Lose fat for good</p>
        <h2 class="h-display reveal">Losing fat is the first step. Keeping it off is <span class="serif">next.</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">X-Force Body by GHF is a one-of-a-kind program that builds muscle to lose fat and keep it off — with less time and effort than anywhere else in the world.</p>
        <p class="body-copy reveal">Developed by renowned strength and fitness expert Ellington Darden, PhD, X-Force Body is the most efficient fat-loss program in the country! This program's proven results and unprecedented speed toward fat loss and muscle gain have generated longstanding support by both Men's Health and Women's Health magazines.</p>
        <p class="body-copy reveal">Our secret weapon? The patented X-Force tilting-weight-stack machines that use the most advanced, innovative technology specifically designed to reshape your body in record-breaking time. X-Force Body has been validated through years of clinical trials. It works. But don't just take our word for it — examine the evidence, and see for yourself.</p>
      </div>
    </div>
  </div>
</section>
""" + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Here's your fat loss plan</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Four levers, six <span class="serif">weeks</span></h2>
      </div>
    </div>
    <div class="steps reveal">
      <div class="step"><span class="step__num">01</span><h3>Carbohydrate-Rich Meals</h3><p>You will consume small meals that are composed of approximately 50 percent of the calories from carbohydrates, 25 percent from fats, and 25 percent from proteins.</p></div>
      <div class="step"><span class="step__num">02</span><h3>Descending Calories</h3><p>You will embark on a six-week eating plan that descends the calories by 100 with each two-week period. Men drop from 1,600 to 1,500 to 1,400 calories and women move from 1,400 to 1,300 to 1,200 calories.</p></div>
      <div class="step"><span class="step__num">03</span><h3>Super-Hydration &amp; Cold Water Therapy</h3><p>You will stifle hunger and burn more calories by drinking a gallon of ice water every day and keeping your body cool to activate the fat-burning power of your body's brown fat stores.</p></div>
      <div class="step"><span class="step__num">04</span><h3>More Sleep = More Muscle</h3><p>Muscle repair is made when you sleep — and it burns a lot of calories. You burn most of your daily calories while your eyes are shut, so don't shortchange your calorie burn. You will learn how best to tap into the rejuvenating, calorie-burning power of rest and sleep.</p></div>
    </div>
  </div>
</section>
""" + split(
    "The exercise science", "03",
    'The patented tilting weight <span class="serif">stack</span>',
    ["Each X-Force Body exercise machine houses a patented \"tilting\" weight stack which allows for a 40% heavier resistance on the \"negative\" or lowering part of the exercise. This heavier negative resistance greatly increases the intensity of muscle exertion during each repetition, which translates into significant strength gains and fat loss in less time.",
     "Results that previously required three, four or five hour-long workouts a week can now be stimulated with only two, 25-minute X-Force Body sessions weekly. When we lower a weight, we are approximately 40% stronger than when we raise it — by tilting the weight stack 45 degrees on the positive motion, we supply a 40% heavier load to the negative phase."],
    f"{IMG}/xforce_machines.JPG",
    "X-Force Body machines",
    tag="The Science",
) + f"""
<section class="section" id="science">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Benefits of negative-accentuated training</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">More than fat <span class="serif">loss</span></h2>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>Elevate your fat-burning metabolism during and after hours after your workout</li>
          <li>Stimulate the production of interleukin 6 and other chemical messengers that help to break down fat storage in fat cells</li>
          <li>Boost bone density and even grow new bone cells to protect against osteoporosis</li>
          <li>Reverse age-related muscle loss and build strength for life</li>
          <li>Lower levels of the stress hormone cortisol, reduce symptoms of anxiety and depression and improve sleep</li>
          <li>Improve blood sugar levels, reducing risk of metabolic syndrome and type 2 diabetes</li>
        </ul>
      </div>
    </div>
  </div>
</section>
""" + f"""
<section class="section section--light" id="discovery">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Schedule a free discovery session</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Your first step to weight <span class="serif">loss</span></h2>
        <p class="lede reveal" style="margin-top:28px">Find out how you can build the most muscle and burn the most fat in 25 minutes twice per week. Complete the form and we will contact you to set up your session.</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_XF_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-xforce.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_XF_XID}">
          <input type="hidden" name="inf_form_name" value="x-force web form">
          <input type="hidden" name="infusionsoft_version" value="{KEAP_XF_VERSION}">
          {KEAP_XF_TRAPS}
          <div class="field"><input type="text" name="inf_field_FirstName" id="xf-first" placeholder=" " required><label for="xf-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="xf-last" placeholder=" " required><label for="xf-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="xf-email" placeholder=" " required><label for="xf-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="xf-phone" placeholder=" " required><label for="xf-phone">Phone</label></div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Book My Discovery Session <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">We will contact you via phone, email, or text. There is no charge, no obligation and no risk.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Is X-Force Body right for <span class="serif">you?</span>',
    "Try a free X-Force Body session and see if it's right for you.",
    f"{IMG}/XForce_XForce_Body_GHF_Gain_Muscle_Leg_Exercises_2023.jpg",
)

# ============================================================ HYROX
hyrox_faq = [
    ("What is HYROX?",
     "A fitness race that alternates a 1&nbsp;km run with a functional strength station, eight times over. Stations include sled pushes, rowing, farmer's carries and wall balls. The format is identical at every event worldwide, so you can benchmark your progress and compare your result against anyone, anywhere."),
    ("Is HYROX good for beginners?",
     "Yes. The movements in HYROX are deliberately basic &mdash; there are no barbell lifts, no gymnastics, and nothing that requires months of technique work. If you can walk, lunge, carry and push, you already have the foundation. What separates a beginner from an elite athlete is pacing, consistency and reps, not skill."),
    ("What are the eight HYROX stations?",
     "In race order: 1,000m SkiErg, 50m sled push, 50m sled pull, 80m burpee broad jumps, 1,000m row, 200m farmer's carry, 100m sandbag lunges, and 100 wall balls &mdash; with a 1&nbsp;km run before each one."),
    ("How is HYROX different from CrossFit?",
     "CrossFit varies every day and includes technical Olympic lifts. HYROX is the same every single time, with simple movements &mdash; and roughly half of a HYROX race is running. That repeatability is exactly what makes it useful as a training method: you always know what is coming, so you can measure whether you are getting faster."),
    ("Do I need to be a runner?",
     "You need basic running ability. If you can currently jog a mile without stopping, you have enough of a base to start."),
    ("Do I have to sign up for a race to train HYROX?",
     "No. Many GHF members train in HYROX-style classes purely as their workout of choice, with no race registration at all. If you decide later that you want to compete, you will already have the foundation to walk into your first race confident instead of overwhelmed."),
    ("How long does it take to train for a race?",
     "Most athletes need eight to twelve weeks of structured training for their first race."),
    ("How long does a HYROX race take?",
     "The average finisher completes the race in about 90 minutes, and there is no time limit."),
    ("What race divisions are there?",
     "Doubles, Relay and Singles, each with Open and Pro categories and five-year age brackets."),
    ("Where is the closest race to Gainesville?",
     "HYROX Tampa, 22&ndash;25 October 2026, at the Tampa Convention Center."),
    ("What should I wear, and what shoes are best?",
     "A hybrid training shoe &mdash; running cushioning with enough grip for the stations. Breathable, moisture-wicking clothing. Bring water and a towel; we provide all the equipment."),
    ("Does GHF host race simulations?",
     "Yes. We periodically run the GHF HYROX Simulation, an in-house event where you complete the full race format start to finish."),
    ("How do I sign up for a class?",
     "HYROX classes run at GHF Main, 4820 Newberry Road. Drop in for $20, or buy an eight-session pack for $119. Request a spot using the form on this page, or email the program director at <a href=\"mailto:AJ.Smith@ghfc.com\" style=\"color:var(--accent)\">AJ.Smith@ghfc.com</a>."),
]

# Keap endpoint for HYROX leads, from the hosted form behind the embed script. As with
# Pilates the version string is the newer 1.70.0.1010026, and the honeypot carries Keap's
# current rotated name — the two traps below are what the live form actually ships. The
# forms deployed before Pilates still send the older inf_eGYY1p7FcL3TD8b6 in KEAP_TRAPS;
# leave them as they are.
#
# NOTE: reCAPTCHA (invisible, Enterprise) is enabled on this form in Keap, as it is on the
# Pilates, TRIBE and personal-training forms. Keap's own JS mints a token on submit; a
# hand-built POST sends none, so Keap may reject these submissions. It is OFF on the
# CrossFit form, so it is a per-form setting — turn it off for the others, or prove with a
# real submission that tokenless posts are accepted.
KEAP_HYROX_ACTION = "https://pv228.infusionsoft.com/app/form/process/3fe1e83b57fa1518bb2eaabbb34fdb38"
KEAP_HYROX_XID = "3fe1e83b57fa1518bb2eaabbb34fdb38"
KEAP_HYROX_VERSION = "1.70.0.1010026"
KEAP_HYROX_TRAPS = ('<input type="text" name="inf_3Ht2uaf45U0YMzrh" value="" tabindex="-1" autocomplete="off" style="display:none !important">'
                    '<input type="text" name="inf-sbt" value="" tabindex="-1" autocomplete="off" style="display:none !important">')

hyrox_body = hero(
    "Official HYROX Training Club",
    ["Eight runs.", 'Eight <span class="serif">stations</span>.'],
    "Gainesville Health &amp; Fitness is North Central Florida's home for official HYROX training &mdash; the world's fastest-growing fitness format. Whether you are training to compete or just want the most effective functional workout you have ever done, this is your base.",
    img=f"{IMG}/hyrox-sled.jpg",
    crumb='Training &nbsp;/&nbsp; HYROX',
    actions=[("Try a Class", "#pass", True), ("See The Eight Stations", "#stations", False)],
    meta=["Official HYROX affiliate", "Race-day equipment", "Coached for all levels"],
    page=True,
) + f"""
<section class="section" id="stations">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">What is HYROX?</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">The workout you can actually <span class="serif">measure</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Run one kilometre, then complete a functional station. Repeat that eight times. No complex skills to learn, no intimidating movements &mdash; just work, in the same order, every time.</p>
    </div>
    <div class="steps reveal">
      <div class="step"><span class="step__num">01</span><h3>1,000m SkiErg</h3><p>Full-body pulling under fatigue, straight off your first run.</p></div>
      <div class="step"><span class="step__num">02</span><h3>50m Sled Push</h3><p>Loaded, low and relentless &mdash; the station most first-timers remember.</p></div>
      <div class="step"><span class="step__num">03</span><h3>50m Sled Pull</h3><p>Hand over hand, dragging the sled back to you from the floor.</p></div>
      <div class="step"><span class="step__num">04</span><h3>80m Burpee Broad Jumps</h3><p>Down, up, jump forward. Simple to learn, hard to pace.</p></div>
      <div class="step"><span class="step__num">05</span><h3>1,000m Row</h3><p>The halfway point, and the best chance to steady your breathing.</p></div>
      <div class="step"><span class="step__num">06</span><h3>200m Farmer's Carry</h3><p>Two heavy kettlebells, grip and posture under pressure.</p></div>
      <div class="step"><span class="step__num">07</span><h3>100m Sandbag Lunges</h3><p>A loaded sandbag across your shoulders, one step at a time.</p></div>
      <div class="step"><span class="step__num">08</span><h3>100 Wall Balls</h3><p>The finish. Legs and lungs, with the line in sight.</p></div>
    </div>
  </div>
</section>
""" + split(
    "New to HYROX", "02",
    'Start as a total <span class="serif">beginner</span>',
    ["At GHF, helping beginners feel confident isn't an afterthought &mdash; it's what we do best. Whether this is your first time in a gym, your first group class, or your first time hearing the word HYROX, our coaches meet you exactly where you are.",
     "HYROX is built to be accessible. If you can walk, lunge, carry and push, you already have the foundation. The difference between a beginner and an elite athlete isn't the movements &mdash; it's pacing, consistency and reps.",
     "Beginners typically start by learning the eight stations one at a time in a coached setting, building a base of strength and running endurance before adding intensity, practising form first and speed second, and training two to three times a week to build consistency without burnout."],
    f"{IMG}/hyrox-wall-ball.jpg",
    "Athlete completing wall balls in a HYROX competition",
    cta=("Try a Class", "#pass"), tag="Beginners",
) + split(
    "Race-day equipment", "03",
    'Train on the <span class="serif">real</span> thing',
    ["No guessing. No improvising. Our facility is equipped with the exact stations used at every official HYROX event &mdash; ski ergs, sleds, rowing machines, sandbags, wall balls and more.",
     "When you train at GHF, you train like it's race day, every day. That means no surprises when you actually reach the start line, and no wasted weeks learning equipment you have never touched."],
    f"{IMG}/hyrox-ski-erg.jpg",
    "Athlete training on the ski erg at a HYROX event",
    rev=True, tag="Equipment",
) + split(
    "For racers and everyone else", "04",
    'HYROX for racers. HYROX for <span class="serif">life</span>.',
    ["Chasing a podium finish? We'll get you there, with structured race preparation built around the format you'll actually face.",
     "Prefer to skip the bib and just get an incredible workout? You belong here too. HYROX at GHF is built for both &mdash; competitive athletes who want race prep, and members who simply want a goal-driven workout that never gets old."],
    f"{IMG}/hyrox-sandbags.jpg",
    "Sandbags lined up for the HYROX sandbag lunge station",
    tag="Everyone",
) + split(
    "Meet your coach", "05",
    'Coached by a HYROX <span class="serif">pro</span>',
    ["<strong>AJ Smith, Program Director.</strong> For more than 25 years AJ has dedicated his career to understanding the human body and unlocking its potential through science-based training, nutrition and performance coaching.",
     "A current HYROX Pro Athlete and former elite cyclist with Team AEG Toshiba, AJ founded a Human Performance Studio in 2010 specialising in VO2 analysis, metabolic testing and body composition. He has coached with Gainesville Health &amp; Fitness, Life Time Fitness, Go Primal, Primal Health and Performance, and OneLife Fitness.",
     "His mission is simple: help people understand their bodies, train with purpose, and reach a level of performance they never thought possible &mdash; from first-timers to professionals."],
    f"{IMG}/hyrox-aj-smith.jpg",
    "AJ Smith, HYROX Program Director at GHF",
    rev=True, cta=("Email AJ", "mailto:AJ.Smith@ghfc.com"), tag="AJ Smith",
) + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Pricing</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">No contract. No <span class="serif">intimidation</span>.</h2>
        <p class="body-copy reveal" style="margin-top:26px">Drop into a HYROX session whenever it suits you, or commit to an eight-session pack and bring the cost per session down. Either way there is no long-term commitment &mdash; just show up and get your best results.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li><strong>$20</strong> &mdash; single drop-in session</li>
          <li><strong>$119</strong> &mdash; eight-session pack ($14.86 per session)</li>
          <li>No long-term contract</li>
          <li>All equipment provided &mdash; bring water and a towel</li>
          <li>HYROX sessions are for GHF members</li>
          <li>Held at GHF Main, 4820 Newberry Road</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Why athletes choose GHF</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">A community that pushes you without leaving you <span class="serif">behind</span></h2>
      </div>
    </div>
    <div class="pillars reveal">
      <div class="pillar"><h3>Official affiliate</h3><p>A verified, recognised HYROX Training Club &mdash; with official programming, coach education and race preparation resources.</p></div>
      <div class="pillar"><h3>Every station</h3><p>Race-specific equipment for all eight stations, so nothing on race day is unfamiliar.</p></div>
      <div class="pillar"><h3>All levels coached</h3><p>Sessions designed to scale, whether it is your first class or your fifth race.</p></div>
      <div class="pillar"><h3>Right here</h3><p>In Gainesville, serving North Central Florida &mdash; no three-hour drive to train properly.</p></div>
    </div>
  </div>
</section>

<section class="section section--light" id="first-class">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Your first class</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Try all eight stations, <span class="serif">properly</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">An interactive, hands-on session where a coach walks you through the form and technique at each of the eight HYROX stations. You get to pull the sled, throw the wall ball and get on the ski erg for the first time &mdash; safely, and with someone showing you how.</p>
        <p class="body-copy reveal" style="margin-top:18px">Classes run all week at GHF Main. Request a spot below, or email the program director at <a href="mailto:AJ.Smith@ghfc.com" style="color:var(--accent)">AJ.Smith@ghfc.com</a> to ask about times.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>Coached through all eight stations</li>
          <li>No experience needed</li>
          <li>Equipment provided</li>
          <li>Held at GHF Main</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Questions</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">HYROX, <span class="serif">answered</span></h2>
      </div>
    </div>
    {accordion(hyrox_faq)}
  </div>
</section>
""" + f"""
<section class="section section--light" id="pass">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Request your spot</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Get into your first <span class="serif">class</span></h2>
        <p class="lede reveal" style="margin-top:28px">Tell us how to reach you and we will get back to you with class times at GHF Main, and answer anything you want to know about training HYROX before you commit.</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_HYROX_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-hyrox.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_HYROX_XID}">
          <input type="hidden" name="inf_form_name" value="Web Form submitted">
          <input type="hidden" name="infusionsoft_version" value="{KEAP_HYROX_VERSION}">
          {KEAP_HYROX_TRAPS}
          <div class="field"><input type="text" name="inf_field_FirstName" id="hx-first" placeholder=" " required><label for="hx-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="hx-last" placeholder=" " required><label for="hx-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="hx-email" placeholder=" " required><label for="hx-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="hx-phone" placeholder=" " required><label for="hx-phone">Phone</label></div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Try a Class <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">We will contact you via phone, email, or text. There is no charge, no obligation and no risk.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Run, lift, <span class="serif">repeat</span>.',
    "Ready to start a more fit life? Become a GHF member today for as little as $16 per week.",
    f"{IMG}/hyrox-wall-ball.jpg",
)

# ============================================================ TEAM STRONG TRAINING
teamstrong_body = hero(
    "Team Strong Training",
    ["Stronger with a", 'team behind <span class="serif">you</span>'],
    "PLACEHOLDER COPY \u2014 replace with the real program description. Team-based strength training with coaching, structure and a group that expects you to show up.",
    img=f"{IMG}/GHF_Tribe_Tribe_Team_Training_Tribe_Fit_Strong_Tribe_Punch_2025.jpg",
    crumb='Training &nbsp;/&nbsp; Team Strong Training',
    actions=[("Get Pricing", "contact.html#pricing", True), ("Join GHF Online", "join.html#start", False)],
    meta=["PLACEHOLDER", "PLACEHOLDER", "PLACEHOLDER"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">About the program</p>
        <h2 class="h-display reveal">How Team Strong Training <span class="serif">works</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">PLACEHOLDER COPY \u2014 to be written. Describe the format, team size, season length, coaching, and how this differs from TRIBE Team Training so the two programs read distinctly.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>PLACEHOLDER \u2014 format and team size</li>
          <li>PLACEHOLDER \u2014 schedule and locations</li>
          <li>PLACEHOLDER \u2014 who it's for / fitness level</li>
          <li>PLACEHOLDER \u2014 coaching approach</li>
          <li>PLACEHOLDER \u2014 cost or membership requirement</li>
        </ul>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Find your <span class="serif">team</span>',
    "PLACEHOLDER COPY \u2014 replace with the real call to action for this program.",
    f"{IMG}/GHF_Tribe_Tribe_Team_Training_Tribe_Fit_Strong_Tribe_Punch_2025.jpg",
)

# ============================================================ SENIORS
seniors_body = hero(
    "Club Seniors at GHF",
    ["Fitness.", 'For <span class="serif">life</span>.'],
    "Resort-style amenities, classes built for your joints (not against them), and a roomful of friends who'll notice if you miss a Tuesday. Stay strong, stay sharp, stay you.",
    img=f"{IMG}/GHF_Seniors_Senior_Fitness_GroupFit_Gainesville_2023.jpg",
    crumb='Fitness &nbsp;/&nbsp; Seniors',
    actions=[("Get Your Free All-Access Pass", "#pass", True)],
    meta=["Senior-friendly classes", "Included in membership"],
    page=True,
) + split(
    "Senior fitness classes", "01",
    'Strength, flexibility, mobility — and <span class="serif">friends</span>',
    ["Our fitness classes for seniors are taught by a team of experienced instructors. Class formats have lots of repetition, fewer directional changes, simple movements, lower intensities with fun music you are sure to enjoy. Classes are perfect for those with limited mobility.",
     "On land, you may choose from balance foundations, functional fitness, simply stretch, postural health, balance for beginners, tai chi, and more."],
    f"{IMG}/Strength_GroupFit_Seniors_GHF_Tioga_2023_1.jpg",
    "Senior GHF members in a strength group fitness class",
    cta=("View Full Class Schedule", "group-fitness.html#schedule"), tag="GroupFit",
) + split(
    "Aqua classes", "02",
    'Pain-free range of <span class="serif">motion</span>',
    ["Aqua classes give you an ideal environment for relieving arthritis pain and stiffness, increasing range of motion, strength, and overall confidence — through pain free range of motion.",
     "Choose from aqua yoga, gentle joints, balance foundations, pilates flow H2O, and stretch and tone fitness classes."],
    f"{IMG}/GHF_Aquix_Pool_2018.jpg",
    "Aqua group fitness class in the pool",
    rev=True, cta=("Explore the Pool", "pool.html"), tag="Aqua",
) + split(
    "Sit To Be Fit", "03",
    'Our signature seated <span class="serif">series</span>',
    ["Our signature program is the Sit To Be Fit series that focuses on seated exercises for strength, cardio, core, yoga, and flexibility and is ideal for those with limited mobility.",
     "All classes on the group fitness schedule are included in membership, there is no additional charge."],
    f"{IMG}/GHF_GHF_Seniors_Sit_to_be_Fit_Senior_Fitness_Group_Fitness_2023.jpg",
    "Sit To Be Fit senior fitness class",
    tag="Signature",
) + split(
    "Supervised strength training", "04",
    'If you\'re not sure how to lift weights, we\'ll <span class="serif">show you</span>',
    ["We have a strength training circuit for beginners that is fully staffed — they will teach you how to safely lift weights and will assist and motivate you EVERY time you come to the gym.",
     "\"The Line\" is a series of 7-9 machines that work large to small muscle groups so you don't have to guess what order to do the machines — it's all done for you!"],
    f"{IMG}/Tioga_Carrie_Grotto_2_Facility_2022_copy.jpg",
    "Assisted strength training on The Line at GHF",
    rev=True, tag="The Line",
) + form_section(
    "pass", "05", "Request your free gym pass",
    'Your free gym pass is <span class="serif">waiting</span>',
    "With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health &amp; Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired.",
    "Claim My Free Pass",
) + cta_band(
    'Live better. Live <span class="serif">longer</span>.',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/Simply_Stretch_GHF_Tioga_GroupFit_Flexibility_2023_1_1.jpg",
)

# ============================================================ SPORTS ACTIVITIES
sports_body = hero(
    "Sports Activities at GHF",
    ["The workouts that don't feel", 'like <span class="serif">workouts</span>'],
    "Pick-up basketball, volleyball nights, lap swimming, cycling crews. Chase a ball for an hour and somehow get fitter than you would on a treadmill. Bring your competitive streak.",
    img=f"{IMG}/GHF_Basketball_5.jpg",
    crumb='Fitness &nbsp;/&nbsp; Sports Activities',
    actions=[("Get Your Free Pass", "#pass", True)],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="rows reveal">
      <a class="row-item" href="pool.html">
        <span class="row-item__idx">01</span>
        <span class="row-item__title">Indoor Lap Pool</span>
        <span class="row-item__desc">Improve your conditioning by swimming laps in our 75-foot lap pool, and recover in our cold pool or sauna — a holistic, healing environment designed to recover and reduce stress.</span>
        <span class="row-item__arrow">→</span>
      </a>
      <a class="row-item" href="group-fitness.html">
        <span class="row-item__idx">02</span>
        <span class="row-item__title">High-Intensity Interval Training</span>
        <span class="row-item__desc">Push your limits with HIIT classes on the GHF fitness class schedule — indoors and out.</span>
        <span class="row-item__arrow">→</span>
      </a>
      <a class="row-item" href="court-sports.html">
        <span class="row-item__idx">03</span>
        <span class="row-item__title">Basketball &amp; Volleyball</span>
        <span class="row-item__desc">Experience the thrill of our full-court basketball court — novice or seasoned, our courts cater to all levels. Volleyball is open for games every Wednesday (6-11p) and Sunday (5-10p).</span>
        <span class="row-item__arrow">→</span>
      </a>
      <a class="row-item" href="cardio.html">
        <span class="row-item__idx">04</span>
        <span class="row-item__title">Indoor Cycling</span>
        <span class="row-item__desc">Sky Cycle at GHF Main: stadium seating, 40 bikes, My Ride technology — a state-of-the-art video projection and sound system that takes you on rides around the world.</span>
        <span class="row-item__arrow">→</span>
      </a>
      <a class="row-item" href="personal-training.html">
        <span class="row-item__idx">05</span>
        <span class="row-item__title">Sports Performance</span>
        <span class="row-item__desc">Nationally certified trainers take young athletes through a comprehensive assessment and carefully designed sports conditioning programs to increase speed, strength, and performance.</span>
        <span class="row-item__arrow">→</span>
      </a>
    </div>
  </div>
</section>

<section class="section section--flush">
  <div class="gallery wrap">
    <div class="g-item g-item--a reveal-img"><img src="{IMG}/GHF_Basketball_5.jpg" alt="Indoor basketball and volleyball court" loading="lazy"></div>
    <div class="g-item g-item--b reveal-img"><img src="{IMG}/sports-activities-hiit-700x467.jpg" alt="Outdoor conditioning group fitness" loading="lazy"></div>
    <div class="g-item g-item--c reveal-img"><img src="{IMG}/GHF_GroupFit_SkyCycle_Classes_Cycle_Cardio_2024.jpg" alt="SkyCycle indoor cycling studio" loading="lazy"></div>
  </div>
</section>
""" + form_section(
    "pass", "06", "Request your free gym fitness pass",
    'Your free all-access pass is <span class="serif">waiting</span>',
    "With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health &amp; Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired.",
    "Claim My Free Pass",
) + cta_band(
    'Get in the <span class="serif">game</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/sports-activities-hiit-700x467.jpg",
)

# ============================================================ SPECIAL NEEDS / FIT FOR ALL
fitforall_body = hero(
    "Special Needs Fitness",
    ["FIT for ALL", 'at <span class="serif">GHF</span>'],
    "Fun Inclusive Training (FIT) for ALL is a free fitness program designed for individuals with special needs. Every aspect of the program is geared toward helping those with developmental and intellectual disabilities, such as Autism, Down's Syndrome, and Prader-Willi Syndrome.",
    img=f"{IMG}/GHF_Careers_Floor_Instructor_Fitness_Jobs_Service.jpg",
    crumb='Fitness &nbsp;/&nbsp; Special Needs Fitness',
    actions=[("Meet The Program Coordinator", "#pass", True)],
    meta=["Free program", "One-on-one instruction"],
    page=True,
) + stats_band([
    (18, "", "Classes across the six-week program"),
    (250, "+", "Volunteers have served as coaches"),
    (50, "", "Special needs athletes — and growing"),
    (0, "$", "Cost to participants"),
]) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Program description</p>
        <h2 class="h-display reveal">Fitness for those with special <span class="serif">needs</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">The six-week program provides 18 classes, each with one-on-one instruction and structure to guide participants through fitness activities including a circuit style group class and strength training machines.</p>
        <p class="body-copy reveal">Outcomes include improved endurance, reduced body fat and secondary risk factors, and improved cognition, social engagement, and self-image. Classes meet Monday–Friday at 3–4pm at our GHF Main location, 4820 Newberry Road.</p>
        <p class="body-copy reveal">Over 250 volunteers have served as coaches in the program which began with 15 participants and is now up to 50 special needs athletes. Participants do not have to be members of GHF. Volunteers welcome — contact president@fitforall.org.</p>
      </div>
    </div>
  </div>
</section>
""" + form_section(
    "pass", "02", "Request your free guest pass",
    'Take the first <span class="serif">step</span>',
    "Meet with the program coordinator as your first step in Fit For All. You will also be able to try a class to see if the program is right for you. Get ready for an experience that will help you get the most out of life and inspire you to become your best.",
    "Get Started",
) + cta_band(
    'There\'s a place for <span class="serif">everyone</span> at GHF',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/groupfit.jpg",
)

# ============================================================ BRING A GUEST
guest_body = hero(
    "Power of Friends",
    ["Your people train", '<span class="serif">free</span>'],
    "Workouts are better with your favorite humans. Every guest visiting with a member gets 6 free visits — classes, pool, sauna, all of it. Grab your friend; we'll handle the rest.",
    img=f"{IMG}/cycle_friends.jpg",
    crumb="Bring a Guest",
    actions=[("Join GHF Online", "join.html#start", True), ("Get Pricing", "contact.html#pricing", False)],
    meta=["6 free visits per guest", "Unlimited guests", "2 at a time"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Guidelines for guest visits</p>
        <h2 class="h-display reveal">Bring as many friends as you <span class="serif">like</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">You may bring as many guests as you'd like during your membership (but just 2 at one time). If you and your guest are unable to work out together, you may request a guest pass. Guests are welcome to join the gym online anytime.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>Guests must be accompanied by a current GHF member</li>
          <li>Guests may visit GHF facilities up to 6 times total</li>
          <li>Guests must check in and present photo ID</li>
          <li>Minimum age is 13 years | 13–17 must be accompanied by parent/guardian</li>
          <li>No special passes or advanced reservations required</li>
        </ul>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'The power of <span class="serif">friends</span>',
    "Guests are welcome to join the gym online anytime — or grab a free all-access pass and see what GHF is all about.",
    f"{IMG}/Echo_GroupFit_Outdoor_Classes_Fun_Classes_2021.jpg",
    primary=("Join GHF Online", "join.html"),
)

# ============================================================ MEMBER SAVINGS
savings_body = hero(
    "Member Savings Program",
    ["The membership that pays", 'for <span class="serif">itself</span>'],
    "Show your GHF card at dozens of local businesses and watch the discounts stack up — many members save more than their dues every month. Eat, shop, save, repeat.",
    img=f"{IMG}/smoothie_girls_web.png",
    crumb="Member Savings",
    actions=[("Get Pricing", "contact.html#pricing", True)],
    meta=["100+ participating businesses", "No coupons required"],
    page=True,
) + stats_band([
    (100, "+", "Participating local businesses"),
    (1, "", "Membership card is all you need"),
    (0, "", "Coupons required"),
    (365, "", "Days a year of savings"),
]) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">How it works</p>
        <h2 class="h-display reveal">Save every <span class="serif">day</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">With over 100 participating businesses, you'll save every day on a variety of services and products, no coupons required! Simply show your GHF membership card and start saving.</p>
        <p class="body-copy reveal"><strong>Would your business like to take part in the Member Savings Program?</strong> Call us at (352) 377-4955 or email us — we'd love to partner with you.</p>
        <div class="reveal"><a class="inline-link" href="contact.html">Contact Us →</a></div>
      </div>
    </div>
  </div>
</section>
""" + savings_directory(SAVINGS) + cta_band(
    'Your membership pays you <span class="serif">back</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/Family_Membership_Plans.jpg",
)

# ============================================================ LOCATION PAGES
# One builder, three data sets. Copy is ported from the live per-location pages
# (main-center.aspx / womens-center.aspx / tioga-center.aspx) with their typos
# and duplicated sentences cleaned up.

def slideshow(slides, label, ratio):
    """slides: list of (filename, alt, caption). Behaviour lives in main.js."""
    out = ""
    for n, (fn, alt, cap) in enumerate(slides):
        cap_attr = f' data-cap="{cap}"' if cap else ' data-cap=""'
        lazy = "" if n == 0 else ' loading="lazy"'
        out += (f'<div class="slideshow__slide"{cap_attr}>'
                f'<img src="{IMG}/gallery/{fn}" alt="{alt}"{lazy}></div>')
    return f"""
<div class="slideshow reveal" tabindex="0" role="group" aria-label="{label} photo gallery">
  <div class="slideshow__stage" style="aspect-ratio:{ratio}">{out}</div>
  <div class="slideshow__bar">
    <button class="slideshow__btn" type="button" data-slide="prev" aria-label="Previous photo">&larr;</button>
    <button class="slideshow__btn" type="button" data-slide="next" aria-label="Next photo">&rarr;</button>
    <span class="slideshow__count"><span class="slideshow__cur">01</span> / {len(slides):02d}</span>
    <p class="slideshow__cap"></p>
  </div>
</div>
"""


def location_page(L):
    hours_rows = "".join(f"<div><dt>{d}</dt><dd>{t}</dd></div>" for d, t in L["hours"])
    kids = ""
    if L.get("kids_hours"):
        kids_rows = "".join(f"<div><dt>{d}</dt><dd>{t}</dd></div>" for d, t in L["kids_hours"])
        kids = ('<h4 style="margin-top:34px">Kid&rsquo;s Club hours</h4>'
                f'<div class="loc-hours">{kids_rows}</div>')
    feats = "".join(f"<li>{f}</li>" for f in L["features"])
    intro = "".join(f'<p class="body-copy reveal">{p}</p>' for p in L["intro"])
    progs = ""
    if L.get("programs"):
        progs = '<div class="pillars" data-stagger>' + "".join(
            f'<div class="pillar"><span class="pillar__num">{t}</span><h3>{b}</h3></div>'
            for t, b in L["programs"]) + "</div>"
        progs = f"""
<section class="section section--tight">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">{L['prog_eyebrow']}</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">{L['prog_title']}</h2>
      </div>
    </div>
    {progs}
  </div>
</section>
"""
    return hero(
        L["kicker"], L["lines"], L["sub"],
        img=L["hero_img"],
        crumb=f'<a href="locations.html">Locations</a> &nbsp;/&nbsp; {L["name"]}',
        actions=[("Claim Your Free Fitness Pass", "ghf-pass.html#claim", True),
                 (f'Call {L["phone"]}', f'tel:{L["tel"]}', False)],
        meta=L["meta"], page=True,
    ) + stats_band(L["stats"]) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">{L['intro_eyebrow']}</p>
        <h2 class="h-display reveal">{L['intro_title']}</h2>
      </div>
      <div class="intro-grid__right">
        {intro}
        <div class="reveal" style="margin-top:8px"><a class="inline-link" href="ghf-pass.html#claim">Claim your free fitness pass &rarr;</a></div>
      </div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Virtual tour</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Look around before you <span class="serif">walk in</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:36ch">{L['tour_note']}</p>
    </div>
    <div class="reveal">{embed('https://www.youtube.com/embed/' + L['tour_id'], 'Virtual tour of ' + L['name'], allow_yt=True)}</div>
  </div>
</section>
{progs}
<section class="section section--light">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">What's here</p>
        <h2 class="h-display reveal">{L['feat_title']}</h2>
        <p class="body-copy reveal" style="margin-top:26px">{L['feat_note']}</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">{feats}</ul>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Photo gallery</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Inside <span class="serif">{L['short']}</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:34ch">Real photos of the floor, the studios and the spaces you'll actually use.</p>
    </div>
    {slideshow(L['gallery'], L['name'], L['gallery_ratio'])}
  </div>
</section>

<section class="section section--light">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Visit us</p>
        <h2 class="h-display reveal">Come see it for <span class="serif">yourself</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">Walk in anytime we're open. Tell the front desk it's your first visit and someone will show you around &mdash; no appointment, no pressure.</p>
        <div class="hero__actions reveal" style="opacity:1;transform:none;margin-top:30px">
          <a class="btn btn--dark" href="ghf-pass.html#claim">Claim Your Free Fitness Pass <span class="arr">&rarr;</span></a>
        </div>
      </div>
      <div class="intro-grid__right reveal">
        <span class="loc-badge">{L['badge']}</span>
        <h3 style="margin-top:16px">{L['name']}</h3>
        <a class="phone" href="tel:{L['tel']}">{L['phone']}</a>
        <h4 style="margin-top:30px">Hours</h4>
        <div class="loc-hours">{hours_rows}</div>
        {kids}
        <address style="margin-top:30px">{L['address']}<br>{L['manager']}</address>
        <div style="margin-top:18px"><a class="inline-link" href="{L['map']}" target="_blank" rel="noopener">Get directions &rarr;</a></div>
      </div>
    </div>
  </div>
</section>
""" + marquee(L["marquee"]) + cta_band(
        L["cta_title"], L["cta_text"], L["cta_img"],
        primary=("Claim Your Free Fitness Pass", "ghf-pass.html#claim"),
        secondary=("Join GHF Online", "join.html"),
    )


MAIN_CENTER = dict(
    name="GHF Main", short="GHF Main", slug="main-center.html",
    kicker="GHF Main &mdash; open 24/7",
    lines=["Gainesville's best gym", 'near <span class="serif">you</span>'],
    sub="130,000 square feet, open every hour of every day, with the deepest bench of equipment, classes and recovery in North Central Florida. And staff on the floor to make sure you never have to figure it out alone.",
    hero_img=f"{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg",
    phone="(352) 377-4955", tel="3523774955",
    address="4820 W Newberry Road, Gainesville, FL 32607",
    manager="General Manager &mdash; Adrian Antigua",
    map="https://maps.google.com/?q=4820+W+Newberry+Road,+Gainesville,+FL+32607",
    badge="Open 24/7",
    meta=["Open 24 hours, every day", "130,000 sq ft", "600 classes a month"],
    hours=[("Every day", "Open 24 hours")],
    stats=[(130, "K", "Square feet under one roof"), (24, "/7", "Hours, every day of the year"),
           (600, "", "Group classes each month"), (75, "ft", "Indoor heated lap pool")],
    intro_eyebrow="The flagship",
    intro_title='Everyone wants something <span class="serif">better</span>',
    intro=[
        "At Gainesville Health &amp; Fitness we believe everyone wants something better &mdash; to look better, feel better, live better &mdash; and that most people need help getting there. That's why we're here.",
        "GHF Main makes it easy to get fit, strong and lean: 24-hour access, free babysitting, expansive cardio selections, state-of-the-art strength equipment, and the most options in town for post-workout recovery &mdash; sauna, cold pool, hot tub, lap pool.",
        "We recently opened another 10,000 square feet featuring hot yoga, functional training turf and a brand new personal training studio. Add indoor basketball and volleyball, a complete aquatic center with a 75-foot pool, and boutique small-group training, and you have unparalleled variety &mdash; the kind that keeps you in the exercise habit for a lifetime.",
        "Here you'll find friendly, down-to-earth staff who make every member and guest feel welcome, with the guidance and support to help you become a better you.",
    ],
    tour_note="Take the full walkthrough of GHF Main &mdash; the weight floor, the pool, the studios and the recovery wing.",
    tour_id="iRFAaDA-NbI",
    feat_num=3, gal_num=4, visit_num=5,
    feat_title='GHF Main <span class="serif">features</span>',
    feat_note="Everything below is included in your membership, and your membership works at all three locations.",
    features=[
        "The most cardio and strength machines", "New functional training turf",
        "Newly expanded free weight areas", "The EndZone &mdash; glute-focused area",
        "Supervised strength circuit for beginners", "75-ft indoor heated pool",
        "Sauna, steam room and hot tub", "Warm and cold therapy pools",
        "Hot yoga studio", "Arthritis and Aquatic Center",
        "Indoor cycling studio", "Free babysitting",
        "600 group classes monthly", "Outdoor fitness pavilion",
        "Staff to help you every time", "X-Force negative-only training center",
        "Open air stretching area", "Indoor basketball and volleyball court",
        "Showers, vanities, hair dryers, lockers, private changing",
        "J-Bar smoothie bar", "Complimentary WiFi",
        "Access to GHF Women and GHF Tioga",
    ],
    gallery=[
        ("Main-Center-ExpansionCableStrengthGHF.jpg", "Cable and strength machines at GHF Main", "Tone up, bulk up or shape up &mdash; state-of-the-art equipment to help you reach your goals."),
        ("Main-Center-HammerStrengthTrainingGHF.jpg", "Hammer Strength equipment at GHF Main", "All the strength training equipment you need to take your body to the next level."),
        ("Main-Center-BasketballCourtGHF.jpg", "Indoor basketball court at GHF Main", "Shoot some hoops on our regulation-size indoor basketball court."),
        ("Main-Center-GroupFitnessExteriorYogaGHF.jpg", "Group fitness studio at GHF Main", "Stretch, dance or find your Zen in the group fitness studio."),
        ("Main-Center-GroupXGatorGHF.jpg", "Group fitness class at GHF Main", "You never know who you'll run into when you take a group fitness class here."),
        ("Main-Center-StretchPersonalTrainingStudioGHF.jpg", "Personal training studio at GHF Main", "Personal instruction and motivation in the Personal Training Studio."),
        ("Main-Center-XForceBodyTrainingStudioGHF.jpg", "X-Force Body training studio at GHF Main", "Lose fat and add muscle with the X-Force Body program."),
        ("Main-Center-LuxuryLoungeGHF.jpg", "Member lounge at GHF Main", "Catch your breath, or catch up with friends, in the lounge."),
        ("Main-Center-ProteinSmoothieBarGHF.jpg", "The J-Bar smoothie bar at GHF Main", "A refreshing smoothie or an energizing snack at the J-Bar."),
        ("Main-Center-SmoothieCafePatioGHF.jpg", "Outdoor patio at GHF Main", "Take a break and enjoy some sunshine on the patio outside the J-Bar."),
        ("Main-Center-RetailFitnessFashionGHF.jpg", "Retail shop at GHF Main", "The gift shop carries the latest athletic wear and GHF-themed goods."),
    ],
    gallery_ratio="1200/350",
    marquee=["24/7 Access", "75ft Lap Pool", "Hot Yoga", "The EndZone", "X-Force", "Free Weights", "J-Bar", "Basketball"],
    cta_title='Live better at <span class="serif">GHF</span>',
    cta_text="Better people. Better programs. Better facilities. Better benefits. Better community. Gainesville's best gym to help you get stronger &mdash; and stay that way.",
    cta_img=f"{IMG}/GHF_Benches_Free_Weight_Expansion_2025.jpg",
)

WOMENS_CENTER = dict(
    name="GHF Women", short="GHF Women", slug="womens-center.html",
    kicker="GHF Women &mdash; women only",
    lines=["Where every woman", 'gets <span class="serif">stronger</span>'],
    sub="Gainesville's only women-only club. Ready to glow from the inside out? Nothing matters more than feeling amazing &mdash; and having women who support and empower each other while you get there.",
    hero_img=f"{IMG}/GHF_GHF_Women_Womens_Center_SWEAT_2023_1.jpg",
    phone="(352) 374-4634", tel="3523744634",
    address="2441 NW 43rd Street, Gainesville, FL 32606",
    manager="Manager &mdash; Jordan Heitzler",
    map="https://maps.google.com/?q=2441+NW+43rd+Street,+Gainesville,+FL+32606",
    badge="Women Only",
    meta=["Women only", "All-female staff", "175 classes a month"],
    hours=[("Mon&ndash;Thurs", "5am&ndash;9pm"), ("Friday", "5am&ndash;8pm"),
           ("Saturday", "8am&ndash;6pm"), ("Sunday", "Closed")],
    kids_hours=[("Mon&ndash;Thurs", "8am&ndash;1pm, 3pm&ndash;8pm"), ("Friday", "8am&ndash;1pm, 3pm&ndash;7pm"),
                ("Saturday", "8am&ndash;1pm"), ("Sunday", "Closed")],
    stats=[(175, "", "Fitness classes each month"), (100, "%", "Female staff"),
           (1, "", "Women-only club in Gainesville"), (0, "", "Extra cost for babysitting")],
    intro_eyebrow="A gym designed by women, for women",
    intro_title='Grab your girl <span class="serif">squad</span>',
    intro=[
        "Experience the place where every woman gets stronger &mdash; in every area of wellness. Feel the support and motivation to lead your healthiest life and make your fitness goals come true.",
        "Come to the hottest group classes in Gainesville, lift in a private space, and see why we're known for our variety of ways to sweat, dance, stretch and challenge yourself.",
        "Every membership includes free babysitting at Kid's Club, and your card works at GHF Main and GHF Tioga too &mdash; so the women-only floor is your home base, not your limit.",
    ],
    tour_note="Step inside the women-only floor, Studio Q and the group fitness studio before your first visit.",
    tour_id="eqRGwNykS_4",
    prog_num=3, feat_num=4, gal_num=5, visit_num=6,
    prog_eyebrow="Programs built for you",
    prog_title='Four ways to get <span class="serif">strong</span>',
    programs=[
        ("Group Fitness", "Build total-body strength with Body Pump, sweat it out with HIIT or Zumba, or lengthen and tone with Pilates Mat and Yoga"),
        ("Personal Training", "Work with nationally certified, expert female trainers &mdash; guidance, motivation and accountability, one-on-one in an enclosed space"),
        ("Functional Training", "Studio Q is built for your favorite functional work: TRX straps, free weights, the hip thrust machine and more"),
        ("Specialty Programs", "Including Yoga For Pregnancy &mdash; improving flexibility and strength while teaching you to use yoga through labor and delivery"),
    ],
    feat_title='Build your strongest <span class="serif">you</span>',
    feat_note="The most classes, the best programs, expansive amenities, and a strong community of women.",
    features=[
        "All-female staff", "Functional training studio &mdash; Studio Q",
        "Free babysitting", "175 fitness classes monthly",
        "Supervised strength circuit for beginners", "Sauna, steam room and hot tub",
        "The most cardio and strength machines", "Stretching and ab workout area",
        "Showers, vanities, hair dryers, lockers, private changing",
        "Convenient parking in Thornebrook Village", "Complimentary WiFi",
        "Access to GHF Main and GHF Tioga",
    ],
    gallery=[
        ("Womens-Center-CardioTrainingMachines.jpg", "Cardio floor at GHF Women", "Boost your cardio in a supportive environment, designed exclusively for women."),
        ("Womens-Center-CircuitGroupFitnessTrainingQueenax.jpg", "Queenax functional training rig at GHF Women", "Build functional fitness with Queenax, a suspended body-weight system in Studio Q."),
        ("Womens-Center-GroupFitnessTrainingHeartRate.jpg", "Group fitness class at GHF Women", "Work up a sweat in the variety of fun, energizing group classes."),
        ("Womens-Center-MatrixStrengthTrainingMachines.jpg", "Matrix strength machines at GHF Women", "Staff are always happy to answer questions or demonstrate the equipment."),
    ],
    gallery_ratio="1200/350",
    marquee=["Women Only", "Studio Q", "Body Pump", "Free Babysitting", "Sauna &amp; Steam", "Yoga", "HIIT", "Zumba"],
    cta_title='Get strong with us. Be strong for <span class="serif">them.</span>',
    cta_text="We understand you &mdash; your needs, your challenges, your life responsibilities. Come see what a room full of women pulling for each other feels like.",
    cta_img=f"{IMG}/GHF_Women_Strength_Moms_Fitness_Medicine_balls_2025.jpg",
)

TIOGA_CENTER = dict(
    name="GHF Tioga", short="GHF Tioga", slug="tioga-center.html",
    kicker="GHF Tioga &mdash; Tioga Town Center",
    lines=["Gainesville's best gym", 'just minutes from your <span class="serif">door</span>'],
    sub="An elegant fitness facility west of I-75, with top-of-the-line equipment, luxurious spaces and deluxe amenities &mdash; steps from the dining and shopping of Tioga Town Center.",
    hero_img=f"{IMG}/Tioga_Carrie_Grotto_Arm_Cross_Facility_2022.jpg",
    phone="(352) 692-2180", tel="3526922180",
    address="12830 SW 1st Lane, Suite 100, Newberry, FL 32669",
    manager="Manager &mdash; Darrius Powell",
    map="https://maps.google.com/?q=12830+SW+1st+Lane,+Suite+100,+Newberry,+FL+32669",
    badge="West of I-75",
    meta=["Minutes from home", "200 classes a month", "Pilates &amp; CrossFit studios"],
    hours=[("Mon&ndash;Thurs", "5am&ndash;10pm"), ("Friday", "5am&ndash;9pm"),
           ("Saturday", "8am&ndash;8pm"), ("Sunday", "10am&ndash;5pm")],
    stats=[(200, "", "Fitness classes each month"), (1, "", "Membership, three locations"),
           (0, "", "Extra cost for babysitting"), (5, "min", "From most of west Gainesville")],
    intro_eyebrow="Your neighborhood club",
    intro_title="You're going to feel good <span class=\"serif\">here</span>",
    intro=[
        "We believe people achieve more when they're energized, inspired and supported. GHF at Tioga Town Center provides that environment for members, their families and guests alike.",
        "Most people choose a gym close to home, and Tioga is the most convenient fitness choice west of I-75. That proximity is the whole point &mdash; it makes the difference in how often you actually go, and that's how you get results.",
        "It's an elegant facility: top-of-the-line equipment, luxurious spaces, and innovative training options including a dedicated Pilates studio and outdoor CrossFit turf. From the state-of-the-art cardio and strength areas to the upscale locker rooms with private changing, every detail was designed with your fitness in mind.",
        "From the moment you walk through the door you'll meet friendly Tioga staff dedicated to making your experience remarkable. It's a place where you will belong.",
    ],
    tour_note="See the Pilates studio, the CrossFit turf and the locker rooms before you make the drive.",
    tour_id="6Qiv714c9Bk",
    feat_num=3, gal_num=4, visit_num=5,
    feat_title='GHF Tioga luxury <span class="serif">amenities</span>',
    feat_note="Boutique touches you won't find at a neighborhood gym &mdash; included in the same one membership.",
    features=[
        "Free babysitting while you work out", "Hydro Massage in our Chill Studio",
        "Staff to help you every time", "Supervised strength circuit for beginners",
        "200 fitness classes monthly", "Private Pilates studio",
        "Outdoor CrossFit turf", "Endless cardio and strength machines",
        "Stretching and ab workout spaces", "Private personal training",
        "Showers, multiple vanities, hair dryers, lockers, private changing",
        "Complimentary WiFi", "Access to GHF Main and GHF Women",
    ],
    gallery=[
        ("Tioga-Center-01.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-02.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-03.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-04.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-05.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-06.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-07.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-08.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-09.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-10.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-11.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-12.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-13.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-14.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-15.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-16.jpg", "Inside GHF Tioga", ""),
        ("Tioga-Center-17.jpg", "Inside GHF Tioga", ""),
    ],
    gallery_ratio="3/2",
    marquee=["Pilates Studio", "CrossFit Turf", "Chill Studio", "Hydro Massage", "Free Babysitting", "West of I-75", "Tioga Town Center"],
    cta_title='Welcome to your neighborhood <span class="serif">gym</span>',
    cta_text="A clean, comfortable environment in a world-class fitness center with hometown values. Come see why members say it's a place where you belong.",
    cta_img=f"{IMG}/Tioga_Carrie_Grotto_2_Facility_2022_copy.jpg",
)

main_center_body = location_page(MAIN_CENTER)
womens_center_body = location_page(WOMENS_CENTER)
tioga_center_body = location_page(TIOGA_CENTER)


# ============================================================ GHF PASS (FREE ALL-ACCESS)
# Keap / Infusionsoft hosted-form endpoint. Field names and hidden values are copied
# verbatim from the live form at ghfc.com/ghf-pass ("All Access Pass", call name
# allaccesspass) so submissions land in the same CRM campaign.
KEAP_ACTION = "https://pv228.infusionsoft.com/app/form/process/838e496be2a9f0685d4734661fc52994"
KEAP_XID = "838e496be2a9f0685d4734661fc52994"

pass_form = f"""
<section class="section section--light" id="claim">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Request your pass</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">You're one click away from the gym that helps <span class="serif">beginners</span></h2>
        <ul class="checklist reveal" style="margin-top:34px">
          <li>Full membership privileges for one day</li>
          <li>Good at any of our three locations</li>
          <li>Please bring photo ID to check in</li>
          <li>For first-time, local guests</li>
          <li>Ages 13+ — 13 to 17 with a parent or guardian</li>
          <li>No charge, no obligation, no risk</li>
        </ul>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-pass.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_XID}">
          <input type="hidden" name="inf_form_name" value="All Access Pass">
          <input type="hidden" name="infusionsoft_version" value="1.70.0.60815">
          <input type="hidden" name="inf_IntegrationName" value="pv228">
          <input type="hidden" name="inf_CallName" value="allaccesspass">
          <input type="hidden" name="inf_api_enabled" value="true">
          <div class="field"><input type="text" name="inf_field_FirstName" id="gp-first" placeholder=" " required><label for="gp-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="gp-last" placeholder=" " required><label for="gp-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="gp-email" placeholder=" " required><label for="gp-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="gp-phone" placeholder=" " required><label for="gp-phone">Phone</label></div>
          <div class="field field--full">
            <select name="inf_custom_Facility" id="gp-loc" aria-label="Gym you would like to visit">
              <option value="">&nbsp;</option>
              <option value="Main">GHF Main — 4820 W Newberry Road</option>
              <option value="Women's Center">GHF Women — 2441 NW 43rd Street</option>
              <option value="Tioga">GHF Tioga — Tioga Town Center</option>
            </select>
            <label for="gp-loc">Gym you would like to visit</label>
          </div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Claim My Free Fitness Pass <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">Submit the form and we&rsquo;ll be in touch by phone, text or email to set up your pass. We&rsquo;ll email it to you &mdash; just activate it by visiting the location of your choice. There is no charge, no obligation and no risk.</p>
      </div>
    </div>
  </div>
</section>
"""

pass_faq = [

        ("What does the free pass actually get me?",
         "Full membership privileges for one day at the Gainesville Health &amp; Fitness location of your choice. That means every group fitness class, the pool and Aquix recovery area, the sauna and steam room, the full weight floor and cardio deck, Kid's Club babysitting, and a hydromassage session. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired."),
        ("Who is the pass for?",
         "First-time, local guests. The minimum age is 13 &mdash; guests 13 to 17 need to be accompanied by a parent or guardian. If you've used a pass with us before, or you're visiting from out of town, give us a call at (352) 377-4955 and we'll sort something out."),
        ("What should I bring?",
         "Photo ID to check in as a guest, comfortable clothes, supportive shoes, a water bottle, and a towel. If you plan to shower or use the sauna, bring toiletries and a change of clothes &mdash; lockers are free and we have full-time housekeeping."),
        ("Do I have to know what I'm doing?",
         "Not even a little. We're the gym that's best at helping beginners &mdash; that's the whole point. Tell the front desk it's your first visit and a fitness instructor will come meet you, learn your goal, and walk you through your first workout. You will not be handed a key card and left to guess."),
        ("Will someone try to sell me a membership?",
         "No pitch, no pressure. If you decide you want pricing afterward we're happy to walk you through it, and you can always <a href=\"join.html\" style=\"color:var(--accent)\">join online</a> on your own time. But the pass is genuinely free and genuinely no-obligation."),
        ("Can I bring a friend?",
         "Come in together and we'll take care of you both. Once you're a member, our Power of Friends program gives every guest you bring 6 free visits &mdash; see <a href=\"bring-a-guest.html\" style=\"color:var(--accent)\">Bring a Guest</a> for how that works."),
]

ghf_pass_body = hero(
    "The GHF Pass",
    ["Find your", 'strong <span class="serif">here</span>'],
    "Your free pass gives you a team that will help you navigate the gym — you don't have to figure it out alone. Full membership privileges for one day: every class, the pool, the sauna, the weight room, and a coach who walks it with you.",
    img=f"{IMG}/GHF_Careers_Floor_Instructor_Fitness_Jobs_Service.jpg",
    crumb="Free All-Access Pass",
    actions=[("Claim My Free Pass", "#claim", True), ("Call (352) 377-4955", "tel:3523774955", False)],
    meta=["One day, full access", "No charge, no obligation", "Any of 3 locations"],
    page=True,
) + stats_band([
    (1, "", "Day of full membership privileges"),
    (3, "", "Locations to choose from"),
    (900, "+", "Classes included each month"),
    (0, "", "Cost, obligation or risk"),
]) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">What your pass includes</p>
        <h2 class="h-display reveal">A full day, <span class="serif">all of it</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">Feeling out of shape, not sure where to start, and afraid you won't stick with it? That's exactly who we're best at helping. Your pass isn't a tour — it's the real thing, with someone beside you.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>One-day gym membership</li>
          <li>Free hydromassage session</li>
          <li>24/7 access at GHF Main</li>
          <li>All group fitness classes</li>
          <li>Indoor heated lap &amp; therapy pools</li>
          <li>Sauna, steam, hot tub, cold plunge</li>
          <li>Largest free weight area in town</li>
          <li>Most cardio &amp; weight machines</li>
          <li>Indoor basketball &amp; volleyball</li>
          <li>Free babysitting at Kid's Club</li>
          <li>Free lockers &amp; full-time housekeeping</li>
          <li>A women-only fitness center</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section section--tight">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Why choose GHF</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">More than just a <span class="serif">gym</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">First-timers and seasoned lifters train side by side here — and both walk out feeling like they belong.</p>
    </div>
    <div class="pillars" data-stagger>
      <div class="pillar"><span class="pillar__num">Convenience</span><h3>Staffed 24 hours a day, three locations on one membership, a women-only club, and free babysitting while you work out</h3></div>
      <div class="pillar"><span class="pillar__num">Programming</span><h3>Supervised strength training on The Line, 900+ group classes monthly, indoor cycle studio and hot yoga — all included</h3></div>
      <div class="pillar"><span class="pillar__num">Availability</span><h3>Thousands of strength and cardio machines, the largest free weight areas in town, indoor basketball and volleyball</h3></div>
      <div class="pillar"><span class="pillar__num">Aquix Area</span><h3>75-foot lap pool, cold pool, sauna, steam room, hot tub and warm therapy pool for the ultimate post-workout recovery</h3></div>
    </div>
  </div>
</section>

<section class="section section--light">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">How it works</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Four steps, <span class="serif">zero pressure</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:36ch">No contracts to sign, no sales pitch to survive. Just show up and see how it feels.</p>
    </div>
    <div class="steps reveal">
      <div class="step"><span class="step__num">01</span><h3>Request your pass</h3><p>Fill out the form below. It takes about twenty seconds and costs you nothing.</p></div>
      <div class="step"><span class="step__num">02</span><h3>We reach out</h3><p>We'll contact you by phone, text, or email to set it up, then send the pass to your inbox.</p></div>
      <div class="step"><span class="step__num">03</span><h3>Come in when you're ready</h3><p>Activate it anytime by walking into the location you picked. Bring photo ID to check in as a guest.</p></div>
      <div class="step"><span class="step__num">04</span><h3>A coach shows you around</h3><p>A real person learns your goal, walks you through your first workout, and makes sure you're never guessing.</p></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Where to use it</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Pick your <span class="serif">club</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Your pass is good at any one of the three. Each is a little different — choose the one that fits your day.</p>
    </div>
    <div class="loc">
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg" alt="Free weight area at GHF Main" loading="lazy"></div>
        <div>
          <span class="loc-badge">Open 24/7</span>
          <h3><a href="main-center.html">GHF Main</a></h3>
          <a class="phone" href="tel:3523774955">(352) 377-4955</a>
          <div class="loc-hours">
            <div><dt>Every day</dt><dd>Open 24 hours</dd></div>
          </div>
          <address>4820 W Newberry Road, Gainesville, FL 32607</address>
        </div>
      </div>
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/GHF_GHF_Women_Womens_Center_Body_Pump_2023_1.jpg" alt="Body Pump class at GHF Women" loading="lazy"></div>
        <div>
          <span class="loc-badge">Women Only</span>
          <h3><a href="womens-center.html">GHF Women</a></h3>
          <a class="phone" href="tel:3523744634">(352) 374-4634</a>
          <div class="loc-hours">
            <div><dt>Mon&ndash;Thurs</dt><dd>5am&ndash;9pm</dd></div>
            <div><dt>Friday</dt><dd>5am&ndash;8pm</dd></div>
            <div><dt>Saturday</dt><dd>8am&ndash;6pm</dd></div>
            <div><dt>Sunday</dt><dd>Closed</dd></div>
          </div>
          <address>2441 NW 43rd Street, Gainesville, FL 32606</address>
        </div>
      </div>
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/GHF_Tioga_Gainesville_Health_Gainesville_Gyms_TIoga_Strength_Gyms_Nearby_2026-2.jpg" alt="Strength training at GHF Tioga" loading="lazy"></div>
        <div>
          <span class="loc-badge">Family Friendly</span>
          <h3><a href="tioga-center.html">GHF Tioga</a></h3>
          <a class="phone" href="tel:3526922180">(352) 692-2180</a>
          <div class="loc-hours">
            <div><dt>Mon&ndash;Thurs</dt><dd>5am&ndash;10pm</dd></div>
            <div><dt>Friday</dt><dd>5am&ndash;9pm</dd></div>
            <div><dt>Saturday</dt><dd>8am&ndash;8pm</dd></div>
            <div><dt>Sunday</dt><dd>10am&ndash;5pm</dd></div>
          </div>
          <address>12830 SW 1st Lane, Suite 100, Newberry, FL 32669</address>
        </div>
      </div>
    </div>
  </div>
</section>
""" + pass_form + f"""
<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Pass questions</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Before you <span class="serif">come in</span></h2>
      </div>
    </div>
    {accordion(pass_faq, open_first=True)}
  </div>
</section>
""" + cta_band(
    'Ready to make it <span class="serif">yours?</span>',
    "Get ready for an experience that will help you get the most out of life and inspire you to become your best. Memberships start at as little as $15 per week.",
    f"{IMG}/Echo_GroupFit_Outdoor_Classes_Fun_Classes_2021.jpg",
    primary=("Join GHF Online", "join.html"), secondary=None,
)


# ============================================================ FAQ
faq_items = [
    ("What should I bring with me when I work out?",
     "Congratulations on taking the first step towards a healthier you! Here's what you'll need to crush your debut workout:<ul><li><strong>Comfortable Clothing:</strong> Choose breathable fabrics like cotton or moisture-wicking synthetics that move with you. Think comfy joggers, leggings, or shorts, and a breathable t-shirt or tank top. Remember socks and a workout towel!</li><li><strong>Supportive Shoes:</strong> Lace up in sneakers that provide good arch support and traction. Running shoes are a great all-around choice.</li><li><strong>Reusable Water Bottle:</strong> Staying hydrated is crucial.</li><li><strong>Shower Essentials:</strong> If you plan to shower at the gym, pack travel-sized toiletries, a towel and a change of clothes for the ride home.</li></ul>"),
    ("What is included in my membership?",
     "We offer you the best and the most of everything that makes a gym experience exceptional:<ul><li>3 locations (3 for women, 2 for men)</li><li>Blue Shirt Service (supervised exercise program on the circuit)</li><li>24/7 hours (GHF Main)</li><li>All group exercise classes</li><li>Indoor cycle classes (SkyCycle)</li><li>Aqua classes</li><li>Indoor heated lap pool, warm therapy pool, cold pool</li><li>Sauna, steam and hot tub</li><li>Club Senior programs</li><li>Kid's Club</li><li>Indoor basketball/volleyball</li><li>Boxing area (heavy bag and speed bag room)</li><li>Largest free weight area in North Central Florida</li><li>X-Force strength equipment</li><li>Largest variety of strength and cardio equipment</li></ul>"),
    ("What is not included in my membership?",
     "Everything is included in your membership except premier programs (Personal Training, CrossFit, Pilates, TRIBE, X-Force Body) and ReQuest Physical Therapy services. All of these additional programs are available for you – if interested we can set up a consultation and discuss what you are looking for and the options."),
    ("Does it cost extra to use the Kid's Club babysitting service?",
     "The Kid's Club is a privilege of membership. There is no additional fee. Enjoy 2 hours of babysitting while you workout at the gym!"),
    ("How do I get started?",
     "When you check in, let the front desk know that it's your first time here as a new member. They will call a fitness instructor to the desk to help you get started on the strength training line, cardio, or a class. We will guide you through your first gym workout!"),
    ("How often should I exercise?",
     "As a beginner, three times per week is sufficient in order to see benefits. Your strength training workouts will take about 25-30 minutes and 20 minutes of cardiovascular exercise should be adequate. Once you've been exercising at least six weeks, you can intensify your workouts. You will also want to add some flexibility exercises which you can do in our stretch classes or in any of our stretching areas."),
    ("What if I haven't been exercising lately — how do I get started again?",
     "Let the front desk know that you haven't been at the center for a while and they will call a fitness instructor to the desk to help you get started."),
    ("Will someone assist me with my workouts?",
     "The main exercise circuits are designed so that a fitness instructor will assist you and all our members with your program – they will help with your seat heights, proper form, and motivation. This is not the same as personal training — the circuits are designed to give everyone assistance at the time most needed and be available at all times to all of our members. If you feel you need more one-on-one attention, we offer Personal Training for an additional fee."),
    ("How long will it take to start to see results?",
     "The moment you start an exercise plan you are seeing some if not the full benefits of a structured fitness regimen. You will start to increase circulation and burn calories. As far as the overall results of increasing strength, reducing inches, losing fat, etc., it will take at least 4-6 weeks of regular exercise – followed by continuous improvements."),
    ("Are group exercise classes part of membership?",
     "Yes, all group exercise classes are included in membership unless they are designated a premier service such as Pilates."),
    ("How do I replace my membership card?",
     "You may order a replacement card for $10 at the front desk of any of our gyms. Or you can download the GHF app (iOS | Android) and enter your membership information to check in using your smartphone."),
    ("What is the minimum age to join Gainesville Health & Fitness?",
     "Children as young as 13 years of age can become a member with a parents' or guardians' approval and signature. Involving the whole family is a great way for everyone to get healthy."),
    ("Do you offer family memberships?",
     "Yes, we have special pricing on family memberships available for spouses and children 13-21 years of age. Getting the whole family involved in fitness is a sure way to keep everyone working out and healthy!"),
    ("If I have questions concerning my membership, who should I call?",
     "Your fitness counselor is your guide and helper and will be able to answer any questions you have about your membership, billing, visits, and account updates. Our business office is also a helpful resource at 352.375.7618."),
    ("What is the Member Savings Program?",
     "The Member Savings Program offers GHF members discounts at many local businesses — to save the cost of your dues! Simply show your GHF membership card and start saving."),
]
faq_body = hero(
    "Frequently Asked Questions",
    ["Get the most out of your", '<span class="serif">membership</span>'],
    "Everything you need to know about getting started, what's included, and making GHF yours.",
    img=f"{IMG}/groupfit.jpg",
    crumb="FAQ",
    actions=[("Still have questions? Contact us", "contact.html", True)],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    {accordion(faq_items)}
  </div>
</section>
""" + cta_band(
    'Ready when you <span class="serif">are</span>',
    "There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired.",
    f"{IMG}/Body_Balance_Les_Mills_Yoga_Group_Fitness_Tioga_2023_2.jpg",
)

# ============================================================ THANK YOU (PRICING)
# Deliberately a single screen — someone who has just submitted a form should see the
# whole message without scrolling, so everything lives in one compact hero.
thankyou_body = hero(
    "Request received",
    ["Thank you for your", 'interest in <span class="serif">GHF</span>'],
    "Congratulations on taking the first step toward a healthier, stronger you. One of our team "
    "members will follow up shortly with membership options and pricing.<br><br>"
    "In the meantime, <a href=\"locations.html\">take a tour of our locations</a>. "
    "Any other questions, email <a href=\"mailto:memberservices@ghfc.com\">memberservices@ghfc.com</a>."
    "<br><br><strong>Your GHF Team</strong> &mdash; <em>Gainesville Strong Since 1978</em>",
    img=f"{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg",
    crumb="Thank you",
    actions=[("Explore Our Locations", "locations.html", True)],
    page=True,
    hero_cls="hero--compact",
)

# ============================================================ THANK YOU (FREE PASS)
# Same one-screen treatment as the pricing thank-you. The two "what to expect" points
# are <strong> + <br> rather than a <ul>: hero() renders sub inside <p class="hero__sub">
# and a list inside a paragraph is invalid.
thankyoupass_body = hero(
    "Pass requested",
    ["Your free pass is", 'on its <span class="serif">way</span>'],
    "Congratulations on taking the first step toward a healthier, stronger you. One of our team "
    "members will follow up shortly to set up your pass and answer any questions.<br><br>"
    "<strong>Check your email</strong> &mdash; look for a confirmation email or text with everything you'll need.<br>"
    "<strong>Prepare for your visit</strong> &mdash; dress comfortably, and get ready to look around and meet the team."
    "<br><br>Questions? Call <a href=\"tel:3523774955\">(352) 377-4955</a> or email "
    "<a href=\"mailto:memberservices@ghfc.com\">memberservices@ghfc.com</a>."
    "<br><br><strong>Your GHF Team</strong> &mdash; <em>Gainesville Strong Since 1978</em>",
    img=f"{IMG}/GHF_GroupFit_SkyCycle_Classes_Cycle_Cardio_2024.jpg",
    crumb="Thank you",
    actions=[("Explore Our Locations", "locations.html", True)],
    page=True,
    hero_cls="hero--compact",
)

# ============================================================ THANK YOU (TRIBE)
thankyoutribe_body = hero(
    "Session requested",
    ["Welcome to the", '<span class="serif">TRIBE</span>'],
    "Congratulations on taking the first step toward a healthier, stronger you. One of our coaches "
    "will follow up shortly to book your free session and answer any questions.<br><br>"
    "<strong>Pick your format</strong> &mdash; LIFE, CORE, PUNCH or FitSTRONG. Your coach will help you choose.<br>"
    "<strong>Bring a friend</strong> &mdash; your free session covers both of you."
    "<br><br>Questions? Call <a href=\"tel:3523774955\">(352) 377-4955</a> or email "
    "<a href=\"mailto:memberservices@ghfc.com\">memberservices@ghfc.com</a>."
    "<br><br><strong>Your GHF Team</strong> &mdash; <em>Gainesville Strong Since 1978</em>",
    img=f"{IMG}/GHF_Tribe_Tribe_Team_Training_Tribe_Fit_Strong_Tribe_Punch_2025.jpg",
    crumb="Thank you",
    actions=[("Explore Our Locations", "locations.html", True)],
    page=True,
    hero_cls="hero--compact",
)

# ============================================================ THANK YOU (CROSSFIT)
thankyoucrossfit_body = hero(
    "Class requested",
    ["See you on", 'the <span class="serif">turf</span>'],
    "Congratulations on taking the first step toward a healthier, stronger you. One of our "
    "certified CrossFit coaches will follow up shortly to book your free class.<br><br>"
    "<strong>What to bring</strong> &mdash; a water bottle, a towel, and comfortable gym clothes and shoes.<br>"
    "<strong>Where to go</strong> &mdash; check in at the GHF Tioga lobby desk, then head out to the CrossFit turf."
    "<br><br>Questions? Call <a href=\"tel:3523774955\">(352) 377-4955</a> or email "
    "<a href=\"mailto:memberservices@ghfc.com\">memberservices@ghfc.com</a>."
    "<br><br><strong>Your GHF Team</strong> &mdash; <em>Gainesville Strong Since 1978</em>",
    img=f"{IMG}/GHF_CrossFit_Fitness_Exercise_Outdoors_Group_Fitness_Crossfit_Gainesville_2024-01_1.jpg",
    crumb="Thank you",
    actions=[("Explore GHF Tioga", "tioga-center.html", True)],
    page=True,
    hero_cls="hero--compact",
)

# ============================================================ THANK YOU (HYROX)
# Same one-screen rule as its siblings above. HYROX trains at GHF Main, not Tioga.
thankyouhyrox_body = hero(
    "Class requested",
    ["See you on", 'the <span class="serif">floor</span>'],
    "Congratulations on taking the first step toward a healthier, stronger you. One of our "
    "HYROX coaches will follow up shortly to book your class at GHF Main.<br><br>"
    "<strong>What to bring</strong> &mdash; a water bottle, a towel, and comfortable gym clothes and "
    "training shoes. No experience with the stations needed; we start where you are.<br>"
    "<strong>Where to go</strong> &mdash; check in at the GHF Main lobby desk and tell them you are "
    "here for HYROX."
    "<br><br>Questions? Call <a href=\"tel:3523774955\">(352) 377-4955</a> or email "
    "<a href=\"mailto:AJ.Smith@ghfc.com\">AJ.Smith@ghfc.com</a>."
    "<br><br><strong>Your GHF Team</strong> &mdash; <em>Gainesville Strong Since 1978</em>",
    img=f"{IMG}/hyrox-sled.jpg",
    crumb="Thank you",
    actions=[("Explore GHF Main", "main-center.html", True)],
    page=True,
    hero_cls="hero--compact",
)

# ============================================================ THANK YOU (PILATES)
thankyoupilates_body = hero(
    "Session requested",
    ["See you on the", '<span class="serif">reformer</span>'],
    "Congratulations on taking the first step toward a healthier, stronger you. One of our "
    "certified Pilates instructors will follow up shortly to book your first session.<br><br>"
    "<strong>Pick your studio</strong> &mdash; Main or Tioga, both fully equipped with Reformer, Tower, Chair and suspension straps.<br>"
    "<strong>Start with Foundations</strong> &mdash; our 50-minute Reformer class built for beginners. Your instructor will steer you to the right level."
    "<br><br>Questions? Call <a href=\"tel:3523774955\">(352) 377-4955</a> or email "
    "<a href=\"mailto:memberservices@ghfc.com\">memberservices@ghfc.com</a>."
    "<br><br><strong>Your GHF Team</strong> &mdash; <em>Gainesville Strong Since 1978</em>",
    img=f"{IMG}/GHF_Pilates_Pilates_at_GHF_Pilates_GHF_Main_Gyms_with_Pilates_Pilates_Studio_2025-4.jpg",
    crumb="Thank you",
    actions=[("Explore Our Locations", "locations.html", True)],
    page=True,
    hero_cls="hero--compact",
)

# ============================================================ THANK YOU (X-FORCE)
# X-Force runs at GHF Main — it is the only location that lists the negative-only
# training center among its amenities.
thankyouxforce_body = hero(
    "Session requested",
    ["See you in the", '<span class="serif">studio</span>'],
    "Congratulations on taking the first step toward a healthier, stronger you. One of our "
    "X-Force coaches will follow up shortly to book your free discovery session.<br><br>"
    "<strong>What to expect</strong> &mdash; two 25-minute workouts a week on the X-Force "
    "negative-training machines, with a coach beside you and a carb-smart eating plan to match.<br>"
    "<strong>Where to go</strong> &mdash; the X-Force training center at GHF Main. Check in at the "
    "lobby desk and tell them you are here for X-Force."
    "<br><br>Questions? Call <a href=\"tel:3523774955\">(352) 377-4955</a> or email "
    "<a href=\"mailto:memberservices@ghfc.com\">memberservices@ghfc.com</a>."
    "<br><br><strong>Your GHF Team</strong> &mdash; <em>Gainesville Strong Since 1978</em>",
    img=f"{IMG}/XForce_XForce_Body_GHF_Gain_Muscle_Leg_Exercises_2023.jpg",
    crumb="Thank you",
    actions=[("Explore GHF Main", "main-center.html", True)],
    page=True,
    hero_cls="hero--compact",
)

# ============================================================ CHILL BY GHF
# Content is GHF's own, from ghfc.com/chill. The signup and cancel forms live on
# their own pages because they are vendor-hosted embeds (Formsite and monday.com)
# with no documented POST target — unlike the Keap forms, they cannot be rebuilt
# natively, so they are framed inside our chrome instead.
# The &EmbedId= tail is not decoration: formsite's embedManager.js appends it at
# runtime, and without it the URL returns "Missing or invalid embed id" instead of
# the form. Framing the URL as copied from the old page renders an error page.
CHILL_SIGNUP_EMBED = "https://fs10.formsite.com/res/showFormEmbed?EParam=B6fiTn-RcO7Cqa4xJ-PSQ8yFxcaxnyMuFzpUCZwnDno&amp;2053452483&amp;EmbedId=2053452483"
CHILL_CANCEL_EMBED = "https://forms.monday.com/forms/embed/a181d524e6993bbd98dcbfbbda4e23eb"
REQUEST_PT_APPT = "https://requestphysicaltherapy.com/physical-therapist-appointment/"
CHILL_VIDEO = "https://www.youtube.com/embed/1nn1R4JJxDs"  # "The Chill by GHF Experience"

chill_faq = [
    ("Will I get wet using the hydro massage lounges?",
     "No. You will receive a full body massage with the use of pressurized water. You will simply lie down on the open design bed, fully clothed, and feel the immediate benefits of the traveling jet system."),
    ("How do I sign up for sessions?",
     'Complete the <a href="chill-signup.html">sign-up form</a> and you are done &mdash; it takes about a minute. You can also sign up at the front desk.'),
    ("How many times a week should I do hydro massage?",
     "The frequency of use is up to you. You may use it once a day or once a week."),
    ("How much does it cost?",
     "Introductory pricing is 15 sessions for $15, auto-renewing monthly. Use all 15 sessions in each 30 day period &mdash; sessions do not carry over."),
    ("Can I buy more if I use all of my sessions before 30 days?",
     "Yes. You can buy another 15-session package, which will be non-recurring. This can be charged to your MindBody account, using the credit cards stored in the system."),
    ("Can I buy a single session?",
     "Single sessions are not available. You may have a complimentary session to see what it's like. If you enjoy it, you can purchase 15 sessions for $15 per month."),
    ("How do I cancel?",
     'Inform the desk that you would like to cancel, or <a href="chill-cancel.html">use the cancellation form</a>. You can keep using your remaining sessions until the date your membership would have renewed &mdash; after that they expire.'),
    ("Is there a fee to cancel?", "No."),
    ("Am I able to do more than 10 minutes at a time?",
     "Yes, unless someone is waiting to use a lounge."),
    ("Can I buy a month (or more) for someone as a gift?",
     "Yes &mdash; the gift must be for an existing GHF member. Gift cards are available at the front desk."),
]

chill_body = hero(
    "Chill by GHF",
    ["Recovery is the part", 'most people <span class="serif">skip</span>'],
    "HydroMassage lounges and CryoLounge+ recovery chairs, in a studio built to serve the whole person. Ten minutes, fully clothed, before or after your workout &mdash; and your first session is free.",
    img=f"{IMG}/Chill_GHF_Hydromassage_Massage_Bed_Gainesville_2025-2.jpg",
    crumb='Fitness &nbsp;/&nbsp; Chill Studio',
    actions=[("Sign Up For Chill", "chill-signup.html", True), ("Cancel Chill", "chill-cancel.html", False)],
    meta=["GHF Main &amp; GHF Tioga", "10-minute sessions", "First session free"],
    page=True,
) + split(
    "HydroMassage", "01",
    'Technology to relax and <span class="serif">recover</span>',
    ["The accumulated stresses of everyday life can damage your health in irreversible ways &mdash; from early aging to heart problems and long-term disability. You cannot eliminate stress, but you can manage it, and it is worth every effort to do so.",
     "Each session is 10 minutes and will loosen up muscles, increase oxygen and blood flow into muscles, remove the lactic acid buildup that makes you sore, and deliver nutrients from your body to your muscles. You will walk out of the gym feeling like a new person."],
    f"{IMG}/post-workout-recovery-chill-hydromassage-lounge-700x467.jpg",
    "HydroMassage lounge in the Chill studio at GHF",
    tag="Chill Studio",
) + split(
    "CryoLounge+", "02",
    'Recover faster with <span class="serif">cold and heat</span>',
    ["CryoLounge+ is an advanced recovery chair with complementary cold and heat zones. Cold is applied to target soreness or minor aches and pains, while heat is applied in other areas of the body for a comfortable experience.",
     "Athletes worldwide have long relied on cold and heat therapy as essential parts of their training &mdash; ice baths, hot tubs, cryotherapy chambers and heating pads. GHF has made that way of recovering faster accessible to you. Stop by the front desk to try a free session."],
    f"{IMG}/Chill_GHF_Hydromassage_Cryobed_Gainesville_2025-2.jpg",
    "CryoLounge+ recovery chair at GHF",
    rev=True, tag="CryoLounge+",
) + f"""
<section class="section" id="video">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">See it for yourself</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">The Chill <span class="serif">experience</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Ten minutes in the studio, start to finish &mdash; what a session actually looks like before you book one.</p>
    </div>
    <div class="reveal">{embed(CHILL_VIDEO, "The Chill by GHF Experience", allow_yt=True)}</div>
  </div>
</section>

<section class="section section--light" id="pricing">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Pricing</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Fifteen sessions, <span class="serif">fifteen dollars</span></h2>
        <p class="lede reveal" style="margin-top:28px">15 ten-minute sessions for $15 a month, or 30 for $25 &mdash; both including CryoLounge+. Subscriptions auto-renew monthly until cancelled, and unused sessions do not roll over to the following month. Located at GHF Main and GHF Tioga.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>15 ten-minute sessions &mdash; $15 a month</li>
          <li>30 ten-minute sessions &mdash; $25 a month</li>
          <li>Includes two 10-minute CryoLounge+ sessions</li>
          <li>Auto-renews monthly; unused sessions do not roll over</li>
          <li>No fee to cancel &mdash; use your remaining sessions up to your renewal date</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section" id="begin">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">How to begin</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Try a complimentary <span class="serif">session</span></h2>
        <p class="lede reveal" style="margin-top:28px">Stop by the desk before or after your workout and try it at no charge. When you are ready, complete the sign-up form &mdash; that is all it takes.</p>
      </div>
      <div class="intro-grid__right reveal">
        <div class="hero__actions" style="margin:0">
          <a class="btn btn--solid" href="chill-signup.html">Sign Up For Chill <span class="arr">&rarr;</span></a>
        </div>
        <!-- Cancelling gets its own labelled block, not a greyed sibling of Sign Up:
             nobody should have to hunt for how to stop paying. -->
        <div class="note-box" style="margin-top:30px">
          <p class="eyebrow" style="margin-bottom:10px">Already a Chill member?</p>
          <p class="body-copy"><strong>You can cancel any time, and there is no fee.</strong> Cancelling stops the next renewal &mdash; your remaining sessions stay usable until the date it would have renewed, and expire after that. Tell the front desk, or do it online in under a minute.</p>
          <div class="hero__actions" style="margin-top:20px">
            <a class="btn" href="chill-cancel.html">Cancel Chill <span class="arr">&rarr;</span></a>
          </div>
        </div>
        <p class="form-note" style="margin-top:26px">Prefer hands-on? ReQuest Physical Therapy offers therapeutic massage inside both our Main and Tioga facilities.
        <a href="{REQUEST_PT_APPT}" target="_blank" rel="noopener">Schedule a massage appointment &rarr;</a></p>
      </div>
    </div>
  </div>
</section>

<section class="section section--light" id="faq">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Questions</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Chill, <span class="serif">answered</span></h2>
      </div>
    </div>
    {accordion(chill_faq)}
  </div>
</section>
""" + f"""
<section class="section" id="pass">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Request your pass</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Come try the Chill studio for <span class="serif">free</span></h2>
        <p class="lede reveal" style="margin-top:28px">Your free all-access pass gives you full membership privileges for one day at any GHF location &mdash; the Chill studio included. No charge, no obligation and no risk.</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-pass.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_XID}">
          <input type="hidden" name="inf_form_name" value="All Access Pass">
          <input type="hidden" name="infusionsoft_version" value="1.70.0.60815">
          <input type="hidden" name="inf_IntegrationName" value="pv228">
          <input type="hidden" name="inf_CallName" value="allaccesspass">
          <input type="hidden" name="inf_api_enabled" value="true">
          <div class="field"><input type="text" name="inf_field_FirstName" id="ch-first" placeholder=" " required><label for="ch-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="ch-last" placeholder=" " required><label for="ch-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="ch-email" placeholder=" " required><label for="ch-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="ch-phone" placeholder=" " required><label for="ch-phone">Phone</label></div>
          <div class="field field--full">
            <select name="inf_custom_Facility" id="ch-loc" aria-label="Gym you would like to visit">
              <option value="">&nbsp;</option>
              <option value="Main">GHF Main &mdash; 4820 W Newberry Road</option>
              <option value="Women's Center">GHF Women &mdash; 2441 NW 43rd Street</option>
              <option value="Tioga">GHF Tioga &mdash; Tioga Town Center</option>
            </select>
            <label for="ch-loc">Gym you would like to visit</label>
          </div>
          <button class="btn field--full" type="submit" style="justify-content:center">Claim My Free Fitness Pass <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">Submit the form and we'll be in touch by phone, text or email to set up your pass.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Train hard. <span class="serif">Recover harder.</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/GHF_Recovery_Workout_Recovery_Massage_Exercise_Fitness_Gyms_2025.jpg",
)

chill_signup_body = hero(
    "Sign up for Chill",
    ["Fifteen sessions,", '<span class="serif">fifteen dollars</span>'],
    "Complete the form below and your Chill membership is set up &mdash; that is the whole process. 15 sessions for $15 a month or 30 for $25, auto-renewing, with CryoLounge+ included."
    "<br><br>Not sure yet? <a href=\"chill.html#begin\">Try a complimentary session</a> at the desk first.",
    img=f"{IMG}/Chill_GHF_Hydromassage_Massage_Bed_Gainesville_2025-2.jpg",
    crumb='Chill &nbsp;/&nbsp; Sign Up',
    page=True,
    hero_cls="hero--compact",
) + f"""
<section class="section section--light">
  <div class="wrap">
    {embed(CHILL_SIGNUP_EMBED, "Sign up for Chill by GHF", tall=True)}
    <p class="form-note" style="margin-top:24px">Trouble with the form? Call <a href="tel:3523774955">(352) 377-4955</a> or ask at the front desk &mdash; we can sign you up in person.</p>
  </div>
</section>
"""

chill_cancel_body = hero(
    "Cancel Chill",
    ["No fee. Use your sessions", 'up to your <span class="serif">renewal date</span>'],
    "Cancelling Chill costs nothing. It stops your next renewal &mdash; you can keep using the sessions you have left up to the date it would have renewed, and they expire after that. Complete the form below, or simply tell the front desk."
    "<br><br>Changed your mind? <a href=\"chill.html\">Back to Chill by GHF</a>.",
    img=f"{IMG}/Chill_by_GHF_hydromassage_room_Gainesville_health_and_fitness_copy.jpg",
    crumb='Chill &nbsp;/&nbsp; Cancel',
    page=True,
    hero_cls="hero--compact",
) + f"""
<section class="section section--light">
  <div class="wrap">
    {embed(CHILL_CANCEL_EMBED, "Cancel your Chill membership", tall=True)}
    <p class="form-note" style="margin-top:24px">You can also cancel in person &mdash; just let the front desk know. Questions? Call <a href="tel:3523774955">(352) 377-4955</a>.</p>
  </div>
</section>
"""


# ============================================================ J-BAR
# Menu extracted from ghfc.com/j-bar — 32 items across 5 categories, names and
# ingredients verbatim. Two source quirks fixed rather than copied: "Berry Bowl"
# had lost its <strong> wrapper, and their own nav links "Additional Products" to
# #more while the anchor is #add, so that link is broken on the live site.
JBAR_VIDEO = "https://www.youtube.com/embed/QJ36IdN_9jY"  # "The Matcha Madness Smoothie from JBar by GHF"

jbar_body = hero(
    "J-Bar by GHF",
    ["Crafted shakes,", 'bowls &amp; <span class="serif">more</span>'],
    "Real fruit, whey protein and a blender, inside GHF Main. Smoothies, acai bowls, parfaits and grab-and-go &mdash; and you do not need to be a member to order one.",
    img=f"{IMG}/jbar-smoothie-collection.jpg",
    crumb='Amenities &nbsp;/&nbsp; J-Bar',
    actions=[("See The Menu", "#menu", True), ("Hours", "#hours", False)],
    meta=["Inside GHF Main", "Open to everyone", "Made to order"],
    page=True,
) + split(
    "Smoothies worthy of your efforts", "01",
    'Real ingredients, <span class="serif">every time</span>',
    ["Nestled inside GHF Main is J-Bar, your one-stop destination for all things smoothies &mdash; from delectable fruit smoothies to invigorating protein shakes. Our standout varieties include the refreshing Strawberry Banana blend and the energizing Peanut Butter Blitz.",
     "Our acai bowls are a testament to the vibrancy of real ingredients, and the smoothie bowls offer a delightful combination of taste and texture, making them the perfect meal replacements or fulfilling snacks. For those particular about protein intake, our shakes are crafted with high-quality whey protein."],
    f"{IMG}/jbar-counter.jpg",
    "The J-Bar smoothie counter at GHF Main",
    tag="GHF Main",
) + split(
    "Any time of day", "02",
    'Breakfast, snack or <span class="serif">recovery</span>',
    ["Whether you're winding down after an intense workout, looking for a healthy breakfast option, or just in the mood for a tantalizing treat, J-Bar caters to every palate and purpose. And the best part? You don't need to be a GHF member to relish our handcrafted delicacies.",
     "We believe nutrition is the cornerstone of wellness, complementing every rep you lift, every mile you run, and every stretch you hold. We're not just a smoothie bar; we're a part of your holistic fitness story."],
    f"{IMG}/jbar-smoothie-friends.jpg",
    "Friends with J-Bar smoothies at GHF",
    rev=True, tag="No membership needed",
) + f"""
<section class="section" id="video">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">Watch one get made</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">The Matcha <span class="serif">Madness</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Milk, pineapple juice, mango, whey protein, spinach and matcha powder &mdash; start to finish at the J-Bar counter.</p>
    </div>
    <div class="reveal">{embed(JBAR_VIDEO, "The Matcha Madness Smoothie from JBar by GHF", allow_yt=True)}</div>
  </div>
</section>

<section class="section section--light" id="menu">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">The menu</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Thirty-two ways to <span class="serif">refuel</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Every smoothie is made to order with real fruit. Add whey protein, branched-chain amino acids or a superfood boost to any of them.</p>
    </div>
    <div class="menu-grid reveal">
      <div class="menu-cat">
        <h3 class="menu-cat__head">Fruit Smoothies <span class="menu-cat__n">9</span></h3>
        <ul class="menu-list">
          <li><strong>Strawberry Banana</strong> <span>Strawberry Kiwi Juice | Strawberry | Banana</span></li>
          <li><strong>Mango Blast</strong> <span>Tropical Juice | Mango | Strawberry | Whey Protein | Superfood</span></li>
          <li><strong>In The Tropics</strong> <span>Tropical Juice | Pineapple | Banana</span></li>
          <li><strong>Blue Heaven</strong> <span>Tropical Juice | Blueberry | Pineapple</span></li>
          <li><strong>Berry Health Fusion</strong> <span>Four Berry Juice | Blueberry | Banana | Berry Health Fusion Mix | Whey Protein | Fish Oil</span></li>
          <li><strong>Pineapple Recovery</strong> <span>Pineapple Juice | Pineapple | Banana | Whey Protein Isolate | BCAA</span></li>
          <li><strong>Lean Body Maker</strong> <span>Water | Banana | Whey Protein Isolate | Superfood</span></li>
          <li><strong>Jungle Juice</strong> <span>Pineapple Juice | Banana | Pineapple | Spinach | Whey Protein</span></li>
          <li><strong>Matcha Madness</strong> <span>Milk | Pineapple Juice | Mango | Whey Protein | Spinach | Matcha Powder</span></li>
        </ul>
      </div>
      <div class="menu-cat">
        <h3 class="menu-cat__head">Peanut Butter Delights <span class="menu-cat__n">5</span></h3>
        <ul class="menu-list">
          <li><strong>Java Nut</strong> <span>Milk | Banana | Almond | Coffee | Whey Protein | Peanut Butter | Chocolate Sauce</span></li>
          <li><strong>Peanut Butter Blitz</strong> <span>Milk | Banana | Whey Protein | Peanut Butter</span></li>
          <li><strong>PB&amp;J</strong> <span>Four Berry Juice | Whey Protein | Blueberry | Strawberry | Peanut Butter</span></li>
          <li><strong>Haus</strong> <span>Milk | Banana | Peanut Butter | Whey Protein | Greek Yogurt | Chocolate Sauce</span></li>
          <li><strong>Joe's Smoothie</strong> <span>Milk | Banana | Blueberry | Peanut Butter | Whey Protein</span></li>
        </ul>
      </div>
      <div class="menu-cat">
        <h3 class="menu-cat__head">Power Parfaits <span class="menu-cat__n">4</span></h3>
        <ul class="menu-list">
          <li><strong>Protein Parfait</strong> <span>Greek Yogurt | Granola | Honey | Strawberry | Blueberry</span></li>
          <li><strong>Wildberry Parfait</strong> <span>Greek Yogurt | Granola | Blackberry | Raspberry | Honey</span></li>
          <li><strong>Four Berry Protein Parfait</strong> <span>Greek Yogurt | Granola | Blackberry | Raspberry | Blueberry | Strawberry | Honey</span></li>
          <li><strong>Strawberry Banana Protein Parfait</strong> <span>Greek Yogurt | Granola | Strawberry | Banana | Honey</span></li>
        </ul>
      </div>
      <div class="menu-cat">
        <h3 class="menu-cat__head">Acai Bowls <span class="menu-cat__n">5</span></h3>
        <ul class="menu-list">
          <li><strong>Rainbowl</strong> <span>Acai | Granola | Strawberry | Kiwi | Blueberry | Banana</span></li>
          <li><strong>J-Bowl</strong> <span>Acai | Granola | Strawberry | Banana | Honey | Almond</span></li>
          <li><strong>Beach Bum</strong> <span>Acai | Granola | Blueberry | Banana</span></li>
          <li><strong>PB&amp;J Bowl</strong> <span>Acai | Peanut Butter | Granola | Blueberry | Strawberry | Honey</span></li>
          <li><strong>Berry Bowl</strong> <span>Acai | Granola | Strawberry | Blueberry | Blackberry | Raspberry | Honey</span></li>
        </ul>
      </div>
      <div class="menu-cat">
        <h3 class="menu-cat__head">Additional Products <span class="menu-cat__n">9</span></h3>
        <ul class="menu-list">
          <li><strong>Monster Energy Drinks</strong> <span>Assorted Flavors</span></li>
          <li><strong>Alani Nu Energy Drinks</strong> <span>Assorted Flavors</span></li>
          <li><strong>BUM Energy Drinks</strong> <span>Assorted Flavors</span></li>
          <li><strong>Ghost Energy Drinks</strong> <span>Assorted Flavors</span></li>
          <li><strong>Gorilla Mind Energy Drinks</strong> <span>Assorted Flavors</span></li>
          <li><strong>Celcius</strong> <span>Assorted Flavors</span></li>
          <li><strong>Core Power Ready-To-Drink Protein Shake</strong> <span>Strawberry, Chocolate, Vanilla available in 26g and 42g of protein</span></li>
          <li><strong>Hard-Boiled Eggs</strong></li>
          <li><strong>Sandwiches</strong></li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="section" id="hours">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Hours</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Open early, <span class="serif">open late</span></h2>
        <p class="lede reveal" style="margin-top:28px">You will find the J-Bar just inside GHF Main at 4820 W Newberry Road. Walk in and order &mdash; no membership, no app, no waiting on a table.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li><strong>Monday &ndash; Friday</strong> &nbsp; 6:00am &ndash; 9:00pm</li>
          <li><strong>Saturday &ndash; Sunday</strong> &nbsp; 8:00am &ndash; 6:00pm</li>
        </ul>
        <div style="margin-top:26px"><a class="inline-link" href="main-center.html">More about GHF Main &rarr;</a></div>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Fuel the work you just <span class="serif">put in</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/jbar-acai-bowl.jpg",
)


# ============================================================ COURT SPORTS
# Content from ghfc.com/court-sports, image from ghfc.com/basketball.
# NOTE: the two source pages disagree on volleyball nights — /court-sports says
# "Wednesday 6-11p & Sunday 5-10p", /basketball says "Thursday & Sunday". We follow
# court-sports: it carries the actual times, and it matches what this site already
# says on amenities.html and sports-activities.html. Worth confirming with the desk.
courtsports_body = hero(
    "Court Sports at GHF",
    ["Get in the", '<span class="serif">game</span>'],
    "Want to shoot some hoops or play some volleyball? Our indoor courts are dynamic and functional for all levels of performance &mdash; and every membership includes them at no extra charge.",
    img=f"{IMG}/GHF_Basketball_2_1.jpg",
    crumb='Fitness &nbsp;/&nbsp; Court Sports',
    actions=[("Get Your Free All-Access Pass", "#pass", True), ("Play Times", "#times", False)],
    meta=["Six hoops", "Hardwood floor", "Included in membership"],
    page=True,
) + split(
    "Indoor basketball and volleyball", "01",
    'One court, <span class="serif">two games</span>',
    ["A regulation-size indoor basketball court with six basketball hoops and hardwood flooring &mdash; the perfect game, whether you are shooting alone or running full-court with friends.",
     "The same floor carries regulation volleyball court dimensions. All that is required is a quick set-up of the volleyball net, and game on."],
    f"{IMG}/GHF_Basketball_5.jpg",
    "Regulation-size indoor basketball and volleyball court at GHF",
    tag="GHF Main",
) + f"""
<section class="section section--light" id="times">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">When to play</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Know before you <span class="serif">go</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">The court switches between full-court, half-court and volleyball through the week. Here is how it runs.</p>
    </div>
    <div class="rows reveal">
      <div class="row-item">
        <span class="row-item__idx">01</span>
        <span class="row-item__title">Full-Court Basketball</span>
        <span class="row-item__desc">Six days a week &mdash; weekdays 6:00&ndash;10:00am, and Sundays 11:00am&ndash;2:00pm.</span>
      </div>
      <div class="row-item">
        <span class="row-item__idx">02</span>
        <span class="row-item__title">Half-Court Basketball</span>
        <span class="row-item__desc">Every other time the court is open. Turn up, pick a hoop and play.</span>
      </div>
      <div class="row-item">
        <span class="row-item__idx">03</span>
        <span class="row-item__title">Volleyball</span>
        <span class="row-item__desc">Twice a week &mdash; Wednesdays 6:00&ndash;11:00pm and Sundays 5:00&ndash;10:00pm. The net goes up and the court is yours.</span>
      </div>
      <div class="row-item">
        <span class="row-item__idx">04</span>
        <span class="row-item__title">Included In Your Membership</span>
        <span class="row-item__desc">All memberships include use of the court at no extra charge. No booking fee, no court hire.</span>
      </div>
    </div>
    <div class="reveal" style="margin-top:34px"><a class="inline-link" href="main-center.html">More about GHF Main &rarr;</a></div>
  </div>
</section>

<section class="section" id="pass">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Request your pass</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Come get in the <span class="serif">game</span></h2>
        <p class="lede reveal" style="margin-top:28px">Your free all-access pass gives you full membership privileges for one day at any GHF location &mdash; the court included. No charge, no obligation and no risk.</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-pass.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_XID}">
          <input type="hidden" name="inf_form_name" value="All Access Pass">
          <input type="hidden" name="infusionsoft_version" value="1.70.0.60815">
          <input type="hidden" name="inf_IntegrationName" value="pv228">
          <input type="hidden" name="inf_CallName" value="allaccesspass">
          <input type="hidden" name="inf_api_enabled" value="true">
          <div class="field"><input type="text" name="inf_field_FirstName" id="cs-first" placeholder=" " required><label for="cs-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="cs-last" placeholder=" " required><label for="cs-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="cs-email" placeholder=" " required><label for="cs-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="cs-phone" placeholder=" " required><label for="cs-phone">Phone</label></div>
          <div class="field field--full">
            <select name="inf_custom_Facility" id="cs-loc" aria-label="Gym you would like to visit">
              <option value="">&nbsp;</option>
              <option value="Main">GHF Main &mdash; 4820 W Newberry Road</option>
              <option value="Women's Center">GHF Women &mdash; 2441 NW 43rd Street</option>
              <option value="Tioga">GHF Tioga &mdash; Tioga Town Center</option>
            </select>
            <label for="cs-loc">Gym you would like to visit</label>
          </div>
          <button class="btn field--full" type="submit" style="justify-content:center">Claim My Free Fitness Pass <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">Submit the form and we'll be in touch by phone, text or email to set up your pass.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Bring your <span class="serif">competitive streak</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/GHF_Basketball_5.jpg",
)


# ============================================================ ECHO
# Content from ghfc.com/echo. The schedule is scoped to Perch's OUTDOOR/LOBBY room —
# the feed has no Echo or pavilion room at all, and 4 of its 5 outdoor classes are at
# Tioga, so the section is headed "outdoor classes across GHF" rather than presented as
# Echo's own. Tagging Echo classes in Perch would make it fill in automatically.
ECHO_VIDEO = "https://www.youtube.com/embed/rw-fEoJXjHg"  # "The Story of Echo of GHF"

echo_body = hero(
    "Echo Outdoor Pavilion",
    ["Gainesville's largest", 'outdoor <span class="serif">gym</span>'],
    "Six thousand square feet of open-air training at GHF Main &mdash; tires, sleds, ropes, TRX and rigs under cover, plus classes, workshops and community events. Included in your membership.",
    img=f"{IMG}/echo-pavilion.jpg",
    crumb='Amenities &nbsp;/&nbsp; Echo',
    actions=[("Outdoor Classes", "#classes", True), ("What Else Runs Here", "#expect", False)],
    meta=["6,000 sq ft", "At GHF Main", "Included in membership"],
    page=True,
) + split(
    "What to expect", "01",
    'Make up your own <span class="serif">workout</span>',
    ["The outdoor fitness pavilion offers functional training workout space, specialty workshops, GroupFit classes and lifestyle events. You have access to open gym times to use tires, sleds, ropes, TRX, dumbbells, rowers, bikes, ski ergs and more.",
     "It's the perfect open-air space to make up your own workouts. Bring a towel and water."],
    f"{IMG}/echo-functional-training.jpg",
    "Functional training at the Echo outdoor pavilion",
    tag="Echo",
) + f"""
<section class="section section--light" id="story">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">The story behind Echo</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">How it came to <span class="serif">be</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Gainesville's largest open-air training destination, and why GHF built it.</p>
    </div>
    <div class="reveal">{embed(ECHO_VIDEO, "The Story of Echo of GHF", allow_yt=True)}</div>
  </div>
</section>
""" + schedule_block("classes", "Outdoor classes across GHF",
                 'Train under the <span class="serif">open sky</span>',
                 "Every class Perch lists outdoors, live. Filter by location, class type, day or instructor &mdash; all of them are included in your membership.",
                 room="OUTDOOR/LOBBY") + f"""
<section class="section" id="expect">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow">More than classes</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">What else runs <span class="serif">out here</span></h2>
      </div>
    </div>
    <div class="rows reveal">
      <a class="row-item" href="team-strong-training.html">
        <span class="row-item__idx">01</span>
        <span class="row-item__title">TEAM Strong Punch</span>
        <span class="row-item__desc">A high-energy workout that burns calories, boosts endurance, sculpts muscles and builds confidence &mdash; aimed at agility, strength and cardiovascular fitness.</span>
        <span class="row-item__arrow">&rarr;</span>
      </a>
      <a class="row-item" href="hyrox.html">
        <span class="row-item__idx">02</span>
        <span class="row-item__title">HYROX Training</span>
        <span class="row-item__desc">GHF is an official HYROX Training Club, bringing the world's fastest-growing fitness format to Gainesville &mdash; whether you are training to compete or just want the most effective functional workout you have done.</span>
        <span class="row-item__arrow">&rarr;</span>
      </a>
      <a class="row-item" href="group-fitness.html#schedule">
        <span class="row-item__idx">03</span>
        <span class="row-item__title">Specialty Wellness Workshops</span>
        <span class="row-item__desc">Each workshop is created to expand your mind, stretch, strengthen or tone your body, and enhance your soul.</span>
        <span class="row-item__arrow">&rarr;</span>
      </a>
      <div class="row-item">
        <span class="row-item__idx">04</span>
        <span class="row-item__title">Member Workout Hours</span>
        <span class="row-item__desc">6,000 sq ft of tires, sleds, ropes, cardio equipment and TRX during designated open gym times. Use of the outdoor pavilion is included in your membership.</span>
      </div>
      <div class="row-item">
        <span class="row-item__idx">05</span>
        <span class="row-item__title">Community Events</span>
        <span class="row-item__desc">Farmers markets, lululemon shop events, Gator game tailgates, Halloween trick-or-treat, pictures with Santa, cook outs, craft fairs and family fitness events.</span>
      </div>
    </div>
  </div>
</section>

<section class="section section--light" id="pass">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow">Request your pass</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Come train <span class="serif">outside</span></h2>
        <p class="lede reveal" style="margin-top:28px">Your free all-access pass gives you full membership privileges for one day at any GHF location &mdash; Echo included. No charge, no obligation and no risk.</p>
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" method="post" action="{KEAP_ACTION}" accept-charset="UTF-8" data-thanks="thank-you-pass.html">
          <input type="hidden" name="inf_form_xid" value="{KEAP_XID}">
          <input type="hidden" name="inf_form_name" value="All Access Pass">
          <input type="hidden" name="infusionsoft_version" value="1.70.0.60815">
          <input type="hidden" name="inf_IntegrationName" value="pv228">
          <input type="hidden" name="inf_CallName" value="allaccesspass">
          <input type="hidden" name="inf_api_enabled" value="true">
          <div class="field"><input type="text" name="inf_field_FirstName" id="ec-first" placeholder=" " required><label for="ec-first">First name</label></div>
          <div class="field"><input type="text" name="inf_field_LastName" id="ec-last" placeholder=" " required><label for="ec-last">Last name</label></div>
          <div class="field"><input type="email" name="inf_field_Email" id="ec-email" placeholder=" " required><label for="ec-email">Email address</label></div>
          <div class="field"><input type="tel" name="inf_field_Phone1" id="ec-phone" placeholder=" " required><label for="ec-phone">Phone</label></div>
          <div class="field field--full">
            <select name="inf_custom_Facility" id="ec-loc" aria-label="Gym you would like to visit">
              <option value="">&nbsp;</option>
              <option value="Main">GHF Main &mdash; 4820 W Newberry Road</option>
              <option value="Women's Center">GHF Women &mdash; 2441 NW 43rd Street</option>
              <option value="Tioga">GHF Tioga &mdash; Tioga Town Center</option>
            </select>
            <label for="ec-loc">Gym you would like to visit</label>
          </div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Claim My Free Fitness Pass <span class="arr">&rarr;</span></button>
        </form>
        <p class="form-note">Submit the form and we will be in touch by phone, text or email to set up your pass.</p>
      </div>
    </div>
  </div>
</section>
""" + cta_band(
    'Training, <span class="serif">outdoors</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/echo-outdoor-yoga.jpg",
)


# ============================================================ BUILD ALL
PAGES = [
    ("index.html", "Gainesville Health & Fitness | The Gym That's Best At Helping Beginners", "The gym that's best at helping beginners — with staff to guide your journey. 3 locations, 900+ classes monthly, open 24/7 at GHF Main.", "", home_body),
    ("why-ghf.html", "Why GHF? | Gainesville Health & Fitness", "Offering you more programs, classes, choices, and variety than any other gym.", "why-ghf.html", why_body),
    ("amenities.html", "Best Gym Amenities In One Place | GHF", "More amenities. More support. More results. 24/7 access at Gainesville Health & Fitness.", "amenities.html", amenities_body),
    ("group-fitness.html", "Fitness Classes at GHF | 900+ Group Classes Monthly", "With over 900 classes per month across our three gym locations, GHF offers the best variety of group fitness classes in Gainesville.", "group-fitness.html", groupfit_body),
    ("personal-training.html", "Personal Training | I Train For Life | GHF", "Personal Training at GHF gives you the guidance, motivation and accountability to take your fitness to the next level.", "training.html", pt_body),
    ("strength-training.html", "Strength Training at GHF | Largest Strength Gym in Gainesville", "The largest strength training gym in Gainesville, FL — free weights, platforms, X-Force, and the new Leg Den.", "", strength_body),
    ("cardio.html", "Cardio Fitness at GHF | Gainesville Health & Fitness", "Keep your heart healthy with the widest variety of cardio equipment in Gainesville and 225 personal TVs.", "", cardio_body),
    ("pool.html", "Indoor Aqua Center | Aquix by GHF", "Gainesville's ONLY full-service aqua center — 75-ft lap pool, salt sauna, steam, cold plunge, warm pool, whirlpool.", "", pool_body),
    ("hot-yoga.html", "Hot Yoga Classes | Three Temperatures, One Stunning Studio | GHF", "Gainesville's most advanced hot yoga studio with three temperature settings — 85°, 95°, and 105°.", "", hotyoga_body),
    ("pilates.html", "Pilates Classes in Gainesville, FL | GHF", "The best Pilates classes in Gainesville — Reformer, Tower, Chair, and Cadillac. First session free.", "", pilates_body),
    ("tribe.html", "TRIBE Team Training | Small Team Training at GHF", "The only small team training program with 8-week seasons. One body, one unit, one team, one tribe.", "", tribe_body),
    ("recovery.html", "Recovery at GHF | The Holistic Recovery Approach", "Meet your new fitness edge: Recovery. Pool & spa, hydro massage, physical therapy, restorative classes.", "", recovery_body),
    ("kids-club.html", "Kid's Club at GHF | Free Babysitting While You Work Out", "Free babysitting as a member benefit while you workout at any of our three fitness centers.", "", kids_body),
    ("weight-loss.html", "Weight Loss at GHF | Accelerate Your Results", "GHF has all the equipment, programs, and experts to help you reach your weight loss goals.", "", weightloss_body),
    ("locations.html", "Locations & Hours | One Membership, Three Locations | GHF", "View hours and amenities for our three gyms in Gainesville, FL.", "locations.html", locations_body),
    ("main-center.html", "GHF Main | 24/7 Gym in Gainesville, FL", "GHF Main — 130,000 sq ft, open 24/7 at 4820 W Newberry Road. Virtual tour, photo gallery, hours, and everything included in your membership.", "locations.html", main_center_body),
    ("womens-center.html", "GHF Women | Women-Only Gym in Gainesville, FL", "GHF Women — Gainesville's only women-only fitness club, with all-female staff, Studio Q and 175 classes a month. Take the virtual tour.", "locations.html", womens_center_body),
    ("tioga-center.html", "GHF Tioga | Gym in Tioga Town Center, Newberry FL", "GHF Tioga — the most convenient gym west of I-75, with a private Pilates studio, outdoor CrossFit turf and Hydro Massage in the Chill Studio.", "locations.html", tioga_center_body),
    ("join.html", "Join Online | Gainesville's Best Gym Memberships | GHF", "Join Gainesville's best gym online — $29.99 + tax, dues every other Wednesday, no maintenance fee. 24 month, 12 month, and month-to-month agreements.", "", join_body),
    ("training.html", "Signature Training Programs | GHF", "Reach a higher level of fitness with Personal Training, Pilates, CrossFit, X-Force Body, and TRIBE Team Training.", "personal-training.html", training_body),
    ("crossfit.html", "CrossFit at GHF Tioga | The Pursuit of Optimal Fitness", "GHF CrossFit is open to the community — free first class, Olympic lifting, and youth classes.", "", crossfit_body),
    ("xforce.html", "X-Force Body | Lose Body Fat Fast | GHF", "Gainesville's top choice for accelerated fat loss — negative training, 2 × 25-minute workouts weekly.", "", xforce_body_page),
    ("hyrox.html", "HYROX Training in Gainesville | Official HYROX Training Club | GHF", "Gainesville Health & Fitness is an official HYROX Training Club — eight runs, eight stations, race-day equipment and coaching for every level, at GHF Main.", "", hyrox_body),
    ("team-strong-training.html", "Team Strong Training | GHF", "PLACEHOLDER — Team-based strength training at Gainesville Health & Fitness.", "", teamstrong_body),
    ("seniors.html", "Senior Fitness Classes | Fitness For Life | GHF", "Club Seniors at GHF — resort-style amenities, senior-friendly classes, and a community of seniors just like you.", "", seniors_body),
    ("sports-activities.html", "Sports Activities at GHF | Basketball, Pool, Cycling & More", "Basketball, volleyball, lap pool, HIIT, indoor cycling and sports performance at Gainesville Health & Fitness.", "", sports_body),
    ("special-needs-fitness.html", "FIT for ALL | Special Needs Fitness at GHF", "Fun Inclusive Training (FIT) for ALL is a free fitness program designed for individuals with special needs.", "", fitforall_body),
    ("bring-a-guest.html", "Bring a Guest | 6 Free Visits | GHF", "The Power Of Friends Guest program — each guest visiting with a member gets 6 free visits.", "", guest_body),
    ("member-savings.html", "Member Savings Program | GHF", "Save the cost of your gym membership dues at over 100 participating local businesses.", "", savings_body),
    ("chill.html", "Chill by GHF | HydroMassage & CryoLounge+ Recovery Studio", "HydroMassage lounges and CryoLounge+ recovery chairs at GHF Main and GHF Tioga. 15 sessions for $15 a month, first session free.", "recovery.html", chill_body),
    ("chill-signup.html", "Sign Up For Chill | Gainesville Health & Fitness", "Sign up for Chill by GHF — 15 HydroMassage and CryoLounge+ sessions for $15 a month.", "recovery.html", chill_signup_body),
    ("chill-cancel.html", "Cancel Chill | Gainesville Health & Fitness", "Cancel your Chill by GHF membership. No fee — use your remaining sessions up to your renewal date.", "recovery.html", chill_cancel_body),
    ("jbar.html", "J-Bar by GHF | Smoothies, Acai Bowls & Protein Shakes in Gainesville", "The J-Bar smoothie cafe inside GHF Main — fruit smoothies, protein shakes, acai bowls and parfaits, made to order with real fruit. No membership required.", "amenities.html", jbar_body),
    ("court-sports.html", "Court Sports at GHF | Indoor Basketball & Volleyball in Gainesville", "Regulation-size indoor basketball court with six hoops and hardwood flooring, plus volleyball twice a week. Included with every GHF membership.", "sports-activities.html", courtsports_body),
    ("echo.html", "Echo Outdoor Pavilion | Outdoor Gym at GHF Main | Gainesville", "Six thousand square feet of open-air training at GHF Main — functional equipment, outdoor classes, workshops and community events. Included in your membership.", "amenities.html", echo_body),
    ("faq.html", "FAQ | Get The Most Out Of Your Gym Membership | GHF", "Frequently asked questions about Gainesville Health & Fitness memberships, amenities, and getting started.", "", faq_body),
    ("ghf-pass.html", "Free All-Access Pass | Try GHF Free | Gainesville Health & Fitness", "Try Gainesville Health & Fitness free. Your all-access pass gives you full membership privileges for one day at any of our three locations — classes, pool, sauna, weight floor and a coach to guide you. No charge, no obligation.", "", ghf_pass_body),
    ("contact.html", "Contact Us & Get Pricing | Gainesville Health & Fitness", "Let's talk fitness memberships in Gainesville — pricing packages and amenities to craft your gym experience.", "", contact_body),
    ("thank-you-pricing.html", "Thank You | Gainesville Health & Fitness", "Thanks for requesting gym pricing from Gainesville Health & Fitness. A team member will follow up shortly with membership options.", "", thankyou_body),
    ("thank-you-pass.html", "Thank You | Free Pass | Gainesville Health & Fitness", "Thanks for requesting your free all-access pass. A team member will follow up shortly to set it up.", "", thankyoupass_body),
    ("thank-you-tribe.html", "Thank You | TRIBE Team Training | Gainesville Health & Fitness", "Thanks for requesting your free TRIBE Team Training session. A coach will follow up shortly to book it.", "", thankyoutribe_body),
    ("thank-you-crossfit.html", "Thank You | CrossFit at GHF Tioga | Gainesville Health & Fitness", "Thanks for requesting your free CrossFit class. A coach will follow up shortly to book it at GHF Tioga.", "", thankyoucrossfit_body),
    ("thank-you-hyrox.html", "Thank You | HYROX at GHF | Gainesville Health & Fitness", "Thanks for requesting your HYROX class. A coach will follow up shortly to book it at GHF Main.", "", thankyouhyrox_body),
    ("thank-you-pilates.html", "Thank You | Pilates at GHF | Gainesville Health & Fitness", "Thanks for requesting your free Pilates session. An instructor will follow up shortly to book it at GHF Main or GHF Tioga.", "", thankyoupilates_body),
    ("thank-you-xforce.html", "Thank You | X-Force Body | Gainesville Health & Fitness", "Thanks for requesting your free X-Force Body discovery session. A coach will follow up shortly to book it at GHF Main.", "", thankyouxforce_body),
]


# ============================================================ BLOG (CMS-driven)
POSTS = load_collection("blog")

def blog_index_body():
    if not POSTS:
        cards = '<p class="body-copy">No posts yet — check back soon.</p>'
    else:
        cards = ""
        for p in POSTS:
            num = f'<span class="card__num">{fmt_date(p.get("date"))} · {p.get("author","")}</span>'
            cards += (f'<a class="card" href="blog/{p["_slug"]}.html"><div class="card__media card__media--wide">'
                      f'<img src="{cms_img(p.get("image"))}" alt="{p.get("title","")}" loading="lazy">{num}'
                      f'<div class="card__label"><h3>{p.get("title","")}</h3></div></div>'
                      f'<div class="card__below"><p>{p.get("excerpt","")}</p></div></a>')
    return hero("GHF Blog", ["News &amp;", '<span class="serif">stories</span>'],
        "Member stories, training tips, club news and behind-the-scenes fun — fresh from the team.",
        img=f"{IMG}/Echo_GroupFit_Outdoor_Classes_Fun_Classes_2021.jpg", crumb="Blog",
        actions=[("Join Now", "join.html", True)], page=True,
    ) + f"""
<section class="section"><div class="wrap">
  <div class="cards-head"><div><p class="eyebrow">Latest</p><h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">On the <span class="serif">blog</span></h2></div></div>
  <div class="card-grid" data-stagger>{cards}</div>
</div></section>
""" + cta_band('Come be part of the <span class="serif">story</span>', "There's always something happening. Come see for yourself.", f"{IMG}/GroupFit_Echo_Yoga_Class_Outdoor_Classes_2021.jpg")

def blog_post_body(p):
    others = "".join(
        f'<a class="row-item" href="../blog/{o["_slug"]}.html"><span class="row-item__idx">→</span>'
        f'<span class="row-item__title">{o.get("title","")}</span>'
        f'<span class="row-item__desc">{o.get("excerpt","")}</span><span class="row-item__arrow">→</span></a>'
        for o in POSTS if o["_slug"] != p["_slug"])
    more = f"""
<section class="section section--light"><div class="wrap">
  <div class="cards-head"><div><p class="eyebrow">Keep reading</p><h2 class="h-display reveal" style="font-size:clamp(30px,3.4vw,52px)">More from <span class="serif">the blog</span></h2></div>
  <a class="inline-link reveal" href="../blog.html">All posts →</a></div><div class="rows reveal">{others}</div>
</div></section>""" if others else ""
    return f"""
<section class="hero hero--page hero--post">
  <div class="hero__media"><img src="../{cms_img(p.get('image'))}" alt=""></div>
  <div class="hero__crumb"><div><a href="../index.html">Home</a> &nbsp;/&nbsp; <a href="../blog.html">Blog</a></div></div>
  <div class="hero__inner">
    <p class="hero__kicker">{fmt_date(p.get('date'))} &nbsp;·&nbsp; {p.get('author','Team')}</p>
    <h1 class="hero__title"><span class="ln"><span style="transition-delay:.12s">{p.get('title','')}</span></span></h1>
  </div>
  <div class="hero__scroll" aria-hidden="true"></div>
</section>
<section class="section section--tight"><div class="wrap" style="max-width:760px">
  <div class="post-body reveal">{p['_body']}</div>
  <div class="reveal" style="margin-top:40px"><a class="btn btn--solid" href="../blog.html">← Back to the blog</a></div>
</div></section>
{more}
""" + cta_band('Like what you\'re <span class="serif">reading?</span>', "Come see it in person.", f"../{IMG}/GroupFit_Echo_Yoga_Class_Outdoor_Classes_2021.jpg")

def page_sub(filename, title, desc, body):
    html = head(title, desc) + header_html("blog.html") + body + footer_html()
    html = _re.sub(r'(href|src)="/(?!/)', r'\1="../', html)
    html = _re.sub(r'(href|src)="assets/', r'\1="../assets/', html)
    html = _re.sub(r'(href)="([a-z0-9-]+\.html)(#[^"]*)?"', r'\1="../\2\3"', html)
    os.makedirs(os.path.join(OUT, "blog"), exist_ok=True)
    with open(os.path.join(OUT, filename), "w") as f:
        f.write(html)
    print("built", filename)
# ============================================================ end BLOG

PAGES.append(("blog.html", f"Blog | GHF", "News, stories and tips from GHF.", "blog.html", blog_index_body()))

# ---- CMS-authored pages (content/pages/*.json) ---------------------------------
CMS_PAGES = load_pages()
_cms_filenames = {p["_filename"] for p in CMS_PAGES}

# Merge CMS pages flagged "in_nav" into the site menu (per-page nav toggle),
# ordered by nav_order; dedupe by href so migrated pages don't double up.
_menu_hrefs = {h for _, h in MENU}
for p in sorted(CMS_PAGES, key=lambda x: (x.get("nav_order", 100) or 100)):
    if p.get("in_nav") and p["_filename"] not in _menu_hrefs:
        MENU.append((p.get("nav_label") or p.get("title") or p["_slug"], p["_filename"]))
        _menu_hrefs.add(p["_filename"])

# Build code pages, but let a CMS page override one with the same filename.
_built = 0
for fn, title, desc, active, body in PAGES:
    if fn in _cms_filenames:
        continue
    page(fn, title, desc, active, body)
    _built += 1

# Build the CMS pages.
for p in CMS_PAGES:
    page(p["_filename"], p.get("title", p["_slug"]),
         p.get("description", ""), p.get("active", p["_filename"]),
         render_blocks(p.get("blocks")))
    _built += 1

print("\nDone:", _built, "pages", f"({len(CMS_PAGES)} from CMS)")
for _p in POSTS:
    page_sub(f"blog/{_p['_slug']}.html", f"{_p.get('title','Post')} | GHF Blog", _p.get("excerpt","")[:160], blog_post_body(_p))
print("blog posts:", len(POSTS))
