/* GHF Coach — Claude-powered concierge */
(function () {
  "use strict";

  var CFG = window.GHF_CHAT || {};
  var MODEL = CFG.model || "claude-sonnet-4-6";

  var SYSTEM = [
    "You are GHF Coach, the friendly AI concierge for Gainesville Health & Fitness (GHF) — ghfc.com, Gainesville, Florida's premier gym for 45 years. You live on their website.",
    "Voice: warm, encouraging, concise. A knowledgeable front-desk pro, not a salesperson. Use short paragraphs. 'You're going to feel good here' is the brand promise.",
    "FACTS:",
    "- 3 locations, one membership: GHF Main (4820 W Newberry Road, Gainesville — open 24/7, (352) 377-4955, GM Adrian Antigua), GHF Women (2441 NW 43rd Street — women only, M-Th 5am-9pm, Fri 5am-8pm, Sat 8am-6pm, Sun closed, (352) 374-4634, Mgr Jordan Heitzler), GHF Tioga (12830 SW 1st Lane, Newberry — family friendly, M-Th 5am-10pm, Fri 5am-9pm, Sat 8am-8pm, Sun 10am-5pm, (352) 692-2180, Mgr Wrenn Klettner).",
    "- Pricing (join online): all plans are $29.99 + tax with dues every other Wednesday, no maintenance fee. 24 Month Agreement (Best Value): after the initial 24 months dues drop to $20.99 + tax, starting fee $49.00. 12 Month Agreement: after 12 months remains $29.99 + tax and renews month-to-month, starting fee $49.00. Month To Month Agreement: cancel with 30 day notice, starting fee $149.00 + tax. Family pricing for spouses + children 13-21. Join online at join.html or get pricing at contact.html. Minimum age 13 with parent approval. Marketing equivalent: 'as little as $15-16 per week.'",
    "- Included in every membership: 24/7 access at Main, staff help every visit (Blue Shirt Service), 900+ group classes monthly, free hot yoga, indoor heated lap pool + warm therapy pool + cold plunge, sauna/steam/hot tub, Kid's Club free babysitting (ages 6wk-12yr, 2 hrs/day), indoor basketball/volleyball, largest free weight area in North Central Florida, member savings at 100+ local businesses.",
    "- NOT included (premier, extra fee): Personal Training, CrossFit, Pilates, TRIBE Team Training, X-Force Body, ReQuest Physical Therapy.",
    "- Kid's Club hours: Main M-F 8a-1p & 3p-8:30p, Sat 8a-2p, Sun 10a-5p. Tioga M-F 8a-1p & 3p-8p, Sat 8a-3p, Sun 10a-5p. Women M-Th 8a-1p & 3p-8p, Fri 8a-1p & 3p-7p, Sat 8a-1p, Sun closed.",
    "- Hot yoga: largest studio in the area, three temps (85° yin, 95° flow, 105° hot), included in membership, bring mat + towel, capacity 30.",
    "- Guests: free all-access day pass for first-timers; members can bring guests — each guest gets 6 free visits (2 guests at a time, age 13+, photo ID).",
    "- Programs: TRIBE (8-week small team seasons: PUNCH, FitSTRONG, CORE, LIFE), X-Force Body (2x25min/week negative training fat loss, 6 weeks), CrossFit at Tioga (open to non-members, free trial week, youth 6-12, Olympic lifting M/W 5:30p), Pilates (Reformer/Tower/Chair, studios at Main & Tioga, first session free), Personal Training (40 certified trainers, free assessment w/ InBody 570), Club Seniors (Sit To Be Fit), FIT for ALL (free special-needs program, M-F 3-4p at Main), recovery (Aquix pool/spa, hydro massage Chill Studio, J-Bar smoothies).",
    "RULES: Answer only about GHF, fitness, and visiting the club. Link pages with markdown like [Join Online](join.html), [Get Pricing](contact.html), [Classes](group-fitness.html), [Hot Yoga](hot-yoga.html), [Kid's Club](kids-club.html), [Locations](locations.html), [Pilates](pilates.html), [CrossFit](crossfit.html), [Personal Training](personal-training.html). If unsure or asked about billing/account specifics, suggest calling (352) 377-4955 or memberservices@ghfc.com. Keep answers under 120 words unless asked for detail. End with a helpful next step when natural."
  ].join("\n");

  var MARK = '<svg viewBox="0 0 64 64" fill="none"><circle cx="32" cy="13" r="7" fill="currentColor"/><path d="M13 24 L32 37 L51 24" stroke="currentColor" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><path d="M32 37 L32 56" stroke="currentColor" stroke-width="8" stroke-linecap="round"/></svg>';

  var CHIPS = [
    "What's included in membership?",
    "How much does it cost?",
    "Kid's Club hours?",
    "Can I try GHF for free?",
    "Tell me about hot yoga"
  ];

  /* ---------- build DOM ---------- */
  var root = document.createElement("div");
  root.innerHTML =
    '<button class="chat-orb" aria-label="Chat with GHF Coach">' + MARK + "</button>" +
    '<div class="chat-orb__hint" role="button" tabindex="0">' +
    '  <span class="chat-orb__hint-avatar">' + MARK + "</span>" +
    '  <span class="chat-orb__hint-text"><em>Have questions?</em> I\'m here to help.</span>' +
    '  <button class="chat-orb__hint-x" aria-label="Dismiss">✕</button>' +
    "</div>" +
    '<div class="chat-panel" role="dialog" aria-label="GHF Coach chat">' +
    '  <div class="chat-head">' +
    '    <div class="chat-head__icon">' + MARK + "</div>" +
    '    <div><div class="chat-head__name">GHF Coach</div><div class="chat-head__sub">AI Concierge · Powered by Claude</div></div>' +
    '    <button class="chat-head__close" aria-label="Close chat">✕</button>' +
    "  </div>" +
    '  <div class="chat-msgs"></div>' +
    '  <div class="chat-input">' +
    '    <textarea rows="1" placeholder="Ask about classes, pricing, hours…" aria-label="Message"></textarea>' +
    '    <button class="chat-send" aria-label="Send">→</button>' +
    "  </div>" +
    '  <div class="chat-note">GHF Coach is an AI assistant — for account questions call (352) 377-4955.</div>' +
    "</div>";
  document.body.appendChild(root);

  var orb = root.querySelector(".chat-orb");
  var hint = root.querySelector(".chat-orb__hint");
  var msgs = root.querySelector(".chat-msgs");
  var input = root.querySelector(".chat-input textarea");
  var sendBtn = root.querySelector(".chat-send");
  var history = [];
  try { history = JSON.parse(sessionStorage.getItem("ghf-chat") || "[]"); } catch (e) {}

  /* activation link: visiting any page with #ck=<api-key> stores the key in
     this browser and cleans the URL — the key never lives in the repo */
  try {
    var ckm = location.hash.match(/[#&]ck=([^&]+)/);
    if (ckm) {
      localStorage.setItem("ghf-anthropic-key", decodeURIComponent(ckm[1]));
      history_replace_safe();
    }
  } catch (e) {}
  function history_replace_safe() {
    try { window.history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
  }

  function getKey() {
    if (CFG.proxyUrl) return "proxy"; /* key lives server-side; nothing needed here */
    if (CFG.apiKey) return CFG.apiKey;
    try { return localStorage.getItem("ghf-anthropic-key") || ""; } catch (e) { return ""; }
  }

  /* ---------- rendering ---------- */
  function md(t) {
    t = t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    t = t.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    var blocks = t.split(/\n{2,}/).map(function (b) {
      var lines = b.split("\n");
      var items = lines.filter(function (l) { return /^\s*[-•]\s+/.test(l); });
      if (items.length && items.length === lines.length) {
        return "<ul>" + items.map(function (l) { return "<li>" + l.replace(/^\s*[-•]\s+/, "") + "</li>"; }).join("") + "</ul>";
      }
      return "<p>" + b.replace(/\n/g, "<br>") + "</p>";
    });
    return blocks.join("");
  }

  function addMsg(role, html) {
    var d = document.createElement("div");
    d.className = "chat-msg chat-msg--" + (role === "user" ? "user" : "ai");
    d.innerHTML = role === "user" ? html.replace(/</g, "&lt;") : html;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
    return d;
  }

  function welcome() {
    var w = document.createElement("div");
    w.className = "chat-welcome";
    w.innerHTML = "<h3>What can we help you crush today?</h3><p>Classes, pricing, hours, programs — ask me anything about GHF.</p>" +
      '<div class="chat-chips">' + CHIPS.map(function (c) { return "<button>" + c + "</button>"; }).join("") + "</div>";
    msgs.appendChild(w);
    w.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () { input.value = b.textContent; send(); });
    });
  }

  function keyGate() {
    var g = document.createElement("div");
    g.className = "chat-gate";
    g.innerHTML = "<p><strong>One-time setup:</strong> paste your Anthropic API key to activate GHF Coach. It's stored only in this browser.</p>" +
      '<input type="password" placeholder="sk-ant-…" aria-label="Anthropic API key">' +
      '<button class="btn btn--solid btn--sm">Activate Coach →</button>';
    msgs.appendChild(g);
    g.querySelector("button").addEventListener("click", function () {
      var v = g.querySelector("input").value.trim();
      if (!v) return;
      try { localStorage.setItem("ghf-anthropic-key", v); } catch (e) {}
      g.remove();
      addMsg("ai", "<p>All set! Ask me anything about GHF. 💪</p>");
    });
  }

  function restore() {
    if (!history.length) { welcome(); }
    else history.forEach(function (m) { addMsg(m.role, m.role === "user" ? m.content : md(m.content)); });
    if (!getKey()) keyGate();
  }

  /* ---------- Claude call (streaming) ---------- */
  function send() {
    var text = input.value.trim();
    if (!text) return;
    if (!getKey()) { keyGate(); return; }
    input.value = "";
    var wEl = msgs.querySelector(".chat-welcome");
    if (wEl) wEl.remove();
    addMsg("user", text);
    history.push({ role: "user", content: text });
    sendBtn.disabled = true;

    var typing = document.createElement("div");
    typing.className = "chat-typing";
    typing.innerHTML = "<i></i><i></i><i></i>";
    msgs.appendChild(typing);
    msgs.scrollTop = msgs.scrollHeight;

    var aiEl = null;
    var full = "";

    var apiUrl = CFG.proxyUrl || "https://api.anthropic.com/v1/messages";
    var apiHeaders = { "content-type": "application/json" };
    if (!CFG.proxyUrl) {
      apiHeaders["x-api-key"] = getKey();
      apiHeaders["anthropic-version"] = "2023-06-01";
      apiHeaders["anthropic-dangerous-direct-browser-access"] = "true";
    }
    fetch(apiUrl, {
      method: "POST",
      headers: apiHeaders,
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 700,
        system: SYSTEM,
        messages: history.slice(-12),
        stream: true
      })
    }).then(function (res) {
      if (!res.ok) return res.text().then(function (t) { throw new Error("API " + res.status + ": " + t.slice(0, 200)); });
      var reader = res.body.getReader();
      var dec = new TextDecoder();
      var buf = "";
      function pump() {
        return reader.read().then(function (r) {
          if (r.done) return;
          buf += dec.decode(r.value, { stream: true });
          var lines = buf.split("\n");
          buf = lines.pop();
          lines.forEach(function (ln) {
            if (ln.indexOf("data: ") !== 0) return;
            try {
              var ev = JSON.parse(ln.slice(6));
              if (ev.type === "content_block_delta" && ev.delta && ev.delta.text) {
                if (!aiEl) { typing.remove(); aiEl = addMsg("ai", ""); }
                full += ev.delta.text;
                aiEl.innerHTML = md(full);
                msgs.scrollTop = msgs.scrollHeight;
              }
            } catch (e) {}
          });
          return pump();
        });
      }
      return pump();
    }).then(function () {
      if (typing.parentNode) typing.remove();
      if (full) {
        history.push({ role: "assistant", content: full });
        try { sessionStorage.setItem("ghf-chat", JSON.stringify(history.slice(-20))); } catch (e) {}
      }
    }).catch(function (err) {
      if (typing.parentNode) typing.remove();
      var isAuth = /401|403/.test(err.message);
      if (isAuth) { try { localStorage.removeItem("ghf-anthropic-key"); } catch (e) {} }
      addMsg("ai", "<p>" + (isAuth
        ? "That API key didn't work — let's try again."
        : "I'm having trouble connecting right now. You can always reach the team at <a href='tel:3523774955'>(352) 377-4955</a>.") + "</p>");
      if (isAuth) keyGate();
      history.pop();
    }).finally(function () {
      sendBtn.disabled = false;
      input.focus();
    });
  }

  /* ---------- events ---------- */
  function openChat() {
    document.body.classList.add("chat-open");
    hint.classList.remove("is-on");
    if (!msgs.children.length) restore();
    setTimeout(function () { input.focus(); }, 400);
  }
  orb.addEventListener("click", openChat);
  /* clicking the popup bubble opens the chat too */
  hint.addEventListener("click", function (e) {
    if (e.target.closest(".chat-orb__hint-x")) return;
    openChat();
  });
  hint.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openChat(); }
  });
  hint.querySelector(".chat-orb__hint-x").addEventListener("click", function (e) {
    e.stopPropagation();
    hint.classList.remove("is-on");
    try { sessionStorage.setItem("ghf-chat-hint", "1"); } catch (er) {}
  });
  root.querySelector(".chat-head__close").addEventListener("click", function () {
    document.body.classList.remove("chat-open");
  });
  sendBtn.addEventListener("click", send);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  });
  input.addEventListener("input", function () {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 110) + "px";
  });

  /* teaser popup, once per session — appears shortly after load, lingers */
  try {
    if (!sessionStorage.getItem("ghf-chat-hint")) {
      setTimeout(function () {
        if (!document.body.classList.contains("chat-open")) hint.classList.add("is-on");
      }, 3500);
      setTimeout(function () {
        hint.classList.remove("is-on");
        try { sessionStorage.setItem("ghf-chat-hint", "1"); } catch (er) {}
      }, 16000);
    }
  } catch (e) {}
})();
