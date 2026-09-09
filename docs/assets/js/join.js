/* GHF — Join Online wizard (cart + IntelliPay Lightbox, two-stage payment)
 *
 *  01 Home club  →  02 Plan  →  03 Details  →  04 Recurring dues (Store Only, returns token)
 *  →  05 Due today (one real charge: saved card in one tap, or a separate card)  →  active.
 *
 *  Talks to intellipay/server.py (window.GHF_JOIN_API, set at build time).
 *  Local testing: append ?api=http://localhost:4400 once — it is remembered in localStorage.
 *  Card / bank data never touches this page: it goes browser → IntelliPay inside the Lightbox.
 */
(function () {
  "use strict";

  var wizard = document.querySelector(".join");
  if (!wizard) return;

  /* ---------- API base ---------- */
  var API = (function () {
    try {
      var q = new URLSearchParams(location.search).get("api");
      if (q) localStorage.setItem("ghf-join-api", q.replace(/\/$/, ""));
      var saved = localStorage.getItem("ghf-join-api");
      if (saved) return saved;
    } catch (e) {}
    return (window.GHF_JOIN_API || "").replace(/\/$/, "");
  })();
  function api(path, opts) {
    return fetch(API + path, Object.assign({ mode: "cors" }, opts || {})).then(function (r) {
      return r.json().then(function (j) { if (!r.ok) throw new Error(j.error || ("Request failed (" + r.status + ")")); return j; });
    });
  }
  function money(n) { return "$" + Number(n || 0).toFixed(2); }

  /* ---------- state ---------- */
  var state = { loc: null, locMeta: "", type: "Individual", plan: null, planKey: null, fee: null, note: "",
                first: "", last: "", email: "", phone: "", method: "CC" };
  var INCLUDES_NOTE = "Every membership includes all 900+ monthly classes, hot yoga, pools & spa, Kid's Club, and access to all three locations.";
  var step = 1, TOTAL = 5;
  var quote = null, member = null, rec = null, terminalLoaded = false;

  var stepsEls = wizard.querySelectorAll(".join-step");
  var navItems = wizard.querySelectorAll(".join__steps-nav li");
  var barFill = wizard.querySelector(".join__progress-bar i");
  var backBtn = wizard.querySelector(".join__nav-row .back");
  var nextBtn = wizard.querySelector(".join__nav-row .next");
  var countEl = wizard.querySelector(".join__count");
  var payStatus = wizard.querySelector("#payStatus");
  var vaultBtn = wizard.querySelector("#vaultBtn");

  /* ---------- step navigation (unchanged UX) ---------- */
  function canLeave(n) {
    if (n === 1) return !!state.loc;
    if (n === 2) return !!state.plan;
    if (n === 3) {
      var ok = true;
      wizard.querySelectorAll('.join-step[data-step="3"] input[required]').forEach(function (i) {
        var valid = i.value.trim() && i.checkValidity();
        i.style.borderBottomColor = valid ? "" : "var(--accent)";
        if (!valid) ok = false;
      });
      return ok;
    }
    return true;
  }
  function refreshNext() {
    if (step === 1) nextBtn.disabled = !state.loc;
    else if (step === 2) nextBtn.disabled = !state.plan;
    else nextBtn.disabled = false;
    nextBtn.querySelector(".lbl").textContent = step === 3 ? "Continue to Payment" : "Continue";
    /* steps 4 and 5 have their own actions (the secure window / pay button) */
    nextBtn.style.display = step >= 4 ? "none" : "";
    backBtn.classList.toggle("is-visible", step > 1 && step < 5);
  }
  function goStep(n) {
    if (n < 1 || n > TOTAL) return;
    step = n;
    stepsEls.forEach(function (s) { s.classList.toggle("is-active", +s.dataset.step === n); });
    navItems.forEach(function (li, i) {
      li.classList.toggle("is-active", i + 1 === n);
      li.classList.toggle("is-done", i + 1 < n);
    });
    barFill.style.width = (n / TOTAL) * 100 + "%";
    countEl.textContent = "Step 0" + n + " / 0" + TOTAL;
    updateSummary();
    refreshNext();
    var top = wizard.getBoundingClientRect().top + window.scrollY - 90;
    if (window.scrollY > top) window.scrollTo({ top: top, behavior: "smooth" });
  }

  /* ---------- selections ---------- */
  wizard.querySelectorAll('[data-step="1"] .choice').forEach(function (c) {
    c.addEventListener("click", function () {
      wizard.querySelectorAll('[data-step="1"] .choice').forEach(function (x) { x.classList.remove("is-selected"); });
      c.classList.add("is-selected");
      state.loc = c.dataset.name;
      var meta = c.querySelector(".meta"); state.locMeta = meta ? meta.textContent.trim() : "";
      updateSummary(); refreshNext();
      setTimeout(function () { goStep(2); }, 420);
    });
  });
  wizard.querySelectorAll('[data-step="2"] .choice').forEach(function (c) {
    c.addEventListener("click", function () {
      wizard.querySelectorAll('[data-step="2"] .choice').forEach(function (x) { x.classList.remove("is-selected"); });
      c.classList.add("is-selected");
      state.plan = c.dataset.name; state.planKey = c.dataset.plan;
      state.fee = c.dataset.fee; state.note = c.dataset.note || "";
      updateSummary(); refreshNext(); loadQuote();
      setTimeout(function () { goStep(3); }, 420);
    });
  });
  wizard.querySelectorAll(".seg button").forEach(function (b) {
    b.addEventListener("click", function () {
      wizard.querySelectorAll(".seg button").forEach(function (x) { x.classList.remove("is-on"); });
      b.classList.add("is-on"); state.type = b.dataset.type; updateSummary();
    });
  });
  wizard.querySelectorAll('[data-step="3"] input').forEach(function (i) {
    i.addEventListener("input", function () { state[i.name] = i.value.trim(); updateSummary(); });
  });
  wizard.querySelectorAll("#payMethods .choice").forEach(function (c) {
    c.addEventListener("click", function () {
      wizard.querySelectorAll("#payMethods .choice").forEach(function (x) { x.classList.remove("is-selected"); });
      c.classList.add("is-selected"); state.method = c.dataset.method;
      updateSummary(); applyMode();
    });
  });

  /* ---------- summary / cart ---------- */
  function setSum(key, val, html) {
    var dd = wizard.querySelector('[data-sum="' + key + '"]');
    if (!dd) return;
    if (html) dd.innerHTML = val; else dd.textContent = val || "—";
    dd.classList.toggle("empty", !val);
  }
  function updateSummary() {
    setSum("loc", state.loc); setSum("type", state.type); setSum("plan", state.plan); setSum("fee", state.fee);
    setSum("name", (state.first || state.last) ? (state.first + " " + state.last).trim() : "");
    setSum("pay", rec ? (rec.hint || rec.method) : (step >= 4 ? (state.method === "ACH" ? "Bank draft" : "Card") : ""));
    var note = wizard.querySelector("[data-sum-note]");
    if (note) note.textContent = state.note ? state.note + " " + INCLUDES_NOTE : INCLUDES_NOTE;
  }
  function loadQuote() {
    if (!state.planKey) return;
    api("/api/quote?plan=" + encodeURIComponent(state.planKey) + "&addons=").then(function (q) {
      quote = q;
      var cart = wizard.querySelector("[data-cart]");
      if (cart) cart.innerHTML = q.lines.map(function (l) {
        return '<div class="sum-row"><dt>' + l.label + "</dt><dd>" + money(l.amount) + "</dd></div>";
      }).join("") + '<div class="sum-row"><dt>Sales tax</dt><dd>' + money(q.tax) + "</dd></div>";
      setSum("due", money(q.dueToday), true);
      var r = wizard.querySelector("[data-sum-recurring]");
      if (r) r.textContent = "Then " + money(q.recurringWithTax) + " every other Wednesday (includes tax).";
    }).catch(function (e) { showStatus("bad", "Pricing unavailable: " + e.message); });
  }

  /* ---------- step 3 → create member → step 4 ---------- */
  function createMember() {
    nextBtn.disabled = true;
    return api("/api/member", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ firstName: state.first, lastName: state.last, email: state.email, phone: state.phone,
                             club: state.loc + " — " + state.locMeta, plan: state.planKey, addons: [], membershipType: state.type }) })
    .then(function (m) {
      member = m;
      ["account", "invoice"].forEach(function (k) { wizard.querySelector("#ipay-" + k).value = m.memberId; });
      wizard.querySelector("#ipay-first").value = m.firstName; wizard.querySelector("#ipay-last").value = m.lastName;
      wizard.querySelector("#ipay-email").value = m.email; wizard.querySelector("#ipay-phone").value = m.phone || "";
      goStep(4); loadTerminal();
    })
    .catch(function (e) { nextBtn.disabled = false; alert("We couldn't start your membership: " + e.message); });
  }

  /* ---------- IntelliPay Lightbox: runtime injection ---------- */
  function showStatus(kind, msg) { if (!payStatus) return; payStatus.className = "pay-status " + (kind || ""); payStatus.textContent = msg; }
  function injectTerminal(html) {
    var t = document.createElement("template"); t.innerHTML = html;
    /* scripts inserted via innerHTML never run — re-create them in order, synchronously */
    Array.prototype.slice.call(t.content.querySelectorAll("script")).forEach(function (s) {
      var n = document.createElement("script");
      if (s.src) n.src = s.src; else n.textContent = s.textContent;
      s.parentNode.removeChild(s); document.head.appendChild(n);
    });
    document.head.appendChild(t.content);
  }
  function loadTerminal() {
    if (terminalLoaded) { applyMode(); return; }
    showStatus("", "Connecting to secure window…");
    fetch(API + "/api/terminal", { mode: "cors" }).then(function (r) {
      if (!r.ok) return r.json().then(function (j) { throw new Error(j.error || "terminal unavailable"); });
      return r.text();
    }).then(function (html) {
      injectTerminal(html);
      if (typeof intellipay === "undefined") throw new Error("Lightbox script did not load");
      /* window.load already fired, so initialize by hand (documented pattern is head-render) */
      if (!document.getElementById("intellipay-lightbox")) intellipay.initialize();
      terminalLoaded = true;
      intellipay.setStoreOnly(true);
      intellipay.runOnApproval(onVaulted);
      intellipay.runOnNonApproval(function (r) {
        var out = wizard.querySelector("#recOut");
        out.innerHTML = '<div class="pay-note warn">' + ((r && r.declinereason) || "That payment method could not be saved.") + " Please try another.</div>";
      });
      applyMode();
      var tries = 0, rv = setInterval(function () {
        tries++;
        if (intellipay.isReady) { clearInterval(rv); vaultBtn.disabled = false; showStatus("ok", "Secure window ready — nothing will be charged"); }
        else if (tries > 80) { clearInterval(rv); showStatus("bad", "Secure window didn't respond. Reload and try again."); }
      }, 250);
    }).catch(function (e) { showStatus("bad", "Secure window unavailable: " + e.message); });
  }

  /* Only these (field, property) pairs are read by IntelliPay's frame. */
  function brandLightbox(stage) {
    var set = function (f, fn, v) { try { intellipay[fn](f, v); } catch (e) {} };
    var today = stage === "today", ach = state.method === "ACH";
    set("header", "setItemBackgroundColor", "#005898"); set("header", "setItemColor", "#ffffff");
    set("header", "setItemLabel", today ? "Pay today's total" : (ach ? "Set up your bank draft" : "Set up recurring dues"));
    if (window.__ghfLogo) { set("banner", "setItemUrl", window.__ghfLogo); set("bannerImage", "setItemHeight", "54px"); }
    set("company", "setItemLabel", "Gainesville Health & Fitness");
    set("leftContainer", "setItemBackgroundColor", "#0b0b0c"); set("lightbox", "setItemBorderRadius", "4px");
    set("input", "setItemBackgroundColor", "#ffffff"); set("input", "setItemColor", "#0b0b0c");
    set("input", "setItemBorderRadius", "2px"); set("input", "setItemBorderBottom", "2px solid #005898");
    set("inputBorder", "setItemColor", "#cfd6dd"); set("inputFont", "setItemColor", "#0b0b0c");
    set("paymentTypeButtonSelected", "setItemColor", "#ffffff");
    set("button", "setItemBackgroundColor", "#0d6fbf"); set("button", "setItemColor", "#ffffff");
    set("button", "setItemLabel", today ? "Pay " + money(rec.dueToday) : (ach ? "Save bank account" : "Save my card"));
    set("account", "setItemLabel", "Member ID");
    try { intellipay.disable("account"); intellipay.disable("email"); intellipay.disable("phone"); } catch (e) {}
    set("successmessage", "setItemLabel", today ? "Payment received — welcome to GHF." : "Saved — nothing was charged today.");
    set("declinemessage", "setItemLabel", "We couldn't process that. Please check the details or try another card.");
  }
  function applyMode() {
    if (typeof intellipay === "undefined" || !terminalLoaded) return;
    var ach = state.method === "ACH";
    try { intellipay.setACHAvailable(ach); intellipay.setCCAvailable(!ach); } catch (e) {}
    brandLightbox("recurring");
    vaultBtn.querySelector(".lbl").textContent = ach ? "Save Bank Account" : "Save Payment Method";
  }
  vaultBtn.addEventListener("click", function () { if (typeof intellipay !== "undefined") intellipay.onSubmit(); });

  /* ---------- stage 1 result: token stored → step 5 ---------- */
  function onVaulted(resp) {
    api("/api/recurring-method", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ memberId: member.memberId, custid: resp.custid, paymenttype: resp.paymenttype, methodhint: resp.methodhint }) })
    .then(function (r) { rec = r; updateSummary(); goStep(5); renderToday(); })
    .catch(function (e) { wizard.querySelector("#recOut").innerHTML = '<div class="pay-note warn">' + e.message + "</div>"; });
  }
  function renderToday() {
    var a = money(rec.dueToday), box = wizard.querySelector("#todayBox");
    box.innerHTML = rec.canReuseForToday
      ? '<div class="pay-total">' + a + "</div>" +
        '<div class="choice-grid choice-grid--2"><button class="choice choice--pay is-selected" type="button"><span class="choice__check">✓</span>' +
        "<h3>Use the card I just saved</h3><p class=\"meta\">" + (rec.hint || "Saved card") + " — one tap, nothing to re-enter.</p></button></div>" +
        '<div class="pay-actions"><button class="btn btn--solid" type="button" id="payNow"><span class="lbl">Pay ' + a + '</span> <span class="arr">→</span></button><span class="pay-status" id="payStatus2"></span></div>'
      : '<div class="pay-total">' + a + "</div>" +
        '<div class="pay-note warn">Your dues will draft from your <b>bank account</b>. We don\'t accept bank draft for the up-front payment — please add a credit or debit card for today\'s total.</div>' +
        '<div class="pay-actions"><button class="btn btn--solid" type="button" id="payCard"><span class="lbl">Add Card &amp; Pay ' + a + '</span> <span class="arr">→</span></button><span class="pay-status" id="payStatus2"></span></div>';
    var btn = box.querySelector("#payNow") || box.querySelector("#payCard");
    btn.addEventListener("click", rec.canReuseForToday ? payWithSaved : payWithNewCard);
  }
  function busy(msg) { var s = wizard.querySelector("#payStatus2"); if (s) { s.className = "pay-status"; s.textContent = msg; } }
  function payWithSaved() {
    busy("Processing…"); this.disabled = true;
    api("/api/charge-today", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ memberId: member.memberId }) })
      .then(function (o) { finish(o, o.approved ? "Charged to your saved card" : "Submitted"); })
      .catch(function (e) { busy(""); wizard.querySelector("#payCard, #payNow").disabled = false; wizard.querySelector("#todayBox").insertAdjacentHTML("beforeend", '<div class="pay-note warn">' + e.message + "</div>"); });
  }
  function payWithNewCard() {
    intellipay.setStoreOnly(false);
    intellipay.setACHAvailable(false); intellipay.setCCAvailable(true);
    brandLightbox("today");
    wizard.querySelector("#ipay-amount").value = Number(rec.dueToday).toFixed(2);
    intellipay.runOnApproval(function (resp) {
      api("/api/today-card", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ memberId: member.memberId, custid: resp.custid, methodhint: resp.methodhint, status: resp.status, approved: resp.response === "A", amount: rec.dueToday }) })
      .then(function (o) { finish(o, "Paid with your card"); });
    });
    intellipay.onSubmit();
  }

  /* ---------- done ---------- */
  function finish(o, label) {
    var success = document.querySelector(".join-success");
    var nameEl = success.querySelector("[data-success-name]");
    if (nameEl && state.first) nameEl.textContent = state.first + ", you're going to feel good here.";
    var detail = success.querySelector("[data-success-detail]");
    if (detail) detail.innerHTML =
      '<span class="chip">Member ID <b>' + member.memberId + "</b></span>" +
      '<span class="chip">' + label + " <b>" + money(rec.dueToday) + "</b></span>" +
      '<span class="chip">Dues from <b>' + (rec.hint || rec.method) + "</b></span>";
    success.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }

  /* ---------- nav buttons ---------- */
  backBtn.addEventListener("click", function () { goStep(step - 1); });
  nextBtn.addEventListener("click", function () {
    if (!canLeave(step)) { refreshNext(); return; }
    if (step === 3) { createMember(); return; }
    if (step < TOTAL) goStep(step + 1);
  });

  updateSummary();
  refreshNext();
})();
