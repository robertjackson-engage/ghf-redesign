#!/usr/bin/env python3
"""Snapshot the Member Savings directory from the old site.

The listings live behind an ASP.NET PageMethod that ghfc.com's own front-end
calls. It sends no Access-Control-Allow-Origin, so the new page cannot fetch it
from the browser — the directory is baked at build time instead. That makes it a
point-in-time copy: re-run this script to refresh both the JSON and the logos.

    python3 tools/fetch_savings.py

Writes content/member-savings.json and docs/assets/img/savings/*.
"""

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "https://www.ghfc.com/member-savings-program.aspx/PageListing"
IMG_BASE = "https://www.ghfc.com/uploads/images/"
OUT_JSON = os.path.join(ROOT, "content", "member-savings.json")
OUT_IMG = os.path.join(ROOT, "docs", "assets", "img", "savings")
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
MAX_W = 400  # logos render a couple of hundred px wide; the sources run to 1.5MB


def slug(s):
    s = re.sub(r"[''`]", "", (s or "").lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "business"


def clean_site(url):
    """21 records carry the placeholder 'http://' and one is double-prefixed
    ('http://https://b12rxandmore.com/'). Return "" for anything unusable."""
    u = (url or "").strip()
    m = re.match(r"^https?://(https?://.*)$", u)
    if m:
        u = m.group(1)
    if not re.match(r"^https?://[^/\s]+\.[^/\s]", u):
        return ""
    return u


def fetch_listing():
    body = json.dumps({"searchText": "", "categoryID": 0}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8-sig"))["d"]


def fetch_logo(image_name, dest_slug):
    """Download and downscale one logo. Returns the filename, or "" if there
    isn't a real one (5 records point at a blank-logo placeholder)."""
    name = (image_name or "").strip()
    if not name or "blank-logo" in name:
        return ""
    ext = os.path.splitext(name)[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".jpg"
    out_name = dest_slug + ext
    out_path = os.path.join(OUT_IMG, out_name)
    url = IMG_BASE + urllib.parse.quote(name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            if r.status != 200:
                return ""
            data = r.read()
    except Exception as e:  # a dead logo must not kill the whole snapshot
        print("  ! logo failed:", name, e)
        return ""
    if not data:
        return ""
    with open(out_path, "wb") as f:
        f.write(data)
    # --matchTo is what actually does the work on the Photoshop-exported logos:
    # several are CMYK JPEGs, which sips will not re-encode in place (they stay
    # ~600KB at 400px) and which some browsers render with wrong colours.
    # Converting to sRGB fixes both — one went 592KB -> 24KB. PNGs keep their
    # format so logo transparency survives.
    fmt = "png" if ext == ".png" else "jpeg"
    args = ["sips", "--resampleWidth", str(MAX_W), "--matchTo", SRGB, "-s", "format", fmt]
    if fmt == "jpeg":
        args += ["-s", "formatOptions", "70"]
    subprocess.run(args + [out_path], capture_output=True)
    return out_name


def main():
    os.makedirs(OUT_IMG, exist_ok=True)
    raw = fetch_listing()
    print("fetched", len(raw), "businesses")

    seen, out = {}, []
    for b in raw:
        name = (b.get("Name") or "").strip()
        if not name:
            continue
        cat = (b.get("Category") or {}).get("Name") or "Other"
        s = slug(name)
        seen[s] = seen.get(s, 0) + 1
        if seen[s] > 1:
            s = f"{s}-{seen[s]}"
        offers = [
            (p.get("Description") or "").strip()
            for p in (b.get("Promotions") or [])
            if (p.get("Description") or "").strip()
        ]
        out.append({
            "name": name,
            "slug": s,
            "category": cat,
            "offers": offers,
            "phone": (b.get("Phone") or "").strip(),
            "address": (b.get("Address") or "").strip(),
            "website": clean_site(b.get("Website")),
            "logo": fetch_logo(b.get("ImageName"), s),
        })

    out.sort(key=lambda x: (x["category"].lower(), x["name"].lower()))
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    cats = sorted({b["category"] for b in out})
    print("wrote", OUT_JSON)
    print("  businesses:", len(out))
    print("  offers:", sum(len(b["offers"]) for b in out))
    print("  with logo:", sum(1 for b in out if b["logo"]))
    print("  with website:", sum(1 for b in out if b["website"]))
    print("  categories:", len(cats), cats)


if __name__ == "__main__":
    sys.exit(main())
