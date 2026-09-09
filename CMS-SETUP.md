# Content Manager (CMS) — Setup & How-To

This site has a built-in **visual content manager** so non-technical staff can write
blog posts, post events, and edit classes & staff — no code, no markdown knowledge needed.

- **Editor:** [Sveltia CMS](https://github.com/sveltia/sveltia-cms) (free, open-source)
- **Where staff go:** `https://<your-site>/admin/`
- **What they can edit:** Blog Posts · Events & Happenings · Group Classes · Staff & Pros
- **How publishing works:** Saving in `/admin` commits to this repo → a GitHub Action
  rebuilds the site and redeploys it live in ~1 minute. No servers to babysit, $0 hosting.

## Content lives in the repo
```
content/
  blog/     *.md   — blog posts (title, date, author, cover image, body)
  events/   *.md   — happenings (title, date, club, thumbnail, link, blurb)
  classes/  *.md   — group classes (name, category, club, description)
  staff/    *.md   — bios (name, role, club, specialties, photo, bio)
```
`build.py` reads these to generate `/blog`, the Happenings page, and home-page cards.
Uploaded images land in `docs/assets/img/` automatically.

## One-time setup: enable staff login (≈5 minutes, repo owner)
The CMS edits via GitHub, so it needs a GitHub OAuth app to let editors sign in.

1. **Create an OAuth app:** GitHub → Settings → Developer settings → **OAuth Apps** → *New*.
   - Application name: `GHF CMS`
   - Homepage URL: your site URL
   - Authorization callback URL: `https://YOUR-AUTH-WORKER/callback` (from step 2)
   - Save the **Client ID** and generate a **Client Secret**.
2. **Deploy the free auth worker** (Cloudflare Workers, free tier):
   `https://github.com/sveltia/sveltia-cms-auth` — paste the Client ID/Secret as
   the worker's `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` env vars.
3. **Point the CMS at it:** in `docs/admin/config.yml`, under `backend:` add
   `base_url: https://YOUR-AUTH-WORKER`.
4. **Invite editors:** add each staff member as a repo collaborator (Settings → Collaborators).
   They log in at `/admin` with their GitHub account — that's the only account they need.

> Prefer email/password logins with zero GitHub accounts? Host the same site on
> **Netlify** (also free) and use Netlify Identity + Git Gateway — the `/admin` and
> `content/` work unchanged; only the `backend:` block in config.yml changes.

## Local preview of the editor (optional, for developers)
```bash
npx @sveltia/cms-proxy-server     # in one terminal
python3 serve.py                  # in another → open http://localhost:4175/admin/
```
(Set `local_backend: true` in config.yml while testing locally.)

## Daily use (staff)
1. Go to `/admin`, sign in.
2. Pick a collection (e.g. **Blog Posts**) → **New**.
3. Fill the friendly fields, drag in an image, write the post.
4. **Publish.** The site updates itself within a minute.

## Pages — build & edit full pages (the page builder)
The **Pages** collection lets staff edit existing pages and **create brand-new ones**
using the site's design blocks — no code. Each page is assembled from **sections**:

- **Hero** (top banner) · **Image + Text** · **Heading + Checklist** · **Stats band**
- **Call-to-action band** · **FAQ / Accordion** · **Rich text** · **Lead form** · **Scrolling word strip**

How to create a page:
1. `/admin` → **Pages** → **New Page**.
2. Set the **title**, a **URL slug** (e.g. `corporate-wellness` → `/corporate-wellness.html`),
   and an **SEO description**.
3. **Show in site menu** on/off, plus an optional **menu label** and **order**.
4. Add **sections** and fill in the fields. Reorder by dragging.
5. Save → the site rebuilds and the page goes live (~1 min); it appears in the menu if toggled on.

Tips:
- Wrap a word in `*asterisks*` inside a headline to give it the **blue serif accent**
  (e.g. `A healthier team, the *GHF* way`).
- Every page automatically gets the site header, footer, navigation and AI concierge.
- Existing pages migrated into the builder (e.g. **Bring a Guest**, **Corporate Wellness**)
  live in `content/pages/*.json`; the rest are still generated from `build.py` until migrated.
