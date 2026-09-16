/* GHF — Join Online (cart-style module + IntelliPay Lightbox, two-stage payment)
 *
 *  01 Details → 02 Home club → 03 Membership → 04 Due today (charge) → done
 *  The card that pays today is registered as the recurring method too; the member can
 *  swap it for another card or ACH on the success screen.
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
    [1, 2, 3, 4, 5].forEach(function (i) { var c = $("#c" + i); if (c) c.classList.toggle("hide", i !== n); });
    [1, 2, 3, 4].forEach(function (i) { var e = $("#s" + i); if (e) e.className = "rl" + (i < n ? " done" : i === n ? " on" : ""); });
    if (modal) modal.scrollTo({ top: 0, behavior: "smooth" });
    else window.scrollTo({ top: Math.max(0, root.getBoundingClientRect().top + window.scrollY - 80), behavior: "smooth" });
  }

  /* ---------- pop-out: the module opens as a takeover from "Start My Membership" / join.html#start ---------- */
  var modal = document.getElementById("joinModal"), lastFocus = null;
  function openJoin() {
    if (!modal || !modal.hidden) return;
    lastFocus = document.activeElement;
    modal.hidden = false; modal.classList.add("is-open"); document.body.classList.add("jn-open");
    modal.scrollTop = 0;
    var close = modal.querySelector("[data-join-close]"); if (close) close.focus();
    if (location.hash !== "#start") history.replaceState(null, "", "#start");
  }
  function closeJoin() {
    if (!modal || modal.hidden) return;
    modal.hidden = true; modal.classList.remove("is-open"); document.body.classList.remove("jn-open");
    if (location.hash === "#start") history.replaceState(null, "", location.pathname + location.search);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  if (modal) {
    document.addEventListener("click", function (e) {
      var a = e.target.closest("a[href$='#start'], a[href$='#wizard'], [data-join-open]");
      if (a) { e.preventDefault(); openJoin(); return; }
      if (e.target.closest("[data-join-close]")) { e.preventDefault(); closeJoin(); }
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeJoin(); });
    if (location.hash === "#start" || location.hash === "#wizard") openJoin();
    window.addEventListener("hashchange", function () { if (location.hash === "#start") openJoin(); });
  }
  root.querySelectorAll("[data-go]").forEach(function (b) {
    b.addEventListener("click", function () { go(+b.dataset.go); });
  });

  /* ---------- plan cards ---------- */
  /* The badge and the value copy are decided HERE, not taken from the catalog. The live
     site reads its catalog from the deployed API, so anything driven by a server field
     (v.badge, which still says "MOST FLEXIBLE") would need that service redeployed before
     it could change. Deciding it client-side means this ships with the static site.
     Every figure below is derived from prices in the catalog — none is retyped, so a card
     cannot drift from what the cart actually charges. */
  var BEST = "24mo";
  var DRAFTS_PER_YEAR = 26;   /* dues draft every other Wednesday */

  function win(t) { return "<li>" + t + "</li>"; }
  function saving(n) { return n % 1 === 0 ? "$" + n : money(n); }

  function planCard(k, v, all) {
    var feat = k === BEST;
    var dearest = 0;
    Object.keys(all).forEach(function (x) { if (all[x].startFee > dearest) dearest = all[x].startFee; });

    /* the struck anchor only appears when another plan genuinely costs more to start */
    var start = (feat && dearest > v.startFee)
      ? '<s>' + money(dearest) + "</s> " + money(v.startFee) + " to start"
      : money(v.startFee) + " to start";

    var body = '<div class="nm">' + v.name + "</div>" +
      '<div class="pr"><b>' + money(v.dues) + "</b> + tax every other Wednesday · " + start + "</div>";

    if (!feat) {
      return '<label class="opt" data-p="' + k + '" role="radio" tabindex="0" aria-checked="false">' +
        '<span class="tick"></span>' + body + '<div class="nt">' + v.note + "</div></label>";
    }

    var wins = "";
    if (dearest > v.startFee) wins += win("Save <b>" + saving(dearest - v.startFee) + "</b> today versus month-to-month");
    if (v.note) wins += win(v.note);
    /* rendered only when the catalog carries the structured figure, so the saving is
       never a number typed in by hand */
    if (v.afterDues && v.afterDues < v.dues)
      wins += win("That’s about <b>" + saving(Math.round((v.dues - v.afterDues) * DRAFTS_PER_YEAR * 100) / 100) + " a year</b> you keep, for good");
    wins += win("No maintenance fee, ever");

    return '<label class="opt opt--feat" data-p="' + k + '" role="radio" tabindex="0" aria-checked="false">' +
      '<div class="opt__flag">Best value — most members choose</div>' +
      '<span class="tick"></span>' + body +
      '<ul class="opt__wins">' + wins + "</ul></label>";
  }

  /* ---------- catalog → clubs, plans, add-ons ---------- */
  api("/api/catalog").then(function (c) {
    CAT = c;
    $("#clubs").innerHTML = c.clubs.map(function (x, i) {
      var parts = x.split("—");
      return '<label class="opt' + (i ? "" : " sel") + '" data-v="' + x.replace(/"/g, "&quot;") + '"><span class="tick"></span>' +
        '<div class="nm">' + parts[0].trim() + '</div><div class="nt">' + (parts[1] || "").trim() + "</div></label>";
    }).join("");
    club = c.clubs[0];
    $("#plans").innerHTML = Object.keys(c.plans).map(function (k) {
      return planCard(k, c.plans[k], c.plans);
    }).join("");
    /* add-ons are intentionally not offered in the join flow — three plans only.
       They remain in the server catalog for later use. */
    wire();   /* no quoteNow() here — the cart stays hidden until a plan is picked */
  }).catch(function (e) {
    $("#clubs").innerHTML = '<div class="jn-note warn">We couldn\'t load membership options right now (' + e.message + '). Please try again in a moment or call (352) 377-4955.</div>';
  });

  function pick(sel, fn) {
    root.querySelectorAll(sel).forEach(function (e) {
      function choose() {
        root.querySelectorAll(sel).forEach(function (x) {
          x.classList.remove("sel");
          if (x.hasAttribute("aria-checked")) x.setAttribute("aria-checked", "false");
        });
        e.classList.add("sel");
        if (e.hasAttribute("aria-checked")) e.setAttribute("aria-checked", "true");
        fn(e);
      }
      e.addEventListener("click", choose);
      /* the options are labels with no input behind them, so without this the step that
         takes payment cannot be operated from the keyboard at all */
      e.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " " || ev.key === "Spacebar") { ev.preventDefault(); choose(); }
      });
    });
  }
  function wire() {
    pick("[data-v]", function (e) { club = e.dataset.v; });
    pick("[data-p]", function (e) { plan = e.dataset.p; planChosen = true; $("#mOut").innerHTML = ""; quoteNow(); });
  }

  /* ---------- cart ---------- */
  var planChosen = false, terminalReady = false;
  var quoteSeq = 0;
  function quoteNow() {
    var seq = ++quoteSeq;   /* ignore responses that arrive out of order */
    if (!planChosen) return;          /* nothing to show until step 3 is answered */
    api("/api/quote?plan=" + encodeURIComponent(plan) + "&addons=").then(function (q) {
      if (seq !== quoteSeq) return;
      $("#cartSide").hidden = false;
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
  /* step 1: details are only validated here — /api/member needs plan and club, which
     are not known until step 3, so the member record is created there instead. */
  $("#toClub").addEventListener("click", function () {
    if (!validDetails()) return;
    go(2);
  });

  /* step 3: plan and club are both known — create the member, then go and take payment */
  $("#toPay").addEventListener("click", function () {
    if (!planChosen) {
      $("#mOut").innerHTML = '<div class="jn-note warn">Please choose a membership to continue.</div>';
      return;
    }
    var btn = this; btn.disabled = true; $("#mOut").innerHTML = "";
    api("/api/member", { firstName: $("#firstName").value.trim(), lastName: $("#lastName").value.trim(),
      email: $("#email").value.trim(), phone: $("#phone").value.trim(), club: club, plan: plan, addons: [] })
    .then(function (m) {
      member = m;
      $("#ipay-account").value = $("#ipay-invoice").value = m.memberId;
      $("#ipay-first").value = m.firstName; $("#ipay-last").value = m.lastName;
      $("#ipay-email").value = m.email; $("#ipay-phone").value = m.phone || "";
      rec = { dueToday: m.dueToday };
      go(4); renderToday(); loadTerminal();
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
    if (terminalLoaded) { armCharge(); return; }
    status("", "Connecting to secure window\u2026");
    fetch(API + "/api/terminal", { mode: "cors" }).then(function (r) {
      if (!r.ok) return r.json().then(function (j) { throw new Error(j.error || "terminal unavailable"); });
      return r.text();
    }).then(function (html) {
      injectTerminal(html);
      if (typeof intellipay === "undefined") throw new Error("Lightbox script did not load");
      if (!document.getElementById("intellipay-lightbox")) intellipay.initialize();
      terminalLoaded = true;
      armCharge();
      var tries = 0, rv = setInterval(function () {
        tries++;
        if (intellipay.isReady) { clearInterval(rv); terminalReady = true; syncPayBtn(); }
        else if (tries > 80) { clearInterval(rv); status("bad", "Secure window didn't respond. Reload and try again."); }
      }, 250);
    }).catch(function (e) { status("bad", "Secure window unavailable: " + e.message); });
  }

  /* Only these (field, property) pairs are read by IntelliPay's frame. */
  function brandLightbox(stage) {
    var set = function (f, fn, v) { try { intellipay[fn](f, v); } catch (e) {} };
    var today = stage === "today", ach = mode === "ACH";
    set("header", "setItemBackgroundColor", "#005898"); set("header", "setItemColor", "#ffffff");
    set("header", "setItemLabel", today ? "Pay today's total" : (ach ? "Set up your bank draft" : "Change your dues card"));
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
    set("successmessage", "setItemLabel", today ? "Payment received \u2014 welcome to GHF." : "Saved \u2014 nothing was charged.");
    set("declinemessage", "setItemLabel", "We couldn't process that. Please check the details or try another card.");
  }

  /* ---------- step 4: one card, charged today AND kept for dues ---------- */
  function armCharge() {
    if (typeof intellipay === "undefined" || !terminalLoaded) return;
    /* coming back to this step must not leave Pay stuck disabled: the readiness
       poll only runs on first load, so re-check the flag here too. */
    if (intellipay.isReady) { terminalReady = true; syncPayBtn(); }
    try { intellipay.setStoreOnly(false); intellipay.setACHAvailable(false); intellipay.setCCAvailable(true); } catch (e) {}
    $("#ipay-amount").value = Number(rec.dueToday).toFixed(2);
    brandLightbox("today");
    intellipay.runOnApproval(onPaid);
    intellipay.runOnNonApproval(function (r) {
      $("#payOut").innerHTML = '<div class="jn-note warn">' + ((r && r.declinereason) || "That card was declined.") + " Please try another.</div>";
      syncPayBtn();
    });
  }

  function syncPayBtn() {
    var b = $("#payNow"), ack = $("#ackDues");
    if (!b) return;
    var acked = !!(ack && ack.checked);
    b.disabled = !(terminalReady && acked);
    /* a greyed button next to "Secure window ready" reads as broken — say which of
       the two conditions is actually missing. */
    if (terminalReady) status(acked ? "ok" : "", acked ? "Secure window ready"
      : "Tick the box above to enable payment.");
  }

  function renderToday() {
    var a = money(rec.dueToday), r = money(member.recurringWithTax);
    $("#todayBox").innerHTML =
      '<p class="jn-lede" style="margin:0 0 8px">One charge today, then you\'re set.</p>' +
      '<div class="big">' + a + "</div>" +
      '<div class="jn-note"><b>This same card becomes your recurring dues method.</b> Your dues draft ' +
      r + ' every other Wednesday from the card you pay with now. ' +
      'You can switch it to a different card or your bank account on the next screen.</div>' +
      '<label class="ack" for="ackDues"><input type="checkbox" id="ackDues">' +
      '<span>I understand that after today\'s ' + a + ', my dues of <b>' + r + '</b> will be charged ' +
      'automatically every other Wednesday to this same payment method until I cancel.</span></label>' +
      '<button class="jn-btn" type="button" id="payNow" disabled>Pay ' + a + "</button>";
    $("#ackDues").addEventListener("change", syncPayBtn);
    $("#payNow").addEventListener("click", function () {
      if (this.disabled) return;
      this.disabled = true; $("#payOut").innerHTML = '<p class="lock">Opening secure window\u2026</p>';
      if (typeof intellipay !== "undefined") intellipay.onSubmit();
    });
    syncPayBtn();
  }

  /* The card that paid today is ALSO registered as the recurring method. Both calls matter:
     /api/export skips any member without recurring.token, so recording only the payment
     would enrol someone who then never gets billed. */
  function onPaid(resp) {
    $("#payOut").innerHTML = '<p class="lock">Confirming\u2026</p>';
    api("/api/today-card", { memberId: member.memberId, custid: resp.custid, methodhint: resp.methodhint,
      status: resp.status, approved: resp.response === "A", amount: rec.dueToday })
    .then(function () {
      return api("/api/recurring-method", { memberId: member.memberId, custid: resp.custid,
        paymenttype: resp.paymenttype || "C", methodhint: resp.methodhint });
    })
    .then(function (r) { rec = r; finish("Paid with your card"); })
    .catch(function (e) { $("#payOut").innerHTML = '<div class="jn-note warn">' + e.message + "</div>"; });
  }

  /* ---------- after joining: swap the dues method ---------- */
  function armRecurringChange() {
    if (typeof intellipay === "undefined" || !terminalLoaded) return;
    try { intellipay.setStoreOnly(true); intellipay.setACHAvailable(true); intellipay.setCCAvailable(true); } catch (e) {}
    brandLightbox("recurring");
    intellipay.runOnApproval(function (resp) {
      api("/api/recurring-method", { memberId: member.memberId, custid: resp.custid,
        paymenttype: resp.paymenttype, methodhint: resp.methodhint })
      .then(function (r) {
        rec = r;
        $("#recLine").innerHTML = "Dues will draft from <b>" + (r.hint || r.method) + "</b>, " +
          money(member.recurringWithTax) + " every other Wednesday.";
        $("#recOut").innerHTML = '<p class="jn-note"><span class="ok">Updated.</span> Nothing was charged.</p>';
      })
      .catch(function (e) { $("#recOut").innerHTML = '<div class="jn-note warn">' + e.message + "</div>"; });
    });
    intellipay.runOnNonApproval(function (r) {
      $("#recOut").innerHTML = '<div class="jn-note warn">' + ((r && r.declinereason) || "That method could not be saved.") + "</div>";
    });
  }

  /* ---------- done ---------- */
  function finish(label) {
    go(5);
    $("#done").innerHTML =
      '<p class="jn-lede" style="margin-top:0">' + label + ". Your membership is active \u2014 see you at the club.</p>" +
      '<div style="margin-top:18px">' +
      '<span class="jn-chip">Member ID <b>' + member.memberId + "</b></span>" +
      '<span class="jn-chip">Paid today <b>' + money(rec.dueToday) + "</b></span></div>" +
      '<div class="jn-note">No card or bank number is stored by GHF.</div>';
    $("#recLine").innerHTML = "Dues will draft from <b>" + (rec.hint || rec.method || "the card you just used") +
      "</b>, " + money(member.recurringWithTax) + " every other Wednesday.";
    $("#changeRec").hidden = false;
    $("#changeRecBtn").addEventListener("click", function () {
      $("#recOut").innerHTML = '<p class="lock">Opening secure window\u2026</p>';
      armRecurringChange();
      if (typeof intellipay !== "undefined") intellipay.onSubmit();
    });
  }
})();
