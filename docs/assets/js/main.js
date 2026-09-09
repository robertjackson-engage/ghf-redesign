/* GHF — interactions */
(function () {
  "use strict";

  var docEl = document.documentElement;
  docEl.classList.add("js");

  /* ---------- preloader intro sequencing ---------- */
  var pre = document.querySelector(".preloader");
  var skipIntro = docEl.classList.contains("no-preloader");
  function ready() { document.body.classList.add("is-loaded"); }

  if (!pre || skipIntro) {
    if (pre) pre.remove();
    /* two frames so hero line transitions still play on entry */
    requestAnimationFrame(function () { requestAnimationFrame(ready); });
  } else {
    var bar = pre.querySelector(".preloader__bar i");
    var count = pre.querySelector(".preloader__count");
    var t0 = null;
    var INTRO_MS = 1500;
    var introFinished = false;
    function tick(t) {
      if (introFinished) return;
      if (!t0) t0 = t;
      var p = Math.min((t - t0) / INTRO_MS, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      if (bar) bar.style.transform = "scaleX(" + eased + ")";
      if (count) count.textContent = Math.round(eased * 100);
      if (p < 1) requestAnimationFrame(tick);
      else setTimeout(introDone, 250);
    }
    function introDone() {
      if (introFinished) return;
      introFinished = true;
      if (bar) bar.style.transform = "scaleX(1)";
      if (count) count.textContent = "100";
      pre.classList.add("is-done");
      ready();
      try { sessionStorage.setItem("ghf-intro", "1"); } catch (e) {}
      setTimeout(function () { pre.remove(); }, 1100);
    }
    requestAnimationFrame(tick);
    /* rAF pauses in background tabs — never let the intro hold the page */
    setTimeout(introDone, INTRO_MS + 1400);
  }

  /* ---------- page-to-page fade transition ---------- */
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a[href]");
    if (!a || a.target || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var href = a.getAttribute("href");
    if (!href || href.charAt(0) === "#" || /^(https?:|tel:|mailto:)/.test(href)) return;
    /* a download (e.g. the schedule's .ics blob) is not a page navigation —
       without this the page fades out and tries to navigate to blob:/data: */
    if (a.hasAttribute("download") || /^(blob:|data:)/.test(href)) return;
    var url = new URL(a.href, location.href);
    if (url.pathname === location.pathname && url.hash) return; /* same-page anchor */
    e.preventDefault();
    document.body.classList.remove("menu-open");
    document.body.classList.add("page-exit");
    setTimeout(function () { location.href = a.href; }, 300);
  });
  /* bfcache restore (Safari back button): never come back faded out */
  window.addEventListener("pageshow", function (ev) {
    if (ev.persisted) {
      document.body.classList.remove("page-exit");
      document.body.classList.add("is-loaded");
    }
  });

  /* ---------- header behavior ---------- */
  /* persistent nav: always visible so Get Pricing never leaves the screen;
     compacts into a glass bar once scrolled */
  var header = document.querySelector(".site-header");
  function onScrollHeader() {
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 60);
  }
  window.addEventListener("scroll", onScrollHeader, { passive: true });
  onScrollHeader();

  /* ---------- menu overlay ---------- */
  var toggle = document.querySelector(".menu-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = document.body.classList.toggle("menu-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      var links = document.querySelectorAll(".menu-list a");
      links.forEach(function (a, i) {
        a.style.transitionDelay = open ? 0.18 + i * 0.05 + "s" : "0s";
      });
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") document.body.classList.remove("menu-open");
  });

  /* ---------- reveal on scroll ---------- */
  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add("is-in");
          io.unobserve(en.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
  );
  document.querySelectorAll(".reveal, .reveal-img, [data-stagger]").forEach(function (el) {
    io.observe(el);
  });

  /* ---------- counters ---------- */
  var cio = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        cio.unobserve(el);
        var target = parseFloat(el.getAttribute("data-count"));
        var dur = 1800;
        var t0 = null;
        function tick(t) {
          if (!t0) t0 = t;
          var p = Math.min((t - t0) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 4);
          el.textContent = Math.round(target * eased).toLocaleString();
          if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      });
    },
    { threshold: 0.5 }
  );
  document.querySelectorAll("[data-count]").forEach(function (el) { cio.observe(el); });

  /* ---------- parallax (media inside masked containers) ---------- */
  /* split/loc media use the wipe + zoom-settle reveal; hero media shows its
     full frame (no over-scan), so only CTA bands keep the parallax drift */
  var pxItems = [];
  document.querySelectorAll(".cta-band__media img").forEach(function (el) {
    pxItems.push(el);
  });
  var ticking = false;
  function parallax() {
    var vh = window.innerHeight;
    pxItems.forEach(function (el) {
      var r = el.parentElement.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) return;
      var p = (r.top + r.height / 2 - vh / 2) / (vh / 2 + r.height / 2); // -1..1
      var range = el.closest(".hero") ? 0.1 : 0.14;
      el.style.transform = "translateY(" + (-p * range * 100).toFixed(2) + "px)";
    });
    ticking = false;
  }
  function onScrollPx() {
    if (!ticking) { requestAnimationFrame(parallax); ticking = true; }
  }
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    window.addEventListener("scroll", onScrollPx, { passive: true });
    window.addEventListener("resize", onScrollPx);
    parallax();
  }

  /* ---------- accordion ---------- */
  document.querySelectorAll(".acc__item").forEach(function (item) {
    var head = item.querySelector(".acc__head");
    var body = item.querySelector(".acc__body");
    head.addEventListener("click", function () {
      var isOpen = item.classList.contains("is-open");
      var parent = item.closest(".acc");
      parent.querySelectorAll(".acc__item.is-open").forEach(function (o) {
        o.classList.remove("is-open");
        o.querySelector(".acc__body").style.maxHeight = "0px";
      });
      if (!isOpen) {
        item.classList.add("is-open");
        body.style.maxHeight = body.scrollHeight + "px";
      }
    });
  });

  /* ---------- testimonial slider ---------- */
  document.querySelectorAll(".t-slider").forEach(function (slider) {
    var track = slider.querySelector(".t-slider__track");
    var slides = track.children.length;
    var idx = 0;
    var auto;
    function go(n) {
      idx = (n + slides) % slides;
      track.style.transform = "translateX(-" + idx * 100 + "%)";
    }
    slider.querySelectorAll("[data-dir]").forEach(function (b) {
      b.addEventListener("click", function () {
        go(idx + (b.getAttribute("data-dir") === "next" ? 1 : -1));
        clearInterval(auto);
        auto = setInterval(function () { go(idx + 1); }, 6000);
      });
    });
    auto = setInterval(function () { go(idx + 1); }, 6000);
  });

  /* ---------- custom cursor ---------- */
  if (window.matchMedia("(hover: hover) and (min-width: 901px)").matches) {
    var dot = document.createElement("div");
    var ring = document.createElement("div");
    dot.className = "cursor-dot";
    ring.className = "cursor-ring";
    document.body.appendChild(dot);
    document.body.appendChild(ring);
    var mx = -100, my = -100, rx = -100, ry = -100;
    window.addEventListener("mousemove", function (e) { mx = e.clientX; my = e.clientY; });
    (function loop() {
      rx += (mx - rx) * 0.16;
      ry += (my - ry) * 0.16;
      dot.style.transform = "translate(" + mx + "px," + my + "px) translate(-50%,-50%)";
      ring.style.transform = "translate(" + rx + "px," + ry + "px) translate(-50%,-50%)";
      requestAnimationFrame(loop);
    })();
    document.addEventListener("mouseover", function (e) {
      if (e.target.closest("a, button, .acc__head")) ring.classList.add("is-hover");
      else ring.classList.remove("is-hover");
    });
  }

  /* ---------- floating labels: keep selects marked ---------- */
  document.querySelectorAll(".field select").forEach(function (s) {
    function mark() { s.closest(".field").classList.toggle("has-value", !!s.value); }
    s.addEventListener("change", mark);
    mark();
  });

  /* ---------- fake submit (demo) ---------- */
  document.querySelectorAll("form[data-demo]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      var btn = f.querySelector("button[type=submit]");
      if (btn) {
        var txt = btn.innerHTML;
        btn.innerHTML = "Request received — we'll be in touch";
        btn.disabled = true;
        setTimeout(function () { btn.innerHTML = txt; btn.disabled = false; f.reset(); }, 4200);
      }
    });
  });

  /* ---------- trainer profile panel ---------- */
  (function () {
    var panel = document.querySelector(".trainer-panel");
    if (!panel) return;
    var inner = panel.querySelector(".trainer-panel__inner");
    var closeBtn = panel.querySelector(".trainer-panel__close");
    var lastFocus = null;

    function fill(card) {
      var d = JSON.parse(card.getAttribute("data-trainer"));
      panel.querySelector("[data-t-photo]").src = d.photo;
      panel.querySelector("[data-t-photo]").alt = d.name;
      panel.querySelector("[data-t-name]").textContent = d.name;
      panel.querySelector("[data-t-role]").textContent = d.role;

      var q = panel.querySelector("[data-t-quote]");
      q.innerHTML = d.quote || "";
      q.hidden = !d.quote;                       // omit the empty "message" slot

      var tags = panel.querySelector("[data-t-tags]");
      tags.innerHTML = (d.specialties || []).map(function (t) {
        return "<span>" + t + "</span>";
      }).join("");
      tags.hidden = !(d.specialties && d.specialties.length);

      var facts = panel.querySelector("[data-t-facts]");
      facts.innerHTML = (d.facts || []).map(function (f) {
        return "<div><dt>" + f[0] + "</dt><dd>" + f[1] + "</dd></div>";
      }).join("");
      facts.hidden = !(d.facts && d.facts.length);
    }

    function open(card) {
      lastFocus = card;
      fill(card);
      panel.classList.add("is-open");
      document.body.style.overflow = "hidden";
      inner.scrollTop = 0;
      setTimeout(function () { closeBtn.focus(); }, 60);
    }

    function close() {
      panel.classList.remove("is-open");
      document.body.style.overflow = "";
      if (lastFocus) { lastFocus.focus(); lastFocus = null; }
    }

    document.querySelectorAll(".trainer-card").forEach(function (card) {
      card.addEventListener("click", function () { open(card); });
    });

    closeBtn.addEventListener("click", close);
    panel.querySelector(".trainer-panel__scrim").addEventListener("click", close);

    document.addEventListener("keydown", function (e) {
      if (!panel.classList.contains("is-open")) return;
      if (e.key === "Escape") { close(); return; }
      if (e.key !== "Tab") return;
      // keep focus inside the dialog
      var f = panel.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
      else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
    });
  })();

  /* ---------- photo slideshow ---------- */
  document.querySelectorAll(".slideshow").forEach(function (sh) {
    var slides = sh.querySelectorAll(".slideshow__slide");
    if (!slides.length) return;
    var cap = sh.querySelector(".slideshow__cap");
    var cur = sh.querySelector(".slideshow__cur");
    var i = 0;

    function show(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) {
        s.classList.toggle("is-on", k === i);
        // keep offscreen slides out of the tab order
        var img = s.querySelector("img");
        if (img && k !== i) img.setAttribute("aria-hidden", "true");
        else if (img) img.removeAttribute("aria-hidden");
      });
      if (cur) cur.textContent = String(i + 1).padStart(2, "0");
      if (cap) cap.textContent = slides[i].getAttribute("data-cap") || "";
      // load the neighbours so the next click is instant
      [i + 1, i - 1].forEach(function (k) {
        var s = slides[(k + slides.length) % slides.length];
        var img = s && s.querySelector("img[loading=lazy]");
        if (img) img.removeAttribute("loading");
      });
    }

    sh.querySelectorAll("[data-slide]").forEach(function (b) {
      b.addEventListener("click", function () {
        show(i + (b.getAttribute("data-slide") === "next" ? 1 : -1));
      });
    });

    sh.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { show(i + 1); e.preventDefault(); }
      if (e.key === "ArrowLeft") { show(i - 1); e.preventDefault(); }
    });

    show(0);
  });

  /* ---------- hero video: respect data saver ---------- */
  var heroVid = document.querySelector(".hero__media video");
  if (heroVid && navigator.connection && navigator.connection.saveData) {
    heroVid.removeAttribute("autoplay");
    heroVid.pause();
  }
})();
