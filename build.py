#!/usr/bin/env python3
# GHF redesign — static site generator
import os, time, json

OUT = os.path.join(os.path.dirname(__file__), "docs")
IMG = "assets/img"

# ============================================================ CMS content engine
CONTENT = os.path.join(os.path.dirname(__file__), "content")
import glob as _glob, re as _re

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

def brand_logo(src=LOGO_MARK, cls=""):
    return (f'<img class="brand__logo {cls}" src="{src}" '
            f'alt="Gainesville Health &amp; Fitness" width="1000" height="350" />')

NAV = [
    ("Why GHF", "why-ghf.html"),
    ("Classes", "group-fitness.html"),
    ("Training", "training.html"),
    ("Amenities", "amenities.html"),
    ("Locations", "locations.html"),
]

MENU = [
    ("Home", "index.html"),
    ("Why GHF", "why-ghf.html"),
    ("Amenities", "amenities.html"),
    ("Group Classes", "group-fitness.html"),
    ("Hot Yoga", "hot-yoga.html"),
    ("Pilates", "pilates.html"),
    ("Personal Training", "personal-training.html"),
    ("TRIBE Team Training", "tribe.html"),
    ("Strength Training", "strength-training.html"),
    ("Cardio", "cardio.html"),
    ("Pool &amp; Aqua Center", "pool.html"),
    ("Recovery", "recovery.html"),
    ("Weight Loss", "weight-loss.html"),
    ("Kids Club", "kids-club.html"),
    ("Locations &amp; Hours", "locations.html"),
    ("Join Online", "join.html"),
    ("Blog", "blog.html"),
    ("Contact", "contact.html"),
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
<link rel="icon" type="image/svg+xml" href="assets/img/ghf-mark.svg">
<link rel="stylesheet" href="assets/css/main.css?v={V}">
<script>(function(){{try{{
  if(sessionStorage.getItem("ghf-intro"))document.documentElement.classList.add("no-preloader");
  var v=localStorage.getItem("ghf-view");
  document.documentElement.setAttribute("data-view", v==="member"?"member":"guest");
  if(v||sessionStorage.getItem("ghf-view-skip"))document.documentElement.classList.add("has-view");
}}catch(e){{}}}})();</script>
</head>
<body>
<div class="preloader" aria-hidden="true">
  <img class="preloader__logo" src="assets/img/brand/logo-mark.png" alt="Gainesville Health &amp; Fitness" width="1000" height="350" />
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
      <div class="view-toggle" role="group" aria-label="View site as">
        <button type="button" data-view-set="guest">Guest</button>
        <button type="button" data-view-set="member">Member</button>
      </div>
      <a class="btn btn--sm only-guest header-pricing" href="contact.html#pricing">Get Pricing</a>
      <a class="btn btn--solid btn--sm only-guest" href="join.html">Join Online</a>
      <a class="btn btn--solid btn--sm only-member" href="group-fitness.html">Class Schedule</a>
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
        <a class="btn btn--solid btn--sm" href="contact.html#pricing">Free All-Access Pass <span class="arr">→</span></a>
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
          <a href="blog.html">Blog</a>
          <a href="why-ghf.html">Why GHF</a>
          <a href="group-fitness.html">Group Classes</a>
          <a href="personal-training.html">Personal Training</a>
          <a href="strength-training.html">Strength Training</a>
          <a href="amenities.html">Amenities</a>
          <a href="recovery.html">Recovery</a>
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
         actions=None, meta=None, page=False):
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
    sub_html = f'<p class="hero__sub">{sub}</p>' if sub else ""
    return f"""
<section class="hero{' hero--page' if page else ''}">
  <div class="hero__media">{media}</div>
  {crumb_html}
  <div class="hero__inner">
    <p class="hero__kicker">{kicker}</p>
    <h1 class="hero__title">{lns}</h1>
    {sub_html}
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


def split(eyebrow, num, title, paras, img, alt, rev=False, cta=None, tag=None, light=False, wide=False):
    body_paras = "".join(f'<p class="body-copy">{p}</p>' for p in paras)
    cta_html = f'<div class="split__cta"><a class="inline-link" href="{cta[1]}">{cta[0]} →</a></div>' if cta else ""
    tag_html = f'<span class="tag">{tag}</span>' if tag else ""
    return f"""
<section class="section{' section--light' if light else ''}">
  <div class="wrap">
    <div class="split{' split--rev' if rev else ''}">
      <div class="split__media{' split__media--wide' if wide else ''} reveal-img">
        <img src="{img}" alt="{alt}" loading="lazy">{tag_html}
      </div>
      <div class="split__body">
        <p class="eyebrow"><span class="num">{num}</span> {eyebrow}</p>
        <h2 class="h-display" style="font-size:clamp(30px,3.8vw,58px)">{title}</h2>
        <div class="reveal">{body_paras}{cta_html}</div>
      </div>
    </div>
  </div>
</section>
"""


def cta_band(title_html, text, img, primary=("Claim Your Free Pass", "contact.html#pricing"),
             secondary=("Free All-Access Pass", "contact.html#pricing")):
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


def form_section(sec_id, num, eyebrow, title_html, text, btn, fields=None, light=True, extra=""):
    fields = fields or [
        ("text", "first", "First name"), ("text", "last", "Last name"),
        ("email", "email", "Email address"), ("tel", "phone", "Phone"),
    ]
    f_html = ""
    for ftype, name, label in fields:
        f_html += f"""
        <div class="field"><input type="{ftype}" name="{name}" id="{sec_id}-{name}" placeholder=" " required><label for="{sec_id}-{name}">{label}</label></div>"""
    return f"""
<section class="section{' section--light' if light else ''}" id="{sec_id}">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow"><span class="num">{num}</span> {eyebrow}</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">{title_html}</h2>
        <p class="lede reveal" style="margin-top:28px">{text}</p>
        {extra}
      </div>
      <div class="intro-grid__right reveal">
        <form class="form-grid" data-demo>
          {f_html}
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
            head_html = (f'<div class="cards-head"><div><p class="eyebrow"><span class="num">'
                         f'{b.get("num", "")}</span> {b.get("eyebrow", "")}</p>'
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
                f'<p class="eyebrow"><span class="num">{b.get("num", "")}</span> {b.get("eyebrow", "")}</p>'
                f'<h2 class="h-display reveal">{_accent(b.get("title", ""))}</h2>'
                f'<p class="body-copy reveal" style="margin-top:26px">{b.get("text", "")}</p></div>'
                f'<div class="intro-grid__right reveal"><ul class="checklist">{lis}</ul></div>'
                f'</div></div></section>\n')
    if t == "richtext":
        eyebrow = (f'<p class="eyebrow"><span class="num">{b.get("num", "")}</span> {b.get("eyebrow", "")}</p>'
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
view_chooser = f"""
<div class="view-chooser" role="dialog" aria-label="Choose your experience">
  <button class="vc-skip" type="button">Just browsing →</button>
  <div class="view-chooser__head">
    <span class="kicker">Welcome to Gainesville Health &amp; Fitness</span>
    <h2>How are you visiting today?</h2>
  </div>
  <div class="view-chooser__panels">
    <button class="vc-panel" type="button" data-choose="guest">
      <img src="{IMG}/Tioga_Carrie_Grotto_Arm_Cross_Facility_2022.jpg" alt="">
      <div class="vc-panel__body">
        <span class="vc-panel__kicker">First time here?</span>
        <h3>I'm a <span class="serif">guest</span></h3>
        <p>Tour the club, get pricing, and claim your free all-access pass.</p>
        <span class="go">Show me around →</span>
      </div>
    </button>
    <button class="vc-panel" type="button" data-choose="member">
      <img src="{IMG}/GHF_Leg_Den_Leg_Day_Exercise_Fitness_Squats_Deadlifts_2025-2.jpg" alt="">
      <div class="vc-panel__body">
        <span class="vc-panel__kicker">Welcome back</span>
        <h3>I'm a <span class="serif">member</span></h3>
        <p>Class schedules, club hours, Kid's Club, and your member perks.</p>
        <span class="go">Take me in →</span>
      </div>
    </button>
  </div>
</div>
"""

member_strip = """
<div class="member-strip only-member">
  <div class="wrap">
    <span class="hello">Welcome back.</span>
    <a href="group-fitness.html">Class Schedules</a>
    <a href="hot-yoga.html">Hot Yoga</a>
    <a href="kids-club.html#hours">Kid's Club Hours</a>
    <a href="pool.html">Pool &amp; Spa</a>
    <a href="locations.html">Locations &amp; Hours</a>
    <a href="member-savings.html">Member Savings</a>
    <a href="bring-a-guest.html">Bring a Guest</a>
  </div>
</div>
"""

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
        <p class="eyebrow"><span class="num">07</span> Getting started is the easy part</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Your first visit, <span class="serif">mapped out</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:36ch">No contracts to sign, no sales pitch to survive. Just show up and see how it feels.</p>
    </div>
    <div class="steps reveal">
      <div class="step"><span class="step__num">01</span><h3>Claim your free pass</h3><p>One day, full access, zero obligation. Every class, the pool, the sauna, the coaches — on us.</p></div>
      <div class="step"><span class="step__num">02</span><h3>Meet your coach</h3><p>A real human gives you the tour, learns your goal, and walks you through your first workout — so you're never guessing.</p></div>
      <div class="step"><span class="step__num">03</span><h3>Make it a habit</h3><p>A plan that fits your life, people who notice when you show up, and results you can see. That's how one visit becomes a routine.</p></div>
    </div>
  </div>
</section>
"""

home_body = view_chooser + hero(
    "Gainesville's most-loved gym — 45 years strong",
    ["Walk in nervous.", 'Walk out a <span class="serif">regular</span>.'],
    "Starting is the hardest part — so we made it the easiest. From your very first visit, a real coach walks the floor with you, builds your plan, and shows you the ropes. No guesswork. No intimidation. Just results.",
    video=f"assets/video/ghf-walkthrough.mp4",
    poster=f"{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg",
    actions=[
        ("Claim Your Free Day Pass", "contact.html#pricing", True, "only-guest"),
        ("See What's Inside", "amenities.html", False, "only-guest"),
        ("View Class Schedule", "group-fitness.html", True, "only-member"),
        ("Bring a Friend Free", "bring-a-guest.html", False, "only-member"),
    ],
    meta=["Free coaching on every visit", "Open 24/7 at GHF Main", "900+ classes included"],
) + member_strip + marquee(["Strength", "Cardio", "Hot Yoga", "Pilates", "Aquatics", "Recovery", "Group Fitness", "Personal Training"]) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow"><span class="num">01</span> The reason members stay</p>
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
        <p class="eyebrow"><span class="num">02</span> Find what you'll love</p>
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
        <p class="eyebrow"><span class="num">05</span> Recover like you mean it</p>
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
        <p class="eyebrow"><span class="num">06</span> When you're ready for more</p>
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
    secondary=("Join Online Today", "join.html"),
)

# ============================================================ WHY GHF
why_body = hero(
    "Why GHF",
    ["The gym you'll", 'actually <span class="serif">stick with</span>'],
    "Anyone can sell you a membership. GHF is engineered so you'll use yours — more coaching, more variety, more recovery, and more reasons to keep showing up than any gym in Gainesville.",
    img=f"{IMG}/Tioga_Carrie_Grotto_Arm_Cross_Facility_2022.jpg",
    crumb="Why GHF",
    actions=[("Free All-Access Pass", "contact.html#pricing", True)],
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
        <p class="eyebrow"><span class="num">01</span> 45 years of helping beginners</p>
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
    actions=[("Try Our Amenities for Free", "contact.html#pricing", True)],
    page=True,
) + f"""
<section class="section section--tight">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow"><span class="num">01</span> A premium fitness experience</p>
        <h2 class="h-display reveal">Beyond the <span class="serif">basics</span></h2>
      </div>
      <div class="intro-grid__right">
        <p class="lede reveal">Your membership isn't a key card — it's an all-access pass. Train, take a class, drop the kids at Kid's Club, shoot hoops, then end in the sauna with a smoothie on the way out.</p>
        <p class="body-copy reveal">Add it up elsewhere and you'd need a gym, a yoga studio, a spa, a pool membership and a babysitter. Here it's one roof, one price, three locations — with a staffed Kid's Club while you train, 24/7 access at Main, indoor courts, an outdoor fitness pavilion, and a full recovery suite of sauna, steam, hot tub, cold plunge and warm therapy pools.</p>
      </div>
    </div>
  </div>
</section>
""" + marquee(["24/7 Access", "Free Babysitting", "Indoor Pools", "Outdoor Fitness", "Basketball", "J-Bar Smoothies", "Member Savings"]) + split(
    "GHF Main — Open 24/7", "02",
    'The flagship that never <span class="serif">sleeps</span>',
    ["GHF's Main Center makes it easy to get fit, strong and lean, with 24-hour access, pool and spa studio, free babysitting, expansive cardio selections, state-of-the-art strength training equipment, the largest free weight area, access to all three facilities, and more."],
    f"{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg",
    "Open free weight space with benches, dumbbells, and barbells at Gainesville's largest gym",
    cta=("Explore GHF Main", "locations.html"), tag="Main Center",
) + split(
    "GHF Women", "03",
    'The only gym in Gainesville just for <span class="serif">women</span>',
    ["We believe nothing is more essential than women supporting and empowering one another. Experience and enjoy the most advanced fitness center for women in Gainesville with unique fitness classes, sauna, steam, and hot tub, free babysitting, and lots of cardio and weight equipment to lead your healthiest, happiest life and make your wellness goals come true."],
    f"{IMG}/GHF_GHF_Women_Womens_Center_SWEAT_2023_1.jpg",
    "Group fitness instructor teaching HIIT for women at the Women's Center",
    rev=True, cta=("Explore GHF For Women", "locations.html"), tag="Women's Center",
) + split(
    "GHF Tioga", "04",
    'Your family-friendly <span class="serif">gym</span>',
    ["From the moment you walk through the door, you will encounter friendly GHF Tioga Center staff, dedicated to making your health club experience remarkable. They will guide you to the right space whether you want to take a group fitness class, walk on the treadmill, or sweat it out on our outdoor fitness turf, there is always someone happy to show you how.",
     "Bring the kids to the Kid's Club for complimentary babysitting or to CrossFit for Kids — there's a place for everyone in the family!"],
    f"{IMG}/GHF_CrossFit_Kids_Exercise_CrossFit_for_Kids_Tioga_2026.jpg",
    "Kids CrossFit class bear crawl exercise at GHF Tioga",
    cta=("Explore GHF Tioga", "locations.html"), tag="Tioga Center",
) + split(
    "Echo — Outdoor Fitness Pavilion", "05",
    'The largest open-air fitness <span class="serif">destination</span>',
    ["The largest open-air fitness destination will give you a line of new ways to move, lift, train and sweat. Located at GHF's Main campus, Echo is a multi-purpose location that offers fitness classes, functional training equipment, and community events.",
     "Echo offers specialty workshops, GroupFit classes and lifestyle events. We have open gym times for members to use the functional training equipment like tires, sleds, ropes, TRX, rowers and ski ergs, and more. These classes are included in your membership."],
    f"{IMG}/Echo_GroupFit_Outdoor_Classes_Fun_Classes_2021.jpg",
    "Fitness classes in an outdoor gym setting at Echo",
    rev=True, cta=("Try An Outdoor Workout", "group-fitness.html"), tag="Echo",
) + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="split">
      <div class="split__media reveal-img"><img src="{IMG}/sports-activities-pool-wide-700x467.jpg" alt="Indoor lap pool at GHF" loading="lazy"><span class="tag">Aquix by GHF</span></div>
      <div class="split__body">
        <p class="eyebrow"><span class="num">06</span> Aquix by GHF — Indoor Pool &amp; Spa</p>
        <h2 class="h-display" style="font-size:clamp(30px,3.8vw,58px)">Dive into a world of <span class="serif">wellness</span></h2>
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
        <div class="split__cta"><a class="inline-link" href="pool.html">Dive Into Aquix →</a></div>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow"><span class="num">07</span> And so much more</p>
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
      <div class="card">
        <div class="card__media"><img src="{IMG}/GHF_Basketball_5.jpg" alt="Regulation-size indoor basketball court at GHF" loading="lazy">
        <div class="card__label"><h3>Indoor Basketball</h3></div></div>
        <div class="card__below"><p>Regulation-size indoor basketball court with six hoops and hardwood flooring. Full-court play six days a week, half-court play every day, and volleyball twice a week (Wednesdays 6–11p &amp; Sundays 5–10p).</p></div>
      </div>
      <div class="card">
        <div class="card__media"><img src="{IMG}/smoothie_girls_web.png" alt="Real fruit smoothies at J Bar" loading="lazy">
        <div class="card__label"><h3>J-Bar Smoothies</h3></div></div>
        <div class="card__below"><p>Real fruit smoothies, made to order with superior fresh ingredients — the perfect fuel for your workout or recovery.</p></div>
      </div>
      <div class="card">
        <div class="card__media"><img src="{IMG}/cropped_sauna.jpg" alt="Salt room sauna at GHF" loading="lazy">
        <div class="card__label"><h3>Sauna, Steam &amp; Spa</h3></div></div>
        <div class="card__below"><p>Relax and recover in our sauna, steam room, hot tub — or experience our cold plunge and warm therapy pools.</p></div>
      </div>
      <div class="card">
        <div class="card__media"><img src="{IMG}/Family_Membership_Plans.jpg" alt="Member savings program" loading="lazy">
        <div class="card__label"><h3>Member Savings</h3></div></div>
        <div class="card__below"><p>The Member Savings Program offers GHF members discounts at many local businesses — to save the cost of your dues. Simply show your GHF membership card and start saving.</p></div>
      </div>
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
    actions=[("Try a Free Class", "#pass", True), ("Most Popular Classes", "#popular", False)],
    meta=["900+ classes / month", "Included in membership", "All levels welcome"],
    page=True,
) + marquee(["Zumba", "Body Pump", "SkyCycle", "Yoga", "HIIT", "Pilates Mat", "Tai Chi", "Aqua", "PiYo", "Body Combat"]) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow"><span class="num">01</span> A few examples of the classes we offer</p>
        <h2 class="h-display reveal">Something for <span class="serif">everyone</span></h2>
        <p class="body-copy reveal" style="margin-top:26px">From beginner to advanced — and classes are included in your membership. Come as often as you want. We're here to help you reach your potential.</p>
      </div>
      <div class="intro-grid__right reveal">
        <ul class="checklist">
          <li>Aqua Strength and Balance</li>
          <li>Les Mills classes (Body Pump, Flow, Combat, Core)</li>
          <li>Circuit Training/HIIT</li>
          <li>Pilates Mat</li>
          <li>PiYo</li>
          <li>SkyCycle Indoor Cycling</li>
          <li>Tai Chi</li>
          <li>Yoga</li>
          <li>Yoga For Pregnancy (fee-based)</li>
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
        <p class="eyebrow"><span class="num">02</span> Unsure where to start?</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Our most <span class="serif">popular</span> classes</h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">We recommend trying all kinds of classes to find what best suits you, your style and your vibe. Most classes are offered at a variety of times and days with different instructors.</p>
    </div>
    <div class="rows reveal">
      <div class="row-item"><span class="row-item__idx">01</span><span class="row-item__title">Zumba</span><span class="row-item__desc">Dance-party cardio that never feels like a workout.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">02</span><span class="row-item__title">Body Combat</span><span class="row-item__desc">Strike, punch and kick your way to total-body fitness.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">03</span><span class="row-item__title">Body Pump</span><span class="row-item__desc">The original barbell class — tone and condition every major muscle group.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">04</span><span class="row-item__title">Cycle</span><span class="row-item__desc">Indoor cycling classes every day of the week in our Sky Cycle studio.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">05</span><span class="row-item__title">Aqua HIIT &amp; HIIT</span><span class="row-item__desc">High-intensity intervals — in and out of the water.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">06</span><span class="row-item__title">S.W.E.A.T.</span><span class="row-item__desc">Exactly what it sounds like. Bring a towel.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">07</span><span class="row-item__title">Yoga or Stretch</span><span class="row-item__desc">Find your zen, restore your range of motion.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">08</span><span class="row-item__title">Pilates Mat</span><span class="row-item__desc">Core strength and control — no machines required.</span><span class="row-item__arrow">→</span></div>
    </div>
  </div>
</section>
""" + split(
    "Classes for every body", "03",
    'Beginners and seniors <span class="serif">welcome</span>',
    ["There is something for everyone from beginner to advanced and classes are included in your membership. You may also select from indoor cycling classes every day of the week in our Sky Cycle studio or take classes designed just for seniors.",
     "Enjoy more than 700 classes per month including Zumba, Pilates mat, yoga, sports conditioning, H.I.I.T, Les Mills programs, aqua, and more."],
    f"{IMG}/Strength_GroupFit_Seniors_GHF_Tioga_2023_1.jpg",
    "Senior GHF members in a strength group fitness class",
    cta=("Classes for Seniors", "group-fitness.html"), tag="All Levels",
) + form_section(
    "pass", "04", "Request your free fitness class pass",
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
        <p class="eyebrow"><span class="num">01</span> One-on-one personal training</p>
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
        <p class="eyebrow"><span class="num">02</span> Personal training that fits your life</p>
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
        <p class="eyebrow"><span class="num">03</span> Our trainers</p>
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

<section class="section">
  <div class="wrap" style="padding-left:0;padding-right:0">
    <p class="eyebrow wrap" style="margin-bottom:clamp(30px,4vw,60px)"><span class="num">04</span> Real members. Real results.</p>
    <div class="t-slider">
      <div class="t-slider__track">{slides}</div>
      <div class="t-slider__nav">
        <button data-dir="prev" aria-label="Previous testimonial">←</button>
        <button data-dir="next" aria-label="Next testimonial">→</button>
      </div>
    </div>
  </div>
</section>
""" + form_section(
    "assessment", "05", "Free fitness assessment &amp; training session",
    'Your first session is on <span class="serif">us</span>',
    "You will be matched with a certified personal trainer to assess your abilities, determine your action plan and guide your complimentary training session. Your assessment features the InBody 570 Body Composition Analyzer — a detailed snapshot of your body's makeup: body fat, lean muscle, metabolic rate, total body water, and visceral fat — helping you make informed decisions about your fitness and wellness journey.",
    "Schedule Your Assessment",
) + cta_band(
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
        <p class="eyebrow"><span class="num">01</span> The equipment</p>
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
        <p class="eyebrow"><span class="num">02</span> Free weight &amp; functional training studio</p>
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
        <p class="eyebrow"><span class="num">06</span> Benefits of strength training</p>
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
    cta=("Check out the GroupFit Class schedule", "group-fitness.html"), tag="SkyCycle",
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
        <p class="eyebrow"><span class="num">01</span> Take a close look at what awaits you</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Seven ways to <span class="serif">soak it in</span></h2>
      </div>
    </div>
    <div class="rows reveal">
      <div class="row-item"><span class="row-item__idx">01</span><span class="row-item__title">75-Foot Indoor Lap Pool</span><span class="row-item__desc">Dive into a world-class swimming experience. Whether you're a seasoned swimmer or just starting out, our pool provides the perfect environment to improve your technique, build endurance, and achieve your aquatic fitness goals.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">02</span><span class="row-item__title">Himalayan Salt Wall Sauna</span><span class="row-item__desc">Indulge in the soothing warmth of dry heat that can help alleviate chronic pain, reduce joint stiffness, and strengthen your immune system. Step inside and let the natural properties of Himalayan salt envelop you in relaxation.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">03</span><span class="row-item__title">Cleansing Steam Room</span><span class="row-item__desc">Let the warm steam open your pores, clear your airways, and melt the day away.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">04</span><span class="row-item__title">Arctic Cold Pool</span><span class="row-item__desc">Awaken your senses and elevate your energy with a plunge into our invigorating cold pool. Cold plunging is known to provide an instant pick-me-up, increase your baseline dopamine levels, aid in muscle recovery, support your immune system, and provide relief from pain.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">05</span><span class="row-item__title">Warm Thermal Pool</span><span class="row-item__desc">Gentle warmth for joint-friendly movement and deep relaxation.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">06</span><span class="row-item__title">Hot Whirlpool</span><span class="row-item__desc">Melt away the stresses of the day. The soothing warmth and massaging action offer a sanctuary for physical, emotional, and mental relaxation — easing tension, promoting muscle relaxation, relieving pain, and improving sleep.</span><span class="row-item__arrow">→</span></div>
      <div class="row-item"><span class="row-item__idx">07</span><span class="row-item__title">Aqua Classes &amp; Swimming</span><span class="row-item__desc">The buoyancy of water reduces joint impact, making it an ideal low-impact exercise for all ages and abilities — improve flexibility, build cardiovascular endurance, strengthen your core, or simply enjoy the supportive community.</span><span class="row-item__arrow">→</span></div>
    </div>
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
        <p class="eyebrow"><span class="num">02</span> Aqua group classes</p>
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
        <div class="split__cta"><a class="inline-link" href="group-fitness.html">See Our Complete Class Schedule →</a></div>
      </div>
    </div>
  </div>
</section>
""" + form_section(
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
        <p class="eyebrow"><span class="num">01</span> Unlimited potential</p>
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
    <p class="eyebrow"><span class="num">02</span> Our three signature temperatures</p>
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
        <p class="eyebrow"><span class="num">03</span> Why hot yoga?</p>
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

<section class="section section--light">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow"><span class="num">04</span> Before you arrive</p>
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
        <p class="eyebrow"><span class="num">01</span> The best Pilates classes in Gainesville, FL</p>
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
        <p class="eyebrow"><span class="num">02</span> Pilates class descriptions</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Find your <span class="serif">class</span></h2>
      </div>
      <p class="body-copy reveal" style="max-width:38ch">Whether you're a beginner or advanced practitioner, you'll find a class that meets your needs.</p>
    </div>
    {accordion(pilates_classes)}
  </div>
</section>
""" + form_section(
    "pass", "03", "Try Pilates — first session free!",
    'Experience the Pilates <span class="serif">difference</span>',
    "Try the Pilates Reformer under the direction of our trained Pilates instructors. They will teach you how to use the reformer, the best technique, and ways to adjust the workout to your own level. Pilates studios are located at GHF Main and GHF Tioga. Complete this form and we will be in touch to schedule your first session.",
    "Book My Free Session",
) + cta_band(
    'Love the way your body <span class="serif">feels</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/GHF_Pilates_Pilates_at_GHF_Pilates_GHF_Main_Gyms_with_Pilates_Pilates_Studio_2025-3.jpg",
)

# ============================================================ TRIBE
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
        <p class="eyebrow"><span class="num">01</span> TRIBE program descriptions</p>
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
""" + form_section(
    "pass", "06", "Realize your greatest strength — train with a team",
    'Get a free sesh for you <span class="serif">&amp; a friend</span>',
    "TRIBE Team Training™ gives you a free session to see what it's all about. Pick from LIFE, CORE, PUNCH or FitSTRONG. Complete the form and we will contact you to schedule your free session. You are a click away from better results!",
    "Claim My Free Session", light=False,
) + cta_band(
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
    actions=[("Free Guest Pass", "contact.html#pricing", True)],
    meta=["The holistic approach", "Body, mind, and spirit"],
    page=True,
) + f"""
<section class="section section--tight">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow"><span class="num">01</span> The holistic recovery approach</p>
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
    rev=True, tag="Chill by GHF",
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
    rev=True, cta=("See class schedule", "group-fitness.html"), tag="GroupFit",
) + f"""
<section class="section section--light">
  <div class="wrap">
    <div class="card-grid card-grid--2" data-stagger>
      <div class="card">
        <div class="card__media card__media--wide"><img src="{IMG}/smoothie_girls_web.png" alt="Smoothie bar at GHF" loading="lazy">
        <div class="card__label"><h3>J-Bar Smoothie Cafe</h3></div></div>
        <div class="card__below"><p>The J-Bar Smoothie Cafe menu is filled with healthy snacks, food and smoothies that make for the perfect fuel for your workout or enhance your recovery. Smoothies are made to order with superior fresh ingredients, including all real fruit. Enhancements such as whey protein and branched chain amino acids are available.</p></div>
      </div>
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
        <p class="eyebrow"><span class="num">01</span> Included in every membership</p>
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
        <p class="eyebrow"><span class="num">02</span> Kids Club hours</p>
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
    actions=[("Try GHF For Free", "contact.html#pricing", True)],
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
    actions=[("Get Your Free All-Access Pass", "contact.html#pricing", True)],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="loc">
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg" alt="Free weight area at GHF Main" loading="lazy"></div>
        <div>
          <span class="loc-badge">Open 24/7</span>
          <h3>Main Center</h3>
          <a class="phone" href="tel:3523774955">(352) 377-4955</a>
          <div class="loc-hours">
            <div><dt>Every day</dt><dd>Open 24 hours</dd></div>
          </div>
          <address>4820 W Newberry Road, Gainesville, FL 32607<br>General Manager — Adrian Antigua</address>
          <div class="hero__actions" style="opacity:1;transform:none;margin-top:26px">
            <a class="btn btn--sm" href="contact.html#pricing">Access Membership Pricing <span class="arr">→</span></a>
          </div>
        </div>
      </div>
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/GHF_GHF_Women_Womens_Center_Body_Pump_2023_1.jpg" alt="Body Pump class at GHF Women" loading="lazy"></div>
        <div>
          <span class="loc-badge">Women Only</span>
          <h3>GHF Women</h3>
          <a class="phone" href="tel:3523744634">(352) 374-4634</a>
          <div class="loc-hours">
            <div><dt>Mon–Thurs</dt><dd>5am–9pm</dd></div>
            <div><dt>Friday</dt><dd>5am–8pm</dd></div>
            <div><dt>Saturday</dt><dd>8am–6pm</dd></div>
            <div><dt>Sunday</dt><dd>Closed</dd></div>
          </div>
          <address>2441 NW 43rd Street, Gainesville, FL 32606<br>Manager — Jordan Heitzler</address>
          <div class="hero__actions" style="opacity:1;transform:none;margin-top:26px">
            <a class="btn btn--sm" href="contact.html#pricing">Access Membership Pricing <span class="arr">→</span></a>
          </div>
        </div>
      </div>
      <div class="loc-item">
        <div class="loc-item__media reveal-img"><img src="{IMG}/GHF_Tioga_Gainesville_Health_Gainesville_Gyms_TIoga_Strength_Gyms_Nearby_2026-2.jpg" alt="Strength training at GHF Tioga" loading="lazy"></div>
        <div>
          <span class="loc-badge">Family Friendly</span>
          <h3>Tioga Center</h3>
          <a class="phone" href="tel:3526922180">(352) 692-2180</a>
          <div class="loc-hours">
            <div><dt>Mon–Thurs</dt><dd>5am–10pm</dd></div>
            <div><dt>Friday</dt><dd>5am–9pm</dd></div>
            <div><dt>Saturday</dt><dd>8am–8pm</dd></div>
            <div><dt>Sunday</dt><dd>10am–5pm</dd></div>
          </div>
          <address>12830 SW 1st Lane, Suite 100, Newberry, FL 32669<br>Manager — Wrenn Klettner</address>
          <div class="hero__actions" style="opacity:1;transform:none;margin-top:26px">
            <a class="btn btn--sm" href="contact.html#pricing">Access Membership Pricing <span class="arr">→</span></a>
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
)

# ============================================================ CONTACT
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
        <p class="eyebrow"><span class="num">01</span> Request gym pricing</p>
        <h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">Get pricing for Gainesville's best <span class="serif">gym</span></h2>
        <p class="lede reveal" style="margin-top:28px">Complete the form and we will set up a convenient time to present your options. We will contact you via phone, email, or text. One gym membership. Three locations.</p>
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
        <form class="form-grid" data-demo>
          <div class="field"><input type="text" name="first" id="p-first" placeholder=" " required><label for="p-first">First name</label></div>
          <div class="field"><input type="text" name="last" id="p-last" placeholder=" " required><label for="p-last">Last name</label></div>
          <div class="field"><input type="email" name="email" id="p-email" placeholder=" " required><label for="p-email">Email address</label></div>
          <div class="field"><input type="tel" name="phone" id="p-phone" placeholder=" " required><label for="p-phone">Phone</label></div>
          <div class="field field--full">
            <select name="location" id="p-loc" aria-label="Preferred location">
              <option value="">&nbsp;</option>
              <option>GHF Main</option>
              <option>GHF Women</option>
              <option>GHF Tioga</option>
            </select>
            <label for="p-loc">Preferred location</label>
          </div>
          <div class="field field--full"><textarea name="msg" id="p-msg" rows="3" placeholder=" "></textarea><label for="p-msg">What are your fitness goals?</label></div>
          <button class="btn btn--dark field--full" type="submit" style="justify-content:center">Request Pricing <span class="arr">→</span></button>
        </form>
        <p class="form-note">Ready to join GHF? We will contact you via phone, email, or text.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow"><span class="num">02</span> Directory of staff</p>
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
    'Be part of Gainesville\'s largest, state-of-the-art fitness community, where your membership connects you to expert guidance, innovative programs, and top-tier amenities for both physical and mental well-being. <em>Must be 18 years or older to join without parent or guardian. Not quite ready to join? <a href="contact.html#pricing" style="color:var(--accent-soft)">Try GHF with a free gym pass</a>.</em>',
    img=f"{IMG}/join-today-bg.jpg",
    crumb="Join Online",
    actions=[("Start My Membership", "#wizard", True), ("Or Call (352) 377-4955", "tel:3523774955", False)],
    meta=["$29.99 + tax · dues every other Wednesday", "24 month · 12 month · month-to-month", "One membership, 3 locations"],
    page=True,
) + f"""
<section class="join" id="wizard">
  <div class="wrap">
    <div class="join__grid">
      <div class="join__main">
        <div class="join__progress">
          <div class="join__progress-bar"><i></i></div>
          <ol class="join__steps-nav">
            <li class="is-active"><span class="n">01</span><span class="lbl">Home Club</span></li>
            <li><span class="n">02</span><span class="lbl">Your Plan</span></li>
            <li><span class="n">03</span><span class="lbl">Your Details</span></li>
            <li><span class="n">04</span><span class="lbl">Recurring Dues</span></li>
            <li><span class="n">05</span><span class="lbl">Due Today</span></li>
          </ol>
        </div>

        <div class="join__steps">
          <div class="join-step is-active" data-step="1">
            <h2 class="join-step__title">Choose your <span class="serif">home club</span></h2>
            <p class="join-step__hint">One membership, three locations — every plan includes access to all three. Pick the club where you'll check in most.</p>
            <div class="choice-grid">
              <button class="choice" type="button" data-name="GHF Main" data-img="{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg">
                <span class="choice__chip">Open 24/7</span><span class="choice__check">✓</span>
                <div class="choice__img"><img src="{IMG}/Free_Weights_Gainesville_Health_and_Fiitness_2021_1_(1).jpg" alt="Free weight area at GHF Main" loading="lazy"></div>
                <h3>GHF Main</h3>
                <p class="meta">4820 W Newberry Road, Gainesville</p>
              </button>
              <button class="choice" type="button" data-name="GHF Women" data-img="{IMG}/GHF_GHF_Women_Womens_Center_Body_Pump_2023_1.jpg">
                <span class="choice__chip">Women Only</span><span class="choice__check">✓</span>
                <div class="choice__img"><img src="{IMG}/GHF_GHF_Women_Womens_Center_Body_Pump_2023_1.jpg" alt="Body Pump class at GHF Women" loading="lazy"></div>
                <h3>GHF Women</h3>
                <p class="meta">2441 NW 43rd Street, Gainesville</p>
              </button>
              <button class="choice" type="button" data-name="GHF Tioga" data-img="{IMG}/GHF_Tioga_Gainesville_Health_Gainesville_Gyms_TIoga_Strength_Gyms_Nearby_2026-2.jpg">
                <span class="choice__chip">Family Friendly</span><span class="choice__check">✓</span>
                <div class="choice__img"><img src="{IMG}/GHF_Tioga_Gainesville_Health_Gainesville_Gyms_TIoga_Strength_Gyms_Nearby_2026-2.jpg" alt="Strength training at GHF Tioga" loading="lazy"></div>
                <h3>GHF Tioga</h3>
                <p class="meta">12830 SW 1st Lane, Newberry</p>
              </button>
            </div>
          </div>

          <div class="join-step" data-step="2">
            <h2 class="join-step__title">Pick your <span class="serif">plan</span></h2>
            <p class="join-step__hint">Choose from a 24 month, 12 month, or month-to-month agreement — all $29.99 + tax with dues every other Wednesday, and no maintenance fee. Special pricing on family memberships is available for spouses and children 13–21 years of age.</p>
            <div class="seg" role="group" aria-label="Membership type">
              <button type="button" class="is-on" data-type="Individual">Individual</button>
              <button type="button" data-type="Family">Family</button>
            </div>
            <div class="choice-grid">
              <button class="choice choice--plan" type="button" data-name="24 Month Agreement" data-plan="24mo" data-fee="$49.00"
                data-note="After the initial 24 months, dues drop to $20.99 + tax every other Wednesday.">
                <span class="choice__chip">Best Value</span><span class="choice__check">✓</span>
                <h3>24 Month</h3>
                <div class="price">$29.99<small> + tax · every other Wednesday</small></div>
                <p class="meta">After initial 24 months, dues drop to $20.99 + tax every other Wednesday. Starting fee $49.00. No maintenance fee.</p>
              </button>
              <button class="choice choice--plan" type="button" data-name="12 Month Agreement" data-plan="12mo" data-fee="$49.00"
                data-note="After the initial 12 months, dues remain at $29.99 + tax and renew month-to-month.">
                <span class="choice__check">✓</span>
                <h3>12 Month</h3>
                <div class="price">$29.99<small> + tax · every other Wednesday</small></div>
                <p class="meta">After initial 12 months, remains at $29.99 + tax and renews month-to-month. Starting fee $49.00. No maintenance fee.</p>
              </button>
              <button class="choice choice--plan" type="button" data-name="Month To Month Agreement" data-plan="m2m" data-fee="$149.00 + tax"
                data-note="Cancel membership with 30 day notice.">
                <span class="choice__check">✓</span>
                <h3>Month To Month</h3>
                <div class="price">$29.99<small> + tax · every other Wednesday</small></div>
                <p class="meta">Cancel membership with 30 day notice. Starting fee $149.00 + tax. No maintenance fee.</p>
              </button>
            </div>
          </div>

          <div class="join-step" data-step="3">
            <h2 class="join-step__title">Tell us about <span class="serif">you</span></h2>
            <p class="join-step__hint">Must be 18 years or older to join without parent or guardian.</p>
            <div class="form-grid">
              <div class="field"><input type="text" name="first" id="j-first" placeholder=" " required><label for="j-first">First name</label></div>
              <div class="field"><input type="text" name="last" id="j-last" placeholder=" " required><label for="j-last">Last name</label></div>
              <div class="field"><input type="email" name="email" id="j-email" placeholder=" " required><label for="j-email">Email address</label></div>
              <div class="field"><input type="tel" name="phone" id="j-phone" placeholder=" " required><label for="j-phone">Phone</label></div>
            </div>
          </div>

          <div class="join-step" data-step="4">
            <h2 class="join-step__title">Set up your <span class="serif">recurring dues</span></h2>
            <p class="join-step__hint">Nothing is charged now. Choose how we draft your dues every other Wednesday — you'll pay today's total on the next step.</p>
            <div class="choice-grid choice-grid--2" id="payMethods">
              <button class="choice choice--pay is-selected" type="button" data-method="CC">
                <span class="choice__check">✓</span>
                <h3>Credit / Debit Card</h3>
                <p class="meta">Can also cover today's total — nothing to re-enter.</p>
              </button>
              <button class="choice choice--pay" type="button" data-method="ACH">
                <span class="choice__check">✓</span>
                <h3>Bank Draft · ACH</h3>
                <p class="meta">Simplest for ongoing dues. A card is still required for today's total.</p>
              </button>
            </div>
            <input class="ipayfield" data-ipayname="account"   type="hidden" id="ipay-account">
            <input class="ipayfield" data-ipayname="amount"    type="hidden" id="ipay-amount" value="0.00">
            <input class="ipayfield" data-ipayname="firstname" type="hidden" id="ipay-first">
            <input class="ipayfield" data-ipayname="lastname"  type="hidden" id="ipay-last">
            <input class="ipayfield" data-ipayname="email"     type="hidden" id="ipay-email">
            <input class="ipayfield" data-ipayname="phone"     type="hidden" id="ipay-phone">
            <input class="ipayfield" data-ipayname="invoice"   type="hidden" id="ipay-invoice">
            <div class="pay-actions">
              <button class="btn btn--solid" type="button" id="vaultBtn" disabled><span class="lbl">Save Payment Method</span> <span class="arr">→</span></button>
              <span class="pay-status" id="payStatus">Preparing secure window…</span>
            </div>
            <p class="pay-lock">🔒 Entered directly with our payment processor. GHF never sees your card or account number.</p>
            <div id="recOut"></div>
          </div>

          <div class="join-step" data-step="5">
            <h2 class="join-step__title">Total due <span class="serif">today</span></h2>
            <p class="join-step__hint">One charge today. After that, your dues draft automatically every other Wednesday.</p>
            <div id="todayBox"></div>
          </div>
        </div>

        <div class="join__nav-row">
          <button class="btn btn--sm back" type="button">← Back</button>
          <span class="join__count">Step 01 / 05</span>
          <button class="btn btn--solid next" type="button" disabled><span class="lbl">Continue</span> <span class="arr">→</span></button>
        </div>
      </div>

      <aside class="join__summary" aria-label="Your membership summary">
        <div class="join__summary-head">
          <h4>Your Membership</h4>
          <span>GHF</span>
        </div>
        <div class="join__summary-body">
          <div class="sum-row"><dt>Home club</dt><dd class="empty" data-sum="loc">—</dd></div>
          <div class="sum-row"><dt>Membership</dt><dd data-sum="type">Individual</dd></div>
          <div class="sum-row"><dt>Plan</dt><dd class="empty" data-sum="plan">—</dd></div>
          <div class="sum-row"><dt>Starting fee</dt><dd class="empty" data-sum="fee">—</dd></div>
          <div class="sum-row"><dt>Member</dt><dd class="empty" data-sum="name">—</dd></div>
          <div class="sum-row"><dt>Payment method</dt><dd class="empty" data-sum="pay">—</dd></div>
          <div class="sum-cart" data-cart></div>
          <div class="sum-rate">
            <span class="lbl">Due today</span>
            <span class="amt" data-sum="due">$29.99<small> + tax</small></span>
          </div>
          <p class="sum-note" data-sum-recurring>Then $29.99 + tax every other Wednesday.</p>
          <p class="sum-note" data-sum-note>Every membership includes all 900+ monthly classes, hot yoga, pools &amp; spa, Kid's Club, and access to all three locations.</p>
          <span class="sum-badge">No maintenance fee</span>
        </div>
      </aside>
    </div>
  </div>
</section>

<section class="section section--light">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow"><span class="num">01</span> Every GHF membership includes</p>
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

<div class="join-success" role="dialog" aria-modal="true" aria-label="Membership request received">
  <div class="join-success__inner">
    <div class="mark">✓</div>
    <h2 data-success-name>You're going to feel good here.</h2>
    <p data-success-copy>Your membership is active. Your dues will draft automatically every other Wednesday — come meet your new gym. Bring a water bottle.</p>
    <div class="chips" data-success-detail></div>
    <div class="hero__actions">
      <a class="btn btn--solid" href="index.html">Back to Home <span class="arr">→</span></a>
      <a class="btn" href="group-fitness.html">Browse Classes <span class="arr">→</span></a>
    </div>
  </div>
</div>
<script>window.GHF_JOIN_API={JOIN_API_JSON};</script>
<script src="assets/js/join.js?v={V}" defer></script>
""" + cta_band(
    'Or call <span class="serif">(352) 377-4955</span> today',
    "Not quite ready to join? Try GHF with a free gym pass — there is no charge, no obligation and no risk.",
    f"{IMG}/GHF_Careers_Floor_Instructor_Fitness_Jobs_Service.jpg",
    primary=("Try GHF For Free", "contact.html#pricing"),
    secondary=("Request Pricing &amp; More Info", "contact.html#pricing"),
)

# ============================================================ TRAINING OVERVIEW
training_body = hero(
    "GHF Signature Training Programs",
    ["You bring the goal.", "We'll match the <span class=\"serif\">program</span>."],
    "Five coached paths to your strongest self — one-on-one, small team, reformer, negative training, or CrossFit. Different styles, same outcome: you, with a coach, getting somewhere. First sessions are free.",
    img=f"{IMG}/AMPD_45_Metcon_Coached_Training_Strength_Straining_GHF_2023.jpg",
    crumb="Training",
    actions=[("Request Your Free Trial Workout", "#trial", True)],
    meta=["5 signature programs", "Expert coaches", "Free trial session"],
    page=True,
) + split(
    "Personal Training by GHF", "01",
    'Find motivation through customized <span class="serif">training</span>',
    ["One-on-one experts in motivation, accountability and program design to help you re-start your exercise routine, get to the gym regularly, or get in shape with orthopedic or medical limitations. A perfect choice when you need your own exercise program written every week to balance strength and weaknesses for best results.",
     "You will benefit from the combined knowledge, training and practice of 40 specialized, nationally certified Personal Trainers. Let us customize your workout to help you enjoy life to the fullest."],
    f"{IMG}/Personal_Training_Legs_Training_2021_1.jpg",
    "Personal trainer working one on one with a client",
    cta=("Get A Free Assessment", "personal-training.html"), tag="Personal Training",
) + split(
    "Pilates at GHF", "02",
    'Sculpt your body and restore your <span class="serif">mind</span>',
    ["Pilates is a comprehensive movement program that speaks to everyone, helping clients develop proper alignment and stabilization, giving all bodies the gift of freedom in movement. A strong core radiates, bringing strength to the whole self.",
     "Develop a lean, toned body while enjoying an environment of complete focus. Our Certified Pilates Instructors will guide you towards body awareness, flexibility and strength, all while helping you achieve your fitness goals."],
    f"{IMG}/pilatescrop.jpg",
    "Private Pilates at GHF",
    rev=True, cta=("New To Pilates Package", "pilates.html"), tag="Pilates",
) + split(
    "CrossFit at GHF", "03",
    'Find motivation through <span class="serif">community</span>',
    ["Become a part of a fitness community that creates a balance of camaraderie and competition to help you reach your fitness goals that are difficult to achieve on your own. Our coaches are committed to making our members stronger, better, and more self-confident through their fitness journey.",
     "GHF CrossFit is now open to the community. You do not have to be a GHF member to enroll."],
    f"{IMG}/crossfitcrop.jpg",
    "CrossFit at GHF",
    cta=("Explore CrossFit During Free Trial Week", "crossfit.html"), tag="CrossFit",
) + split(
    "X-Force Body at GHF", "04",
    'Shed some serious fat in 6 <span class="serif">weeks</span>',
    ["The only fat loss and muscle gain program in the country delivering results with just two 25-minute workout sessions a week. Experience a combination of negative training, carb-friendly diet plan, super-hydration, and stress reduction practices to shed fat, build muscle, and reshape your body with remarkable self-confidence.",
     "Get ready, your journey to a leaner, stronger, healthier body is beginning now."],
    f"{IMG}/xforce_body_daryl_and_client_with_logo_for_website.jpg",
    "Coach and client on X-Force negative weight machines",
    rev=True, cta=("Schedule A Discovery Session", "xforce.html"), tag="X-Force Body",
) + split(
    "TRIBE Team Training at GHF", "05",
    'Find motivation through <span class="serif">teamwork</span>',
    ["TRIBE Team Training™ offers the best in small team training to deliver the promise \"together everyone will achieve more.\" You will work with a team of up to 10 members and one coach for 8 weeks to motivate and to be motivated for better results.",
     "Experience support, belonging and challenge in a dynamic motivating environment that will respect your individuality to achieve more. Choose between TRIBE Core, TRIBE Life, TRIBE Punch or TRIBE Fit."],
    f"{IMG}/tribe_line.jpg",
    "TRIBE small team training at GHF",
    cta=("Find Your Tribe", "tribe.html"), tag="TRIBE",
) + form_section(
    "trial", "06", "Request your free trial workout",
    'Your complimentary workout is a click <span class="serif">away</span>',
    "The best way to pick the signature program best for you is to try a complimentary session. Experience the style of workout, environment, and trainer to see if it's right for you. Accelerate your results with the experts of Personal Training, X-Force Body, Pilates, CrossFit, and TRIBE Team Training. They will guide you to the results you want to reconnect with life!",
    "Request Free Trial",
) + cta_band(
    'The expertise you need to get <span class="serif">better results</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/Hero_Shot_PT_Page_Debra_and_Adam_Personal_Training_2021.jpg",
)

# ============================================================ CROSSFIT
crossfit_body = hero(
    "CrossFit at GHF Tioga",
    ["The best hour of", 'your <span class="serif">day</span>'],
    "Workouts you'd never finish alone become the thing you can't stop talking about. Coaches scale every WOD to your level, and the community learns your name by week one. Open to everyone — no GHF membership required.",
    img=f"{IMG}/GHF_CrossFit_at_GHF_CrossFit_in_Gainesville_Gainesville_Gyms_Gyms_Workout_Fitness_Cardio_Strength_2025-1.jpg",
    crumb='Training &nbsp;/&nbsp; CrossFit',
    actions=[("Your Free CrossFit Session", "#pass", True), ("What To Expect", "#expect", False)],
    meta=["Open to the community", "Certified coaches", "Free trial week"],
    page=True,
) + f"""
<section class="section" id="expect">
  <div class="wrap">
    <div class="cards-head">
      <div>
        <p class="eyebrow"><span class="num">01</span> Try a free CrossFit class</p>
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
) + form_section(
    "pass", "05", "Your free week of CrossFit",
    'Try CrossFit for <span class="serif">free</span>',
    "Try CrossFit under the direction of certified CrossFit coaches to teach you the mechanics and safety of W.O.D.s. Try CrossFit in our newly renovated, covered space at GHF Tioga. New equipment and classes too. Simply complete the form and we will contact you to set up your free week.",
    "Claim My Free Week",
) + cta_band(
    'Stronger. Fitter. More <span class="serif">confident</span>.',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/GHF_CrossFit_Fitness_Exercise_Outdoors_Group_Fitness_Crossfit_Gainesville_2024-01_1.jpg",
)

# ============================================================ X-FORCE
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
        <p class="eyebrow"><span class="num">01</span> Lose fat for good</p>
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
        <p class="eyebrow"><span class="num">02</span> Here's your fat loss plan</p>
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
        <p class="eyebrow"><span class="num">04</span> Benefits of negative-accentuated training</p>
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
""" + form_section(
    "discovery", "05", "Schedule a free discovery session",
    'Your first step to weight <span class="serif">loss</span>',
    "Find out how you can build the most muscle and burn the most fat in 25 minutes twice per week. Complete the form and we will contact you to set up your session.",
    "Book My Discovery Session",
) + cta_band(
    'Is X-Force Body right for <span class="serif">you?</span>',
    "Try a free X-Force Body session and see if it's right for you.",
    f"{IMG}/XForce_XForce_Body_GHF_Gain_Muscle_Leg_Exercises_2023.jpg",
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
    cta=("View Full Class Schedule", "group-fitness.html"), tag="GroupFit",
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
      <a class="row-item" href="amenities.html">
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
        <p class="eyebrow"><span class="num">01</span> Program description</p>
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
    actions=[("Join GHF Online", "join.html", True), ("Get Pricing", "contact.html#pricing", False)],
    meta=["6 free visits per guest", "Unlimited guests", "2 at a time"],
    page=True,
) + f"""
<section class="section">
  <div class="wrap">
    <div class="intro-grid">
      <div>
        <p class="eyebrow"><span class="num">01</span> Guidelines for guest visits</p>
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
        <p class="eyebrow"><span class="num">01</span> How it works</p>
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
""" + cta_band(
    'Your membership pays you <span class="serif">back</span>',
    "Ready to start a more fit life? Become a GHF member today for as little as $15 per week.",
    f"{IMG}/Family_Membership_Plans.jpg",
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
    ("join.html", "Join Online | Gainesville's Best Gym Memberships | GHF", "Join Gainesville's best gym online — $29.99 + tax, dues every other Wednesday, no maintenance fee. 24 month, 12 month, and month-to-month agreements.", "", join_body),
    ("training.html", "Signature Training Programs | GHF", "Reach a higher level of fitness with Personal Training, Pilates, CrossFit, X-Force Body, and TRIBE Team Training.", "personal-training.html", training_body),
    ("crossfit.html", "CrossFit at GHF Tioga | The Pursuit of Optimal Fitness", "GHF CrossFit is open to the community — free trial week, Olympic lifting, and youth classes.", "", crossfit_body),
    ("xforce.html", "X-Force Body | Lose Body Fat Fast | GHF", "Gainesville's top choice for accelerated fat loss — negative training, 2 × 25-minute workouts weekly.", "", xforce_body_page),
    ("seniors.html", "Senior Fitness Classes | Fitness For Life | GHF", "Club Seniors at GHF — resort-style amenities, senior-friendly classes, and a community of seniors just like you.", "", seniors_body),
    ("sports-activities.html", "Sports Activities at GHF | Basketball, Pool, Cycling & More", "Basketball, volleyball, lap pool, HIIT, indoor cycling and sports performance at Gainesville Health & Fitness.", "", sports_body),
    ("special-needs-fitness.html", "FIT for ALL | Special Needs Fitness at GHF", "Fun Inclusive Training (FIT) for ALL is a free fitness program designed for individuals with special needs.", "", fitforall_body),
    ("bring-a-guest.html", "Bring a Guest | 6 Free Visits | GHF", "The Power Of Friends Guest program — each guest visiting with a member gets 6 free visits.", "", guest_body),
    ("member-savings.html", "Member Savings Program | GHF", "Save the cost of your gym membership dues at over 100 participating local businesses.", "", savings_body),
    ("faq.html", "FAQ | Get The Most Out Of Your Gym Membership | GHF", "Frequently asked questions about Gainesville Health & Fitness memberships, amenities, and getting started.", "", faq_body),
    ("contact.html", "Contact Us & Get Pricing | Gainesville Health & Fitness", "Let's talk fitness memberships in Gainesville — pricing packages and amenities to craft your gym experience.", "", contact_body),
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
  <div class="cards-head"><div><p class="eyebrow"><span class="num">01</span> Latest</p><h2 class="h-display reveal" style="font-size:clamp(34px,4.6vw,72px)">On the <span class="serif">blog</span></h2></div></div>
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
  <div class="cards-head"><div><p class="eyebrow"><span class="num">02</span> Keep reading</p><h2 class="h-display reveal" style="font-size:clamp(30px,3.4vw,52px)">More from <span class="serif">the blog</span></h2></div>
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
