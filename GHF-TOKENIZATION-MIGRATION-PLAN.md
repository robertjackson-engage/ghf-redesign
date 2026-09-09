# GHF — Card-on-File Tokenization Migration (IntelliPay)
*Plan for moving GHF's member billing from stored card/bank numbers to IntelliPay tokens · prepared 2026-09-02*

---

## Where we are and where we're going

| | Today | After |
|---|---|---|
| What GHF stores | Full card numbers + bank account/routing numbers in the member system | An IntelliPay **token** (`custid`) + display-only hints (brand, last 4) |
| Nightly SFTP batch | Rows carry raw numbers | Rows carry the token |
| Online join | New — built on Lightbox, already token-native | Same; writes the token into the new TOKEN field |
| Card updates at the desk | Staff key numbers into the member system | Staff use an IntelliPay capture surface; the system receives a token |
| PCI scope | GHF holds cardholder data (SAQ-D territory) | GHF never holds it (SAQ-A territory) |

A token is IntelliPay's `custid` — a numeric customer id, scoped to GHF's merchant account. It's useless to anyone else, works for both cards and bank accounts, and is what every IntelliPay charge method (`card_payment`, `payment_create`, batch upload) accepts in place of a number.

---

## 1 · What to store (data model changes)

**Add** to the member's billing record:

| Field | Type | Notes |
|---|---|---|
| `TOKEN` | string(32) | IntelliPay `custid`. Required for any member on autopay. Read-only in the UI — only the system writes it. |
| `TOKEN_TYPE` | `C` / `A` | Card or bank (ACH). The batch file needs it. |
| `METHOD_HINT` | string(24) | e.g. `VI ***1111` or `Bank ***4321`. For staff/member display only. |
| `TOKEN_SOURCE` | enum | `migration` · `online-join` · `front-desk` · `member-update`. Tells you how it got there. |
| `TOKEN_CREATED` | datetime | When IntelliPay issued it. |
| `TOKEN_STATUS` | enum | `active` · `expired` · `declined` · `needs-update`. Driven by batch returns. |

**Remove** (after the sweep is verified — see Phase 5):
- Card number, expiration date, CVV (should never have existed), bank account number, routing number.
- The same values wherever else they live: reports, spreadsheets, exports, old batch files on the SFTP server, log files, **database backups**.

**Keep** (not cardholder data): name on account, billing address, card brand, last 4 digits, bank name.

**UI change:** the "Credit Card #" / "Bank Account #" fields become a single read-only **TOKEN** field with the hint next to it. Add a **"Add / replace payment method"** button that launches the IntelliPay capture (below) instead of a text box.

---

## 2 · The one-time sweep — getting every card into IntelliPay

Every active billing record needs a `custid`. There are two ways to get there.

### Option A — IntelliPay bulk import *(recommended: ask for it first)*
Processors run a card-data import service for exactly this: the merchant hands over an **encrypted file** (PGP, over SFTP) with one row per customer, the processor tokenizes everything on their side, and returns a mapping file of *your reference → custid*.

- GHF never writes code that handles card numbers, and the export is one controlled event.
- **Ask IntelliPay:** file spec, encryption key, how ACH rows are handled, turnaround, and that the return file maps to our member ID via the `account` field.

### Option B — API sweep with `cust_create` *(fallback)*
IntelliPay's API accepts `cust_create` with raw card or bank fields and returns the `custid`. GHF already holds the numbers, so this is permitted **only if GHF is PCI-validated for it** (AGENTS.md "Case 2") — otherwise it's a compliance violation even though the API accepts it.

If used: one POST per member — `account`=member ID, `firstname`, `lastname`, `address1`, `city`, `state` (2-letter), `zipcode`, `country`=`USA`, then either `cardname` + `cardnum` + `expdate` (MMYY) or `bankacctname` + `bankacctnum` + `routingnum` + `bankaccttype` (C/S). Run from a locked-down host, TLS only, never log the request bodies, one run.

### Either way — the sweep checklist
1. **Freeze** payment-method edits in the member system during the sweep window (between two dues cycles — dues run every other Wednesday).
2. **Clean the data first** — this is where migrations fail:
   - De-duplicate members (one billing record per member; `account` must be unique — it's how we reconcile).
   - Normalize `expdate` to MMYY, state to 2 letters, country to ISO-3.
   - Luhn-check card numbers; ABA-checksum routing numbers; bank type C/S.
   - **Pull out already-expired cards** — IntelliPay will store them but every charge fails (`-7 stored card expired`). These members go straight to the outreach list.
   - Members with *both* a card and a bank account: decide which is primary; create one token each if needed.
3. **Rehearse in sandbox** with IntelliPay test cards and a 50-row sample. Confirm the return mapping lands in the TOKEN field correctly.
4. **Run production.** Capture per-row result: `custid` or failure reason.
5. **Reconcile:** every active autopay member has a token, or is on a named exception list with a reason. Second pass on transient failures (search with `cust_search(account=…)` before retrying so we never double-create).
6. **Outreach** for the exception list (expired, invalid, missing): email/text a secure "update your payment method" link (Lightbox Store Only) or handle at the desk. Give it a deadline before the first token-based dues run.

---

## 3 · The nightly SFTP batch

Today the file carries numbers; after cutover it carries `TOKEN` + `TOKEN_TYPE` + amount + invoice. IntelliPay's batch upload (origin code 4) is the same processing path as `payment_create`, so the same rules apply:

| Item | What to do |
|---|---|
| **Get the token-based file spec from IntelliPay** | Column names for `custid`/type/amount/invoice; delimiter; the rejection/return file format. This is a blocking question. |
| Unique invoice per member per cycle | e.g. `GHF-<memberId>-<YYYYMMDD>`. Lets us search before resubmitting and never double-charge. |
| Handle return codes | `-2` custid not found → token missing/wrong merchant · `-7` card expired · `-8` stored card missing · `-4/-5` bank details missing/invalid · `-10` amount problem. Each maps to a `TOKEN_STATUS` and an outreach action. |
| ACH timing | ACH rows are voidable until 5 pm MT on the day the file is transmitted; card rows settle per normal. |
| **Parallel cycle** | For one dues cycle, generate the file both ways (numbers and tokens), compare row counts and totals, then transmit only the token file. |
| Retire the old file | Delete historical batch files containing numbers from the SFTP server and any archive. |

**Note on multiple clubs:** a `custid` belongs to one IntelliPay merchant account. If Main / Women / Tioga bill under separate merchant IDs, each member needs a token under the MID that bills them. Confirm the MID structure before the sweep.

---

## 4 · What happens with online joins

Nothing changes in principle — the join flow we built is already token-native:

1. Member picks club, plan, enters details → we create the member record with a **member ID**.
2. **Recurring method:** Lightbox in Store Only mode. Card/bank data goes straight from the browser to IntelliPay; we receive `custid`, type, and hint → written to `TOKEN`, `TOKEN_TYPE`, `METHOD_HINT`, `TOKEN_SOURCE=online-join`.
3. **Due today:** one real charge by `custid` (or a separate card if they chose bank draft). GHF never sees a number.
4. The member appears in that night's export with their token — same file, same columns as migrated members.

Two things to lock down:
- We pass **member ID as IntelliPay's `account`** field, so `cust_search(account=…)` always finds the right token — same convention as the sweep.
- The **front desk** must stop keying numbers after cutover. Give staff the same tool: a staff-facing Lightbox Store Only page (or the Lightbox Card Present terminal for chip/tap), which hands the member system a token. One new card typed into the old field puts GHF back in scope.

---

## 5 · After cutover — keeping tokens healthy

- **Turn on Visa Account Updater.** Monthly, IntelliPay checks stored Visa/Mastercard cards expiring next month against the card networks and refreshes reissued numbers/expiry automatically. Requirements: saved payment method, active customer record, primary record only. Amex/Discover aren't covered — keep the expiring-card outreach for those.
- **Postbacks:** IntelliPay's server-to-server confirmation is the authoritative record; wire it into `TOKEN_STATUS` updates.
- **Member self-service:** a "update my card" link that opens Lightbox Store Only and replaces the token — no staff involvement, no numbers.
- **Access control:** tokens are merchant-scoped and not cardholder data, but treat them as sensitive — role-based access, audit log on changes.

---

## 6 · Phased timeline

| Phase | When | What | Done when |
|---|---|---|---|
| **0 · Discovery** | Week 1 | Confirm GHF's PCI status (AOC?). Count active autopay members by card vs bank, by club/MID. Open the IntelliPay questions below. **Order front-desk terminals** (§9). | Answers in hand; Option A or B chosen; terminals ordered. |
| **1 · Build** | Weeks 1–3 | Member-system vendor adds TOKEN fields, read-only UI, "Add/replace method" launcher; batch generator emits tokens; online-join export maps to new fields; staff join page in `businessattended` mode. | Sandbox end-to-end: join → token → batch file → IntelliPay accepts. |
| **2 · Rehearse** | Week 3 | Sample sweep (50 rows) in sandbox; token batch file accepted; return-file handling tested with forced `-2`/`-7`. | Runbook written; timings known. |
| **3 · Sweep** | Between two dues Wednesdays | Freeze edits → clean data → run sweep → reconcile → outreach list. | 100% of active autopay have a token or a named exception. |
| **4 · Cutover** | Next dues cycle | Parallel file compare → transmit token file → monitor returns for 48 h. Front desk switches to terminal capture the same day. | First token-based cycle settles; return rate ≈ historical. |
| **5 · Purge & attest** | Within 30 days | Delete numbers from DB, reports, exports, SFTP archive, logs, and backups (or set backup retention to expire them). Document destruction. Rotate IntelliPay API keys. Update the PCI self-assessment. | Written attestation that no cardholder data remains. |

---

## 7 · Risks and how we handle them

| Risk | Mitigation |
|---|---|
| Expired/invalid cards surface in the sweep | Expected — that's the exception list. Outreach starts the day of the sweep with a deadline before Phase 4. |
| Duplicate member records → duplicate tokens | De-dupe before the sweep; `account` unique; `cust_search` before any retry. |
| Numbers survive in a backup or old report | Phase 5 inventory covers backups, SFTP archive, BI extracts, staff spreadsheets. Set retention so old backups age out. |
| Staff keep typing card numbers | Remove the field entirely; give them the Lightbox tool; brief and audit in week 1 after cutover. |
| Token created under the wrong merchant ID | Confirm MID structure in Phase 0; sweep per MID. `-2 custid not found` in returns is the tell. |
| Batch file rejected on first token cycle | Parallel cycle in Phase 4; IntelliPay reviews a sample file before go-live. |
| ACH not testable in sandbox today | Ask IntelliPay to enable ACH on the test merchant (currently `achenable:false`). |

---

## 8 · Questions to close with IntelliPay

1. Do you offer a **bulk card/ACH import** (encrypted file → tokens)? Spec, encryption, turnaround, return mapping by `account`.
2. **Batch upload file spec** for token-based rows (custid + type + amount + invoice) and the return/rejection file format.
3. Confirm the merchant-ID structure for GHF's three clubs and whether one `custid` can bill under all.
4. Enable **Visa Account Updater** and **ACH on the sandbox** merchant.
5. Production keys and whether our join domain needs registering in the iframe allow-list (`add_iframe_url`).
6. Postback endpoint registration for production.
7. **Terminals:** recommended Dejavoo model, price per unit, monthly fees, lead time, and one merchant-key/API-key pair per desk (5).

## Questions to close with GHF / the member-system vendor
1. Current PCI status — is there an AOC that covers storing card data? (Decides Option A vs B and how urgent Phase 5 is.)
2. Exact list of every place a card/bank number is stored or printed today.
3. Active autopay count, card vs bank, per club.
4. Who owns the batch generator and the SFTP job, and how quickly can the field mapping change?
5. Dues calendar — which two Wednesdays bracket the sweep window.

---

## Owners at a glance

| Workstream | Owner |
|---|---|
| Data model, UI, batch generator | Member-system vendor |
| Sweep execution & reconciliation | GHF IT + vendor (Option B) or IntelliPay (Option A) |
| Online join integration & staff capture tool | Us |
| Outreach to exception members | GHF member services |
| PCI attestation & purge | GHF IT / compliance |
| API keys, VAU, batch spec, sandbox ACH, terminal quote & provisioning | IntelliPay |
| Terminal purchase, network drops at desks, staff training | GHF operations |

---

## 9 · Terminals for the front desk (purchase)

After cutover nobody at a desk can type a card number into the member system, so every staffed desk that joins members or updates payment methods needs an IntelliPay-connected way to capture a card and hand back a token.

**How it works.** IntelliPay's **Lightbox Card Present Terminal** is the same Lightbox we use online, opened with `operatingenv=businessattended`. The form gains chip / tap / key-entry tabs and routes the capture through the physical terminal bound to that desk. Each terminal is bound to its own **merchant-key + API-key pair** in the IntelliPay admin, so the staff join page picks the desk's key pair and the token comes back exactly as it does online (`custid`, `paymenttype`, `methodhint`).

**Hardware IntelliPay supports** (confirm current models with them):
- **Dejavoo** tap-to-pay countertop terminals — chip + contactless, network-connected. Preferred: no card data touches the PC.
- **Ingenico** terminals — same integration path.
- **ID Tech Augusta / 3350** — USB chip readers with an IntelliPay driver, for a reader plugged into the desk PC.

Chip and contactless are the entry methods to use. Avoid magnetic swipe: unless the reader is P2PE-certified, swipe data puts PCI scope back on GHF.

**What to buy**

| Location | Desks | Units |
|---|---|---|
| GHF Main (24/7) | Front desk + membership office | 2 |
| GHF Women | Front desk | 1 |
| GHF Tioga | Front desk | 1 |
| Spare / swap | — | 1 |
| **Total** | | **5** |

- Ask IntelliPay for a quote on the Dejavoo model they currently recommend, plus any per-terminal monthly gateway fee. Countertop EMV/contactless units typically run a few hundred dollars each — treat that as a budgeting placeholder until the quote lands.
- Order in **Phase 0**: hardware lead time and key-pair provisioning are the long poles for the front-desk switch in Phase 4.
- Each desk needs: network drop or Wi-Fi for the terminal, the staff join page (our join wizard in `businessattended` mode), and the desk's key pair stored server-side — never in the browser.
- Train staff on the new flow in the week before cutover; the old card field will be gone.

---

# Appendix A — Payloads that come back, and exactly what to store

Sources: IntelliPay AGENTS.md (§4a, §7f, §9, §6), plus responses observed against the sandbox merchant. Field names below are verbatim.

## A1 · The six payloads

### 1. Lightbox Store Only — browser callback `runOnApproval(r)`
Fires when a member (online join, member self-service, or front-desk capture) saves a payment method. **This is the primary source of a token.**
```
r = {
  status,            // > 0 on success
  response: "A",     // A = approved (D / E arrive via runOnNonApproval)
  custid,            // ← THE TOKEN
  paymenttype,       // "C" card | "A" bank        (observed: "C")
  methodhint,        // "VI ***1111"               (observed)
  cardbrand,         // "Visa", "Mastercard", …
  paymentid, authcode, declinereason, amount, fee,   // populated only when a charge ran (not store-only)
  hmac, nonce,       // integrity check — verify, don't persist
  receiptelements    // receipt markup — ignore
}
```

### 2. `cust_create` — one-time sweep (Option B) or IntelliPay bulk import (Option A)
```
{ "status": 19682099 }        // > 0 → the custid (token).  -1 auth · -2 could not create
```
Option A returns the same thing as a file: `account → custid` per row.

### 3. `cust_read` — what IntelliPay holds against a token *(observed field list)*
```
{ "status": "19682099",          // = custid
  "account": "GHF-…",            // our member ID, as we sent it
  "firstname", "lastname", "address1", "address2", "city", "state", "zipcode", "country", "phone", "email",
  "cardtype": "Card",            // brand text when a card is stored
  "cardending": "1111",          // last 4
  "cardnumdisplay": "…",         // masked display form
  "cardname", "expdate",         // MMYY
  "bankacctnum": "???",          // masked
  "bankaccttype": "C"|"S", "routingnum",
  "relatedmerchantkey": "M7976"  // the merchant the token belongs to
}
```
Use it to **reconcile after the sweep** and to refresh display hints — fetch on demand, don't mirror it.

### 4. `card_payment` by `custid` — the online-join "due today" charge
```
success: { "status": 19866057, "response": "A", "authcode": "269224", "declinereason": "Success",
           "avsresult": "Y", "fee": 0.01, "custid": 18096987, "paymentid": 19866057 }
decline: { "status": -4, "response": "D", "authcode": "", "declinereason": "DECLINE", "paymentid": 19866058 }
```
Always read **both** `status` and `response`. A decline is still a recorded payment with a `paymentid`.

### 5. `payment_create` / batch upload — the nightly dues run
Per row: `status` > 0 = `paymentid` queued. Failures: `-2` custid not found · `-3` bad type · `-4` routing missing/invalid · `-5` bank acct missing · `-6` bank type not C/S · `-7` **stored card expired** · `-8` stored card missing · `-9` record not created · `-10` amount invalid.
ACH is asynchronous: the settle/return result arrives days later via postback (or `list_bank_returns`).

### 6. Postback — server-to-server, the durable record (form-encoded POST)
```
timestamp, customerid (= custid), paymentid, account, firstname, lastname,
address1, address2, city, state, zipcode, phone, method ("CARD"|"ACH"),
invoice, authcode, avsdata, ipaddress, amount, fee, total, comment, notes,
merchantid, origin, department, arglist
```
Up to 3 delivery attempts; **must be idempotent on `paymentid`**; return 2xx only after the row is saved; never redirect.

## A2 · Exactly what to store

### Table 1 — `member_billing` (one row per member)

| Column | Type | Comes from | Notes |
|---|---|---|---|
| `member_id` | string(20) PK | ours | Sent to IntelliPay as `account` on every call — this is the join key. |
| `ipay_custid` | string(32) **(the TOKEN)** | Lightbox `custid` · `cust_create` `status` · postback `customerid` · bulk-import mapping | Required for autopay. Read-only in the UI. |
| `ipay_merchant_id` | string(12) | postback `merchantid` · `cust_read` `relatedmerchantkey` | Which MID the token lives under. Needed if the clubs bill separately. |
| `token_type` | char(1) `C`/`A` | Lightbox `paymenttype` · postback `method` (CARD→C, ACH→A) · what we sent in the sweep | Batch file needs it. |
| `method_hint` | string(24) | Lightbox `methodhint` · `cust_read` `cardnumdisplay` · "Bank ***" + last 4 | Display only. |
| `card_brand` | string(16) | Lightbox `cardbrand` · `cust_read` `cardtype` | Display; also drives Account Updater expectations (Visa/MC only). |
| `card_last4` | char(4) | `cust_read` `cardending` | Display / reconciliation. Not cardholder data. |
| `card_exp_mmyy` | char(4) | `cust_read` `expdate` | **Allowed under PCI.** Drives expiring-card outreach for Amex/Discover. |
| `token_source` | enum | ours | `migration` · `online-join` · `front-desk` · `member-update` |
| `token_created_at` | datetime | ours (at receipt) | |
| `token_status` | enum | derived from batch returns / postbacks | `active` · `expired` (-7) · `needs-update` (-2/-4/-5/-8) · `declined` |
| `token_status_reason` | string(64) | last `declinereason` or numeric code | For staff, not logic. |
| `token_updated_at` | datetime | ours | |

### Table 2 — `payment_history` (one row per charge attempt — online join, batch, postback)

| Column | Type | Comes from |
|---|---|---|
| `ipay_paymentid` | string(32) PK | `card_payment`/`payment_create` `paymentid` · postback `paymentid` — idempotency key |
| `member_id` | string(20) | ours / postback `account` |
| `ipay_custid` | string(32) | response `custid` · postback `customerid` |
| `invoice` | string(40) | ours: `GHF-<memberId>-<YYYYMMDD>` — unique per member per cycle |
| `amount`, `fee`, `total` | decimal(10,2) | response / postback |
| `method` | `CARD`/`ACH` | postback `method` |
| `response` | char(1) `A`/`D`/`E` | response `response` |
| `status_code` | int | numeric `status` (paymentid or negative code) |
| `authcode` | string(12) | response / postback `authcode` |
| `declinereason` | string(64) | response `declinereason` |
| `avsresult` | char(1) | response `avsresult` · postback `avsdata` |
| `origin` | string(16) | postback `origin` (API / Batch Upload / Hosted Lightbox) |
| `source` | enum | ours: `lightbox` · `api` · `batch-return` · `postback` |
| `ipay_timestamp` | datetime | postback `timestamp` (Mountain Time — convert) |
| `received_at` | datetime | ours |
| `raw_payload` | json | the full response/postback as received — audit trail; contains no card data |

### Never store
`cardnum`, `cvv`, `expdate` *as part of a PAN*, `bankacctnum`, `routingnum`, `trackdata`, and the Lightbox `hmac`/`nonce` (verify, then discard). Nothing that comes back from IntelliPay contains a full number, so the only way a number lands in these tables is if someone types it in — which is why the old fields must be deleted, not just hidden.

### Nightly SFTP row (what leaves GHF)
`member_id` (as `account`) · `ipay_custid` · `token_type` · `amount` · `invoice` — column names to be confirmed against IntelliPay's batch spec (open question #2).
