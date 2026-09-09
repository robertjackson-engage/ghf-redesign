/* GHF — Join Online (cart-style module + IntelliPay Lightbox, two-stage payment)
 *
 *  01 Home club → 02 Membership (+ add-ons) → 03 Details → 04 Recurring dues (Store Only → token)
 *  → 05 Due today (saved card in one tap, or a separate card) → active.
 *
 *  Talks to intellipay/server.py. API base: ?api=… (remembered) → localhost:4400 when served
 *  locally → window.GHF_JOIN_API (baked in at build time).
 *  Card / bank data never touches this page — it goes browser → IntelliPay inside the Lightbox.
 */
(function () {
  "use strict";
  var root = document.querySelector(".jn");
  if (!root) return;

  var $ = function (s) { return root.querySelector(s); };
  var money = function (n) { return "$" + Number(n || 0).toFixed(2); };

  /* ---------- API base ---------- */
  var API = (function () {
    try {
      var q = new URLSearchParams(location.search).get("api");
      if (q) localStorage.setItem("ghf-join-api", q.replace(/\/$/, ""));
      var saved = localStorage.getItem("ghf-join-api");
      if (saved) return saved;
    } catch (e) {}
    if (/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) return "http://localhost:4400";
    return (window.GHF_JOIN_API || "").replace(/\/$/, "");
  })();
  function api(path, body) {
    var opts = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
    opts.mode = "cors";
    return fetch(API + path, opts).then(function (r) {
      return r.json().then(function (j) { if (!r.ok) throw new Error(j.error || ("Request failed (" + r.status + ")")); return j; });
    });
  }

  /* ---------- state ---------- */
  var CAT = null, club = "", plan = "24mo", addons = [], mode = "CC";
  var member = null, rec = null, terminalLoaded = false;

  /* ---------- steps ---------- */
  function go(n) {
    [1, 2, 3, 4, 5, 6].forEach(function (i) { var c = $("#c" + i); if (c) c.classList.toggle("hide", i !== n); });
    [1, 2, 3, 4, 5].forEach(function (i) { var e = $("#s" + i); if (e) e.className = "rl" + (i < n ? " done" : i === n ? " on" : ""); });
    var top = root.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }
  root.querySelectorAll("[data-go]").forEach(function (b) {
    b.addEventListener("click", function () { go(+b.dataset.go); });
  });

  /* ---------- catalog → clubs, plans, add-ons ---------- */
  api("/api/catalog").then(function (c) {
    CAT = c;
    $("#clubs").innerHTML = c.clubs.map(function (x, i) {
      var parts = x.split("—");
      return '<label class="opt' + (i ? "" : " sel") + '" data-v="' + x.replace(/"/g, "&quot;") + '"><span class="tick"></span>' +
        '<div class="nm">' + parts[0].trim() + '</div><div class="nt">' + (parts[1] || "").trim() + "</div></label>";
    }).join("");
    club = c.clubs[0];
    $("#plans").innerHTML = Object.keys(c.plans).map(function (k, i) {
      var v = c.plans[k];
      return '<label class="opt' + (i ? "" : " sel") + '" data-p="' + k + '"><span class="tick"></span>' +
        (v.badge ? '<span class="tag">' + v.badge + "</span>" : "") +
        '<div class="nm">' + v.name + "</div>" +
        '<div class="pr"><b>' + money(v.dues) + "</b> + tax every other Wednesday · " + money(v.startFee) + " to start</div>" +
        '<div class="nt">' + v.note + "</div></label>";
    }).join("");
    $("#addons").innerHTML = Object.keys(c.addons).map(function (k) {
      var v = c.addons[k];
      return '<label class="opt" data-a="' + k + '"><span class="tick"></span><div class="nm">' + v.name + "</div>" +
        '<div class="pr"><b>' + money(v.price) + "</b> · " + (v.oneTime ? "one-time" : "added to dues") + "</div></label>";
    }).join("");
    wire(); quoteNow();
  }).catch(function (e) {
    $("#clubs").innerHTML = '<div class="jn-note warn">We couldn\'t load membership options right now (' + e.message + '). Please try again in a moment or call (352) 377-4955.</div>';
  });

  function pick(sel, fn) {
    root.querySelectorAll(sel).forEach(function (e) {
      e.addEventListener("click", function () {
        root.querySelectorAll(sel).forEach(function (x) { x.classList.remove("sel"); });
        e.classList.add("sel"); fn(e);
      });
    });
  }
  function wire() {
    pick("[data-v]", function (e) { club = e.dataset.v; });
    pick("[data-p]", function (e) { plan = e.dataset.p; quoteNow(); });
    pick("#recChoice .opt", function (e) { mode = e.dataset.m; applyMode(); });
    root.querySelectorAll("[data-a]").forEach(function (e) {
      e.addEventListener("click", function () {
        e.classList.toggle("sel");
        addons = Array.prototype.map.call(root.querySelectorAll("[data-a].sel"), function (x) { return x.dataset.a; });
        quoteNow();
      });
    });
  }

  /* ---------- cart ---------- */
  var quoteSeq = 0;
  function quoteNow() {
    var seq = ++quoteSeq;   /* ignore responses that arrive out of order */
    api("/api/quote?plan=" + encodeURIComponent(plan) + "&addons=" + addons.join(",")).then(function (q) {
      if (seq !== quoteSeq) return;
      $("#cart").innerHTML =
        q.lines.map(function (l) { return '<div class="ln">' + l.label + "<b>" + money(l.amount) + "</b></div>"; }).join("") +
        '<div class="ln">Sales tax (' + (CAT.taxRate * 100).toFixed(0) + "%)<b>" + money(q.tax) + "</b></div>" +
        '<div class="tot"><span>Due today</span><span>' + money(q.dueToday) + "</span></div>" +
        '</div><div class="rec">Then <b>' + money(q.recurringWithTax) + "</b> every other Wednesday (includes tax).";
    }).catch(function () {});
  }

  /* ---------- step 3: details → member → step 4 ---------- */
  function validDetails() {
    var err = $("#detailsErr"), firstBad = null, msgs = {
      firstName: "your first name", lastName: "your last name", email: "a valid email address (name@example.com)", phone: "your mobile number"
    };
    root.querySelectorAll("#detailsForm input").forEach(function (i) {
      var ok = i.value.trim() && i.checkValidity();
      i.setAttribute("aria-invalid", ok ? "false" : "true");
      if (!ok && !firstBad) firstBad = i;
    });
    err.hidden = !firstBad;
    if (firstBad) { err.textContent = "Please enter " + msgs[firstBad.name] + " to continue."; firstBad.focus(); }
    return !firstBad;
  }
  root.querySelectorAll("#detailsForm input").forEach(function (i) {
    i.addEventListener("input", function () { i.setAttribute("aria-invalid", "false"); $("#detailsErr").hidden = true; });
  });
  $("#toPay").addEventListener("click", function () {
    if (!validDetails()) return;
    var btn = this; btn.disabled = true; $("#mOut").innerHTML = "";
    api("/api/member", { firstName: $("#firstName").value.trim(), lastName: $("#lastName").value.trim(),
      email: $("#email").value.trim(), phone: $("#phone").value.trim(), club: club, plan: plan, addons: addons })
    .then(function (m) {
      member = m;
      $("#ipay-account").value = $("#ipay-invoice").value = m.memberId;
      $("#ipay-first").value = m.firstName; $("#ipay-last").value = m.lastName;
      $("#ipay-email").value = m.email; $("#ipay-phone").value = m.phone || "";
      go(4); loadTerminal();
    })
    .catch(function (e) { $("#mOut").innerHTML = '<div class="jn-note warn">' + e.message + "</div>"; })
    .then(function () { btn.disabled = false; });
  });

  /* ---------- IntelliPay Lightbox (loaded at runtime from the join API) ---------- */
  function status(cls, msg) { $("#tstatus").innerHTML = cls ? '<span class="' + cls + '">' + msg + "</span>" : msg; }
  function injectTerminal(html) {
    var t = document.createElement("template"); t.innerHTML = html;
    Array.prototype.slice.call(t.content.querySelectorAll("script")).forEach(function (s) {
      var n = document.createElement("script");
      if (s.src) n.src = s.src; else n.textContent = s.textContent;
      s.parentNode.removeChild(s); document.head.appendChild(n);   /* innerHTML scripts never run — re-create them */
    });
    document.head.appendChild(t.content);
  }
  function loadTerminal() {
    if (terminalLoaded) { applyMode(); return; }
    status("", "Connecting to secure window…");
    fetch(API + "/api/terminal", { mode: "cors" }).then(function (r) {
      if (!r.ok) return r.json().then(function (j) { throw new Error(j.error || "terminal unavailable"); });
      return r.text();
    }).then(function (html) {
      injectTerminal(html);
      if (typeof intellipay === "undefined") throw new Error("Lightbox script did not load");
      if (!document.getElementById("intellipay-lightbox")) intellipay.initialize();   /* window.load already fired */
      terminalLoaded = true;
      intellipay.setStoreOnly(true);
      intellipay.runOnApproval(onVaulted);
      intellipay.runOnNonApproval(function (r) {
        $("#recOut").innerHTML = '<div class="jn-note warn">' + ((r && r.declinereason) || "That method could not be saved.") + " Please try another.</div>";
      });
      applyMode();
      var tries = 0, rv = setInterval(function () {
        tries++;
        if (intellipay.isReady) { clearInterval(rv); $("#vaultBtn").disabled = false; status("ok", "Secure window ready — nothing will be charged"); }
        else if (tries > 80) { clearInterval(rv); status("bad", "Secure window didn't respond. Reload and try again."); }
      }, 250);
    }).catch(function (e) { status("bad", "Secure window unavailable: " + e.message); });
  }

  /* Only these (field, property) pairs are read by IntelliPay's frame. */
  function brandLightbox(stage) {
    var set = function (f, fn, v) { try { intellipay[fn](f, v); } catch (e) {} };
    var today = stage === "today", ach = mode === "ACH";
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
    var ach = mode === "ACH";
    try { intellipay.setACHAvailable(ach); intellipay.setCCAvailable(!ach); } catch (e) {}
    brandLightbox("recurring");
    $("#vaultBtn").textContent = ach ? "Save bank account" : "Save payment method";
  }
  $("#vaultBtn").addEventListener("click", function () { if (typeof intellipay !== "undefined") intellipay.onSubmit(); });

  /* ---------- stage 1 done: token stored → step 5 ---------- */
  function onVaulted(resp) {
    api("/api/recurring-method", { memberId: member.memberId, custid: resp.custid, paymenttype: resp.paymenttype, methodhint: resp.methodhint })
    .then(function (r) {
      rec = r;
      $("#recOut").innerHTML = '<p class="jn-note"><span class="ok">Payment method saved.</span> <span class="jn-chip">' + r.method + '</span><span class="jn-chip">' + (r.hint || "") + "</span></p>";
      go(5); renderToday();
    })
    .catch(function (e) { $("#recOut").innerHTML = '<div class="jn-note warn">' + e.message + "</div>"; });
  }
  function renderToday() {
    var a = money(rec.dueToday);
    $("#todayBox").innerHTML = rec.canReuseForToday
      ? '<p class="jn-lede" style="margin:0 0 8px">One charge today, then you\'re set.</p><div class="big">' + a + "</div>" +
        '<label class="opt sel" style="margin-top:22px"><span class="tick"></span><div class="nm">Use the card I just saved</div>' +
        '<div class="nt">' + (rec.hint || "Saved card") + " — one tap, nothing to re-enter.</div></label>" +
        '<button class="jn-btn" type="button" id="payNow">Pay ' + a + "</button>"
      : '<p class="jn-lede" style="margin:0 0 8px">One charge today, then your dues draft from your bank.</p><div class="big">' + a + "</div>" +
        '<div class="jn-note warn">Your dues will draft from your <b>bank account</b>. We don\'t accept bank draft for the up-front payment — please add a credit or debit card for today\'s total.</div>' +
        '<button class="jn-btn" type="button" id="payCard">Add card &amp; pay ' + a + "</button>";
    var b = $("#payNow") || $("#payCard");
    b.addEventListener("click", rec.canReuseForToday ? payWithSaved : payWithNewCard);
  }
  function payWithSaved() {
    this.disabled = true; $("#payOut").innerHTML = '<p class="lock">Processing…</p>';
    api("/api/charge-today", { memberId: member.memberId })
      .then(function (o) { finish(o, o.approved ? "Charged to your saved card" : "Submitted"); })
      .catch(function (e) { $("#payOut").innerHTML = '<div class="jn-note warn">' + e.message + "</div>"; $("#payNow").disabled = false; });
  }
  function payWithNewCard() {
    intellipay.setStoreOnly(false);
    intellipay.setACHAvailable(false); intellipay.setCCAvailable(true);
    brandLightbox("today");
    $("#ipay-amount").value = Number(rec.dueToday).toFixed(2);
    intellipay.runOnApproval(function (resp) {
      api("/api/today-card", { memberId: member.memberId, custid: resp.custid, methodhint: resp.methodhint,
        status: resp.status, approved: resp.response === "A", amount: rec.dueToday })
      .then(function (o) { finish(o, "Paid with your card"); });
    });
    intellipay.onSubmit();
  }

  /* ---------- done ---------- */
  function finish(o, label) {
    go(6);
    $("#done").innerHTML =
      '<p class="jn-lede" style="margin-top:0">' + label + ". Your membership is active — see you at the club.</p>" +
      '<div style="margin-top:18px">' +
      '<span class="jn-chip">Member ID <b>' + member.memberId + "</b></span>" +
      '<span class="jn-chip">Paid today <b>' + money(rec.dueToday) + "</b></span>" +
      '<span class="jn-chip">Dues from <b>' + (rec.hint || rec.method) + "</b></span></div>" +
      '<div class="jn-note">Your dues draft automatically every other Wednesday. No card or bank number is stored by GHF.</div>';
  }
})();
