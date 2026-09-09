# GHF Online Join — IntelliPay integration (MVP)

Cart-style online join for Gainesville Health & Fitness, built on IntelliPay's **Lightbox
Terminal**. Two payment stages, exactly like the club's in-person agreement:

1. **Recurring dues** — the member adds the payment method their bi-weekly dues will draft from
   (card or bank). Lightbox runs in **Store Only** mode: nothing is charged, IntelliPay vaults
   the method and returns a `custid` **token**.
2. **Due today** — one real charge for the start fee + first dues + tax. If the saved method is
   a card, one tap re-uses it (`card_payment` with the `custid`); if it's a bank account, the
   member adds a card for today (we don't take ACH for the up-front payment — enforced server-side).

The token goes to GHF's member-management system in the nightly file (`/api/export`), which runs
the recurring billing. No card or bank number ever touches a GHF server → **PCI SAQ-A**.

```bash
cp .env.example .env            # merchant key + API key (see below)
python3 server.py               # http://localhost:4400   (branding / flow work)
python3 https_server.py         # https://localhost:4443  (full end-to-end incl. captcha)
```

## Things we learned the hard way

| Symptom | Cause / rule |
|---|---|
| `Lightbox Authentication Failed` / `status:-1` | The merchant key is literally **`:AK:<merchant number>`** — the leading colon is part of it. |
| Lightbox never opens after "Save" | Lightbox binds `initialize` to `window.load`. The autoterminal blob must be **server-rendered into `<head>`** (we replace `<!--IPAY_TERMINAL-->`), not injected later. |
| Frame stays blank on `http://127.0.0.1` | The frame rejects IP-literal origins. Always use **`localhost`**. |
| Form renders but reCAPTCHA / final layout never arrives | **Needs HTTPS.** Production has it; locally use `https_server.py` (self-signed — accept it once in Safari/Chrome). |
| Frame blank for ~10 s on first open | Normal cold start of the frame after a page load. Later opens are instant. |
| Bank draft option does nothing in sandbox | Test merchant has `achenable:false`. Ask IntelliPay to enable ACH on the sandbox. |
| Logo doesn't show | The banner must be an **https URL** the frame can fetch — no `data:` URIs, no `http://` (mixed content). |

## Customizing the Lightbox — what IntelliPay actually honors

IntelliPay ships no hosted-fields / token-iframe product; the Lightbox *is* their tokenizing iframe
(their public offerings are Lightbox, Hosted Online Payment Page, Text-to-Pay, batch, and the direct
API which requires SAQ-D). Reading the frame's code, these are the **only** `(field, property)`
pairs it reads — everything else is silently ignored:

| Hook | What it controls |
|---|---|
| `banner.url`, `bannerImage.height` | Logo at the top (replaces the IntelliPay logo) |
| `header.label/color/backgroundcolor` | Title bar (only shown in some layouts) |
| `button.label/color/backgroundcolor` | Primary button |
| `input.backgroundcolor/color/borderradius/borderbottom`, `inputBorder.color`, `inputFont.color` | Fields |
| `leftContainer.backgroundcolor`, `lightbox.borderradius` | Panels / corners |
| `account.label`, `amount.label`, `company.label` | Labels |
| `email.enabled`, `phone.enabled`, `account.enabled`, `confirm.enabled`, `viewExitButton.enabled` | Show/hide |
| `successmessage.label`, `declinemessage.label` | Outcome copy |

Set via `intellipay.setItemUrl/Label/Color/BackgroundColor/BorderRadius/Height`, `enable/disable`
— see `brandLightbox()` in `join.html`. Mobile: the frame has its own mobile layout (`isMobileDevice()`
+ breakpoints at 500/750/768/1050 px) and the host modal is full-viewport; nothing to do on our side.

**Merchant-portal settings, not JS** (change in the IntelliPay admin or ask support):
"Powered by IntelliPay" footer (`display_powered_by`), reCAPTCHA (`require_captcha`), which fields
display/require by default, accepted card brands, the default logo (`verticalMarketImage`).

### Logo hosting
`server.py` hands the frame `window.__ghfLogo`: `IPAY_LOGO_URL` env var if set → on the local https
server, `https://localhost:4443/static/ghf-logo.png` → otherwise the copy on GitHub Pages.
`static/ghf-logo.png` (transparent, brand-blue) is also staged at `docs/assets/img/ghf-logo.png`;
once pushed, Pages serves it and the http dev path picks it up automatically.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/` | Join wizard (autoterminal blob + logo URL rendered into `<head>`) |
| `GET`  | `/api/catalog`, `/api/quote` | Clubs, plans, add-ons; cart math incl. 7% tax |
| `POST` | `/api/member` | Create pending member → `memberId` |
| `POST` | `/api/recurring-method` | Store `custid` + type from Stage 1; says whether it can pay today (`C` only) |
| `POST` | `/api/charge-today` | Stage 2 with the saved card — `card_payment` by `custid`; rejects ACH |
| `POST` | `/api/today-card` | Stage 2 with a separate card (Lightbox, not store-only) |
| `POST` | `/api/postback` | IntelliPay server-to-server confirmation (authoritative) |
| `GET`  | `/api/export?date=YYYY-MM-DD` | Nightly CSV: member, `recurring_token`, `recurring_method`, paid-today |
| `GET`  | `/static/*` | Logo and other assets for the Lightbox |

## Credentials & security
- `.env` is gitignored. Keys are used server-side only (autoterminal + Web API calls).
- **Rotate the API key before production** — the current one passed through chat.
- Two orphaned personal-access tokens ("claude-code GHF", "claude-code (GHF join MVP)") exist in the
  IntelliPay admin from a broken grant flow; revoke them.
- Sandbox: `test.cpteller.com` · Production: `secure.cpteller.com` (`IPAY_HOST`).

## Site integration (docs/join.html)

The GHF website's **Join Online** page is this cart-style module, wrapped in the site's header and
footer (`build.py` → `docs/join.html`; styles scoped under `.jn` in `docs/assets/css/main.css`; logic in
`docs/assets/js/join.js`). The static page talks to this server cross-origin:

- **API base** is baked in at build time: `GHF_JOIN_API=https://join.ghfc.com python3 build.py`
  (default `https://ghf-join-demo.azurewebsites.net`). Pages served from `localhost` automatically use
  `http://localhost:4400`; `join.html?api=…` overrides either (remembered in `localStorage`).
- **CORS**: the server answers preflights and sets `Access-Control-Allow-Origin` —
  `JOIN_ALLOWED_ORIGINS=https://ghfc.com,https://www.ghfc.com` in production (`*` by default for dev).
- **Terminal**: the page fetches `/api/terminal` at runtime, re-creates the blob's inline `<script>`
  tags so they execute, then calls `intellipay.initialize()` itself (window `load` has already fired).
  `/api/terminal` also ships `window.__ghfLogo` for the Lightbox banner.
- The standalone `join.html` served at `/` by this server is kept as the API's own demo page.

Steps on the site: 01 Home Club → 02 Plan → 03 Details (creates the member) → 04 Recurring Dues
(Lightbox Store Only → token) → 05 Due Today (saved card in one tap, or a separate card) → active.
