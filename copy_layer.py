"""
Copy layer — makes every piece of text on the built site editable from the CMS.

How it works (runs inside build.py's page writers):

  1. A page is rendered as usual (head + header + body + footer).
  2. Every text node in the page body/head is catalogued into content/copy/<page>.json;
     text shared by all pages (header, menu, footer) is catalogued once into content/copy/_site.json.
     Each entry: {id, where, original, text}. New text keeps text == original.
  3. Editors change "text" in the CMS (Site Text collection). On the next build, any entry whose
     text differs from its original is swapped into the rendered HTML at that exact node.

IDs are derived from the page, the original text and its occurrence index, so they are stable
across builds. If the code's original text changes, that entry gets a new id and the old edit
simply stops applying — the CMS shows the new text ready to edit again.

Pages built from the CMS block editor and blog posts are not catalogued (their content is
already editable there); shared header/footer edits still apply to them.
"""
import os, re, json, hashlib, html as _html

COPY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "copy")
SITE_SCOPE = "_site"

_SKIP = re.compile(r'<(script|style|noscript)\b.*?</\1>|<!--.*?-->', re.S | re.I)
_NODE = re.compile(r'>([^<>]+)<')
_TAG_BEFORE = re.compile(r'<([a-zA-Z][a-zA-Z0-9-]*)\b[^<>]*>\s*$')
_META_DESC = re.compile(r'(<meta\s+name="description"\s+content=")([^"]*)(")', re.I)
_ALNUM = re.compile(r'[A-Za-z0-9]')
_WS = re.compile(r'\s+')

_chrome_overrides = None   # synced once per build


def _norm(raw):
    return _WS.sub(" ", _html.unescape(raw)).strip()


def _extract(fragment, scope, counter, heading_state):
    """Return editable nodes in `fragment` with positions, stable ids and a 'where' label."""
    masked = _SKIP.sub(lambda m: " " * len(m.group(0)), fragment)
    entries = []
    for m in _NODE.finditer(masked):
        raw = m.group(1)
        if not _ALNUM.search(raw):
            continue
        original = _norm(raw)
        if re.fullmatch(r"\d{1,3}", original):      # step numbers / preloader counter — structure, not copy
            continue
        n = counter.get(original, 0); counter[original] = n + 1
        tag_m = _TAG_BEFORE.search(masked[:m.start(1)])
        tag = (tag_m.group(1).lower() if tag_m else "text")
        if tag == "title":
            where = "Browser tab title"
        else:
            where = tag + (" · " + heading_state["h"] if heading_state["h"] else "")
        if tag in ("h1", "h2", "h3"):
            heading_state["h"] = original[:60]
        entries.append({
            "id": hashlib.sha1(f"{scope}|{original}|{n}".encode("utf-8")).hexdigest()[:10],
            "where": where[:90], "original": original, "start": m.start(1), "end": m.end(1), "raw": raw,
            "escape": lambda s: _html.escape(s, quote=False),
        })
    md = _META_DESC.search(fragment)
    if md and _ALNUM.search(md.group(2)):
        original = _norm(md.group(2))
        entries.append({
            "id": hashlib.sha1(f"{scope}|meta|{original}".encode("utf-8")).hexdigest()[:10],
            "where": "Search-engine description", "original": original,
            "start": md.start(2), "end": md.end(2), "raw": md.group(2),
            "escape": lambda s: _html.escape(s, quote=True),
        })
    return entries


def _sync_manifest(scope, entries):
    """Merge freshly extracted entries with the CMS file; return {id: edited text}."""
    path = os.path.join(COPY_DIR, scope + ".json")
    prev = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                prev = {e.get("id"): e for e in json.load(fh).get("items", [])}
        except Exception:
            prev = {}
    seen, items = set(), []
    for e in entries:
        if e["id"] in seen:          # same text twice at the same occurrence can't happen, but be safe
            continue
        seen.add(e["id"])
        p = prev.get(e["id"])
        text = p.get("text") if (p and isinstance(p.get("text"), str) and p["text"].strip()) else e["original"]
        items.append({"id": e["id"], "where": e["where"], "original": e["original"], "text": text})
    data = {"page": scope, "items": items}
    os.makedirs(COPY_DIR, exist_ok=True)
    current = None
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                current = json.load(fh)
        except Exception:
            current = None
    if current != data:   # avoid churn when the CMS wrote the same content with different formatting
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    return {i["id"]: i["text"] for i in items if i["text"] != i["original"]}


def _apply(fragment, entries, overrides):
    if not overrides:
        return fragment
    out, last = [], 0
    for e in sorted(entries, key=lambda x: x["start"]):
        if e["id"] not in overrides:
            continue
        raw = e["raw"]
        lead = raw[:len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        out.append(fragment[last:e["start"]])
        out.append(lead + e["escape"](overrides[e["id"]]) + trail)
        last = e["end"]
    out.append(fragment[last:])
    return "".join(out)


def _chrome(header, footer):
    """Catalogue header + footer text once per build; return (header, footer) with edits applied."""
    global _chrome_overrides
    counter, hs = {}, {"h": ""}
    h_entries = _extract(header, SITE_SCOPE, counter, hs)
    f_entries = _extract(footer, SITE_SCOPE, counter, hs)
    if _chrome_overrides is None:
        _chrome_overrides = _sync_manifest(SITE_SCOPE, h_entries + f_entries)
    return _apply(header, h_entries, _chrome_overrides), _apply(footer, f_entries, _chrome_overrides)


def compose(filename, head_html, header, footer, body, manifest=True):
    """Assemble a page: catalogue its text for the CMS (head + body under one scope, shared
    header/footer under _site) and apply any edits. Returns the final HTML."""
    header, footer = _chrome(header, footer)
    if manifest:
        scope = scope_of(filename)
        counter, hs = {}, {"h": ""}
        head_entries = _extract(head_html, scope, counter, hs)
        body_entries = _extract(body, scope, counter, hs)
        overrides = _sync_manifest(scope, head_entries + body_entries)
        head_html = _apply(head_html, head_entries, overrides)
        body = _apply(body, body_entries, overrides)
    # Invisible scope markers let the visual editor (docs/admin/edit.html) tell shared text from page text.
    return (head_html + "<!--copy:_site-->" + header + "<!--/copy-->" + body
            + "<!--copy:_site-->" + footer + "<!--/copy-->")


def scope_of(filename):
    return re.sub(r"\.html$", "", filename).replace("/", "__")


def publish(out_dir, pages, repo, branch):
    """Copy the catalogues (and a page index) into the built site so the visual editor can load them."""
    import glob, shutil
    dst = os.path.join(out_dir, "admin", "copy")
    os.makedirs(dst, exist_ok=True)
    for f in glob.glob(os.path.join(COPY_DIR, "*.json")):
        shutil.copy(f, dst)
    index = {"repo": repo, "branch": branch, "pages": []}
    for fn, title in pages:
        sc = scope_of(fn)
        if os.path.exists(os.path.join(COPY_DIR, sc + ".json")):
            index["pages"].append({"scope": sc, "file": fn, "title": title})
    index["pages"].sort(key=lambda x: (x["file"] != "index.html", x["title"].lower()))
    with open(os.path.join(dst, "pages.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
