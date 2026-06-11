# GHF — Gainesville Health & Fitness Redesign

A first-class, fully responsive redesign of [ghfc.com](https://www.ghfc.com/) — 16 static pages,
original copy and photography preserved, rebuilt with a modern editorial design system
(dark palette, oversized display type, scroll-triggered reveals, parallax media, video hero,
full-screen menu, custom cursor).

## View the site

Open `site/index.html` directly in a browser, or serve it:

```bash
python3 -m http.server 4173 --directory site
# → http://localhost:4173
```

## Pages (16)

index, why-ghf, amenities, group-fitness, personal-training, strength-training, cardio,
pool, hot-yoga, pilates, tribe, recovery, kids-club, weight-loss, locations, contact

## Structure

- `site/` — the deliverable (open this in a browser)
  - `assets/css/main.css` — design system
  - `assets/js/main.js` — preloader, menu, reveals, parallax, counters, sliders, accordions
  - `assets/img/` — 119 photos downloaded from ghfc.com (web-optimized to max 1800px)
  - `assets/video/ghf-walkthrough.mp4` — 32s hero loop cut from the official walkthrough video
- `build.py` — static site generator; edit content here and run `python3 build.py` to regenerate
- `scrape/` — raw pages + extracted copy from the live site (source of truth for content)

## Notes

- Copy is verbatim from the live site; photography and video are the club's own assets.
- Forms are demo-only (no backend); they show a confirmation state on submit.
- Fonts: Anton, Instrument Serif, Inter (Google Fonts — needs internet on first load).
