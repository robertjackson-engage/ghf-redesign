# GHF Website — Member vs. Guest Experience Review
*Audit of the current site (28 pages) · prepared for team review*

---

## Executive summary

The site has a **Guest / Member toggle**, but the two experiences are **~97% identical**. Across all 28 pages, only **8 elements** actually change — and all of them live on the **header** and the **homepage**.

The practical consequence: **a logged-in member is still browsing a sales site.** They see "Claim Your Free Pass," "Free All-Access Pass," "Join Online," and lead-capture forms asking for their name, email, and phone — on pages they visit *because they're already paying members.*

| | Guest | Member |
|---|---|---|
| Pages with any tailored content | 1 of 28 (home) | 1 of 28 (home) |
| Total elements that differ | 4 | 4 |
| "Join / Free Pass" CTAs still shown | ✅ appropriate | ❌ **30 pages' worth** |
| Lead-capture forms still shown | ✅ appropriate | ❌ **18 forms** |

**Recommendation:** treat this as a real member experience, not a toggle. Details in *Recommendations* below.

---

## 1 · How the system works today

**The mechanism** (`main.js` + `main.css`):
- First-time visitors get a full-screen **view chooser**: *"I'm a guest"* vs *"I'm a member."*
- The choice is stored in `localStorage` as `ghf-view` and set as `data-view="guest|member"` on the `<html>` element.
- CSS then does the work — two rules:
  ```css
  html[data-view="guest"] .only-member { display: none !important; }
  html[data-view="member"] .only-guest { display: none !important; }
  ```
- A **Guest / Member toggle** in the header lets people switch any time.
- Skipping the chooser sets `ghf-view-skip` and defaults the visitor to **guest**.

**Assessment:** the plumbing is solid and works correctly. The problem isn't the mechanism — it's that almost nothing is tagged to use it.

---

## 2 · Everything that actually differs (the complete list)

### A. Header — 3 elements
| Element | Guest sees | Member sees |
|---|---|---|
| Secondary button | **Get Pricing** → contact#pricing | *(hidden)* |
| Primary button | **Join Online** → join.html | *(hidden)* |
| Primary button | *(hidden)* | **Class Schedule** → group-fitness.html |

### B. Homepage hero — 4 buttons
| Guest sees | Member sees |
|---|---|
| **Claim Your Free Day Pass** (primary) | **View Class Schedule** (primary) |
| **See What's Inside** (secondary) | **Bring a Friend Free** (secondary) |

### C. Homepage member strip — 1 element *(members only)*
A quick-links bar reading **"Welcome back."** with: Class Schedules · Hot Yoga · Kid's Club Hours · Pool & Spa · Locations & Hours · Member Savings · Bring a Guest.

> ⚠️ **This strip appears on the homepage only.** Navigate anywhere else and the member experience effectively ends.

### D. View chooser (first visit)
| Guest panel | Member panel |
|---|---|
| *"First time here?"* — Tour the club, get pricing, and claim your free all-access pass. | *"Welcome back"* — Class schedules, club hours, Kid's Club, and your member perks. |

**That's the entire list.** Nothing else on the site changes.

---

## 3 · What is IDENTICAL for both (the gap)

| Surface | Count | What members currently see |
|---|---|---|
| **CTA bands** (bottom of nearly every page) | **30** | "Claim Your Free Pass" + "Free All-Access Pass" — an acquisition pitch to an existing member |
| **Lead-capture forms** | **18** | Name / email / phone / preferred location forms, as if they're a prospect |
| **Menu overlay panel** | 1 | *"There is no charge, no obligation and no risk…"* + **Free All-Access Pass** button |
| **Main navigation** | all pages | Identical — no member-oriented items (schedules, hours, perks) |
| **Every interior page** (27 of 28) | 27 | No member framing at all |
| **Footer** | all pages | Identical |
| **Pricing / join pages** | 2 | Fully visible to members |

### Why this matters
1. **It reads as a bug to members.** Being asked to "Join Online" when you've been a member for six years feels like the club doesn't know you.
2. **It wastes the toggle.** Members who self-identify get almost nothing for it — so the feature trains them to ignore it.
3. **It buries member utility.** The things members actually call the front desk about — class times, hours, Kid's Club, pool schedule — are one strip on one page.
4. **It clutters the guest funnel too.** Because nothing is segmented, guest pages carry member-oriented content (Member Savings, Bring a Guest) that dilutes the sales message.

---

## 4 · Side-by-side: what a member's journey looks like now

| Step | Today | Should be |
|---|---|---|
| Lands on home | ✅ Sees "Welcome back" strip + member CTAs | ✅ Good |
| Clicks "Hot Yoga" | ❌ Member strip gone; page ends with "Claim Your Free Pass" | Class times + "Book a spot" |
| Clicks "Kid's Club" | ❌ Ends with a lead form asking for their phone number | Hours + reservation info |
| Clicks "Locations" | ❌ Sales CTA band | Hours, holiday closures, amenities per club |
| Opens the menu | ❌ "Free All-Access Pass" offer | Member links + guest-pass sharing |

---

## 5 · Recommendations (in priority order)

### Priority 1 — Stop the acquisition bleed *(highest impact, lowest effort)*
Make the shared components view-aware so members stop getting sold to. Both are single-function changes in `build.py`:
- **`cta_band()`** → member variant with member CTAs (Class Schedule · Book Recovery · Reserve Kid's Club) instead of Join/Free Pass. **Fixes 30 pages at once.**
- **`form_section()`** → hide or replace lead forms for members. **Fixes 18 forms at once.**
- **Menu overlay** → swap the free-pass panel for a member panel.

*(This is exactly the fix we shipped on the Forma site — one change to the shared component, and every page inherits it.)*

### Priority 2 — Extend the member strip sitewide
Move it from homepage-only to every page, so member utility is always one click away.

### Priority 3 — Make the nav view-aware
Give members a nav weighted to schedules, hours, and perks rather than Why GHF / Amenities (which are sales pages).

### Priority 4 — Build genuine member value
Right now "member view" only *removes* selling. It should *add* something:
- Class schedules & booking
- Club hours, including holiday closures
- Kid's Club hours + reservations
- Member Savings partner list
- Guest-pass sharing (Power of Friends)
- App download / check-in

### Priority 5 — Persistence & entry
- The choice lives in `localStorage`, so it's **per-device and lost when cleared** — a member on a new phone is treated as a prospect.
- Consider a "Members" entry point in the nav, and revisit whether the full-screen chooser on first visit is the right trade for guests (it adds friction to the sales funnel).

---

## 6 · Open questions for the team
1. **How real is "member view" meant to be?** A content filter (current), or the beginning of a true member portal?
2. **Should members ever see pricing/join pages?** Relevant for upgrades, family add-ons, and referrals.
3. **Is there a schedule/booking system** we can link or embed? That's the #1 member need and the biggest gap.
4. **Should the view chooser stay?** It adds a step for guests; an alternative is defaulting to guest with a subtle "I'm a member" switch.
5. **Do we want a real login** eventually (so member view is verified, persistent, and can show personalized data)?

---

## Appendix — technical reference
- **Toggle logic:** `docs/assets/js/main.js` (lines ~10–48)
- **Visibility rules:** `docs/assets/css/main.css` (lines 970–978)
- **Gated markup:** `build.py` — 4 × `only-guest`, 4 × `only-member` (lines 165–167, 607, 657–660)
- **Storage keys:** `ghf-view` (localStorage), `ghf-view-skip` (sessionStorage)
- **Shared components that need gating:** `cta_band()` (30 uses), `form_section()` (18 uses), menu overlay, `member_strip` (1 use)
