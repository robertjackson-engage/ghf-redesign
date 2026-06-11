/* GHF — Join Online wizard */
(function () {
  "use strict";

  var wizard = document.querySelector(".join");
  if (!wizard) return;

  var state = { loc: null, locImg: "", type: "Individual", plan: null, fee: null, note: "", first: "", last: "", email: "", phone: "" };
  var INCLUDES_NOTE = "Every membership includes all 900+ monthly classes, hot yoga, pools & spa, Kid's Club, and access to all three locations.";
  var step = 1;
  var TOTAL = 4;

  var stepsEls = wizard.querySelectorAll(".join-step");
  var navItems = wizard.querySelectorAll(".join__steps-nav li");
  var barFill = wizard.querySelector(".join__progress-bar i");
  var backBtn = wizard.querySelector(".join__nav-row .back");
  var nextBtn = wizard.querySelector(".join__nav-row .next");
  var countEl = wizard.querySelector(".join__count");

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
    if (n === 4) {
      var agree = wizard.querySelector("#agree");
      return agree && agree.checked;
    }
    return true;
  }

  function refreshNext() {
    if (step === 1) nextBtn.disabled = !state.loc;
    else if (step === 2) nextBtn.disabled = !state.plan;
    else if (step === 4) nextBtn.disabled = !wizard.querySelector("#agree").checked;
    else nextBtn.disabled = false;
    nextBtn.querySelector(".lbl").textContent = step === TOTAL ? "Complete My Join" : "Continue";
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
    backBtn.classList.toggle("is-visible", n > 1);
    countEl.textContent = "Step 0" + n + " / 0" + TOTAL;
    if (n === 4) renderReview();
    refreshNext();
    var top = wizard.getBoundingClientRect().top + window.scrollY - 90;
    if (window.scrollY > top) window.scrollTo({ top: top, behavior: "smooth" });
  }

  /* selections */
  wizard.querySelectorAll('[data-step="1"] .choice').forEach(function (c) {
    c.addEventListener("click", function () {
      wizard.querySelectorAll('[data-step="1"] .choice').forEach(function (x) { x.classList.remove("is-selected"); });
      c.classList.add("is-selected");
      state.loc = c.dataset.name;
      state.locImg = c.dataset.img;
      updateSummary(); refreshNext();
      setTimeout(function () { goStep(2); }, 420);
    });
  });
  wizard.querySelectorAll('[data-step="2"] .choice').forEach(function (c) {
    c.addEventListener("click", function () {
      wizard.querySelectorAll('[data-step="2"] .choice').forEach(function (x) { x.classList.remove("is-selected"); });
      c.classList.add("is-selected");
      state.plan = c.dataset.name;
      state.fee = c.dataset.fee;
      state.note = c.dataset.note || "";
      updateSummary(); refreshNext();
      setTimeout(function () { goStep(3); }, 420);
    });
  });
  wizard.querySelectorAll(".seg button").forEach(function (b) {
    b.addEventListener("click", function () {
      wizard.querySelectorAll(".seg button").forEach(function (x) { x.classList.remove("is-on"); });
      b.classList.add("is-on");
      state.type = b.dataset.type;
      updateSummary();
    });
  });
  wizard.querySelectorAll('[data-step="3"] input').forEach(function (i) {
    i.addEventListener("input", function () {
      state[i.name] = i.value.trim();
      updateSummary();
    });
  });

  /* summary */
  function updateSummary() {
    var set = function (key, val) {
      var dd = wizard.querySelector('[data-sum="' + key + '"]');
      if (!dd) return;
      dd.textContent = val || "—";
      dd.classList.toggle("empty", !val);
    };
    set("loc", state.loc);
    set("type", state.type);
    set("plan", state.plan);
    set("fee", state.fee);
    set("name", (state.first || state.last) ? (state.first + " " + state.last).trim() : "");
    var note = wizard.querySelector("[data-sum-note]");
    if (note) note.textContent = state.note ? state.note + " " + INCLUDES_NOTE : INCLUDES_NOTE;
  }

  function renderReview() {
    var list = wizard.querySelector("#reviewList");
    var rows = [
      ["Home club", state.loc],
      ["Membership", state.type],
      ["Plan", state.plan + " — $29.99 + tax, dues every other Wednesday"],
      ["Starting fee", state.fee],
      ["Name", (state.first + " " + state.last).trim()],
      ["Email", state.email],
      ["Phone", state.phone],
    ];
    list.innerHTML = rows.map(function (r) {
      return '<div class="sum-row"><dt>' + r[0] + "</dt><dd>" + (r[1] || "—") + "</dd></div>";
    }).join("");
  }

  /* nav buttons */
  backBtn.addEventListener("click", function () { goStep(step - 1); });
  nextBtn.addEventListener("click", function () {
    if (!canLeave(step)) { refreshNext(); return; }
    if (step < TOTAL) { goStep(step + 1); return; }
    /* finish */
    var success = document.querySelector(".join-success");
    var nameEl = success.querySelector("[data-success-name]");
    if (nameEl && state.first) nameEl.textContent = state.first + ", you're going to feel good here.";
    success.classList.add("is-open");
    document.body.style.overflow = "hidden";
  });
  var agreeBox = wizard.querySelector("#agree");
  if (agreeBox) agreeBox.addEventListener("change", refreshNext);

  updateSummary();
  refreshNext();
})();
