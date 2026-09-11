/* GHF — group fitness class schedule (Perch public API) */
(function () {
  "use strict";

  var root = document.querySelector(".gx");
  if (!root) return;

  var ENDPOINT = root.getAttribute("data-endpoint");
  /* when set, the schedule is scoped to a single studio (e.g. the hot yoga page) */
  var ONLY_ROOM = (root.getAttribute("data-room") || "").trim().toUpperCase();
  var TIMEOUT = 20000;
  var PERCH_URL = "https://app.perchteams.com/public/gx/ghf";
  var TZ = "America/New_York";

  /* the API's per-category `color` is corrupt (same category, different hex;
     mostly damaged near-identical greens) — location colour is clean, so we
     key off site and remap to on-brand tones. */
  var SITE_TONE = {
    "GHF MAIN": "main",
    "GHF WOMEN": "women",
    "GHF TIOGA": "tioga"
  };

  var state = { q: "", sites: [], category: "", room: "", day: "", instructor: "" };
  var days = [];      /* [{ key, day, date, heading, classes: [] }] */
  var all = [];       /* flat list, each class carries _dayKey */

  var elSearch = root.querySelector("#gxSearch");
  var elClear = root.querySelector(".gx__search-clear");
  var elChips = root.querySelector(".gx__chips");
  var elType = root.querySelector("#gxType");
  var elRoom = root.querySelector("#gxRoom");
  var elDay = root.querySelector("#gxDay");
  var elInstructor = root.querySelector("#gxInstructor");
  var elCount = root.querySelector(".gx__count");
  var elReset = root.querySelector(".gx__reset");
  var elStatus = root.querySelector(".gx__status");
  var elDays = root.querySelector(".gx__days");
  var elFilters = root.querySelector(".gx__filters");
  var elNow = root.querySelector(".gx__now");
  var lb = root.querySelector(".gx-lb");
  var lbImg = lb && lb.querySelector(".gx-lb__img");
  var lbName = lb && lb.querySelector(".gx-lb__name");
  var lbClose = lb && lb.querySelector(".gx-lb__close");
  var lbLastFocus = null;
  var TICK = 30000;

  /* ---------- helpers ---------- */

  /* third-party JSON goes into innerHTML — escape everything */
  function esc(v) {
    return String(v == null ? "" : v)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function clean(v) {
    return String(v == null ? "" : v).replace(/\s+/g, " ").trim();
  }

  function titleCase(v) {
    return clean(v).toLowerCase().replace(/(^|[\s\-\/&])([a-z])/g, function (m, a, b) {
      return a + b.toUpperCase();
    });
  }

  function initials(name) {
    var parts = clean(name).split(" ").filter(Boolean);
    if (!parts.length) return "";
    if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
  }

  function safePhoto(url) {
    var u = clean(url);
    return /^https:\/\//i.test(u) ? u : "";
  }

  function siteShort(site) {
    return clean(site).replace(/^GHF\s+/i, "");
  }

  /* month name pinned to the club's timezone — isoDate is UTC-shifted, so
     parsing it naively renders the wrong day east of UTC. The API's own
     `day` and `date` are authoritative for the weekday and day number. */
  function monthOf(isoDate) {
    try {
      return new Intl.DateTimeFormat("en-US", { timeZone: TZ, month: "long" })
        .format(new Date(isoDate));
    } catch (e) {
      return "";
    }
  }

  function uniqSorted(list) {
    var seen = {}, out = [];
    list.forEach(function (v) {
      if (v && !seen[v]) { seen[v] = 1; out.push(v); }
    });
    return out.sort();
  }

  /* ---------- parse ---------- */

  function parse(payload) {
    var raw = (payload && payload.schedule) || [];
    days = [];
    all = [];

    raw.forEach(function (d, i) {
      var key = "d" + i;
      var month = monthOf(d.isoDate);
      var src = (d.classes || []).filter(function (c) {
        return !ONLY_ROOM || String(c.room == null ? "" : c.room).trim().toUpperCase() === ONLY_ROOM;
      });
      var list = src.map(function (c) {
        var o = {
          id: clean(c.id) || (key + "-" + Math.random().toString(36).slice(2)),
          name: clean(c.name),
          /* 'CIRCUIT/ HIIT' and 'CIRCUIT/HIIT' are the same category */
          category: clean(c.category).replace(/\s*\/\s*/g, "/"),
          time: clean(c.time),
          duration: clean(c.duration),
          startTime: clean(c.startTime),
          endTime: clean(c.endTime),
          /* true UTC instants — correct in every viewer timezone */
          _start: Date.parse(c.startTime) || 0,
          _end: Date.parse(c.endTime) || 0,
          site: clean(c.site),
          room: clean(c.room),
          location: clean(c.location),
          instructor: clean(c.instructor),
          coInstructor: clean(c.coInstructor),
          photo: safePhoto(c.instructorPhotoUrl),
          description: clean(c.description),
          equipment: clean(c.equipment),
          _dayKey: key,
          _dayName: clean(d.day)
        };
        o._search = (o.name + " " + o.instructor + " " + o.coInstructor).toLowerCase();
        all.push(o);
        return o;
      });

      days.push({
        key: key,
        day: clean(d.day),
        date: d.date,
        heading: clean(d.day) + (month ? ", " + month + " " + d.date : ""),
        classes: list
      });
    });
  }

  /* ---------- filters ---------- */

  function buildFilters() {
    elChips.innerHTML = uniqSorted(all.map(function (c) { return c.site; }))
      .map(function (site) {
        return '<button type="button" class="gx__chip" data-tone="' +
          esc(SITE_TONE[site] || "main") + '" data-site="' + esc(site) +
          '" aria-pressed="false">' + esc(siteShort(site)) + "</button>";
      }).join("");

    fillSelect(elType, uniqSorted(all.map(function (c) { return c.category; })), "All types", titleCase);
    fillSelect(elRoom, uniqSorted(all.map(function (c) { return c.room; })), "All studios", titleCase);
    fillSelect(elInstructor, uniqSorted(all.map(function (c) { return c.instructor; })), "All instructors", titleCase);

    elDay.innerHTML = '<option value="">All days</option>' + days.map(function (d) {
      return '<option value="' + esc(d.key) + '">' + esc(d.heading) + "</option>";
    }).join("");
  
    /* one studio, one site: these two filters would each offer a single option.
       Hidden rather than removed — resetAll() still addresses both. */
    if (ONLY_ROOM) {
      elChips.hidden = true;
      var roomWrap = elRoom.closest(".gx__select");
      if (roomWrap) roomWrap.hidden = true;
    }
  }

  function fillSelect(el, values, allLabel, fmt) {
    el.innerHTML = '<option value="">' + esc(allLabel) + "</option>" +
      values.map(function (v) {
        return '<option value="' + esc(v) + '">' + esc(fmt ? fmt(v) : v) + "</option>";
      }).join("");
  }

  function matches(c) {
    if (state.sites.length && state.sites.indexOf(c.site) === -1) return false;
    if (state.category && c.category !== state.category) return false;
    if (state.room && c.room !== state.room) return false;
    if (state.day && c._dayKey !== state.day) return false;
    if (state.instructor && c.instructor !== state.instructor) return false;
    if (state.q && c._search.indexOf(state.q) === -1) return false;
    return true;
  }

  function isFiltered() {
    return !!(state.q || state.sites.length || state.category ||
              state.room || state.day || state.instructor);
  }

  /* ---------- render ---------- */

  function classHtml(c) {
    var tone = SITE_TONE[c.site] || "main";
    var whoName = titleCase(c.instructor);
    /* a photo is clickable (role/tabindex, not <button> — this sits inside the
       row's own <button>); initials stay inert */
    var photo = c.photo
      ? '<img class="gx-class__avatar gx-class__avatar--zoom" src="' + esc(c.photo) +
        '" alt="' + esc(whoName) + '" title="View photo of ' + esc(whoName) +
        '" role="button" tabindex="0" data-photo="' + esc(c.photo) +
        '" data-who="' + esc(whoName) + '" loading="lazy" width="34" height="34">'
      : (c.instructor
          ? '<span class="gx-class__avatar gx-class__avatar--initials" aria-hidden="true">' + esc(initials(c.instructor)) + "</span>"
          : "");

    var who = c.instructor
      ? '<span class="gx-class__who">' + photo +
        "<span>" + esc(titleCase(c.instructor)) +
        (c.coInstructor ? ' <em>with ' + esc(titleCase(c.coInstructor)) + "</em>" : "") +
        "</span></span>"
      : "";

    var detail =
      (c.description ? "<p>" + esc(c.description) + "</p>" : "") +
      (c.equipment ? '<p class="gx-class__equip"><strong>Equipment</strong> ' + esc(c.equipment) + "</p>" : "") +
      '<dl class="gx-class__facts">' +
        "<div><dt>Day</dt><dd>" + esc(c._dayName) + "</dd></div>" +
        "<div><dt>Duration</dt><dd>" + esc(c.duration) + "</dd></div>" +
        "<div><dt>Studio</dt><dd>" + esc(c.location) + "</dd></div>" +
      "</dl>" +
      '<div class="gx-cal">' +
        '<div class="gx-cal__links">' +
          '<span class="gx-cal__label">Add to calendar</span>' +
          '<a class="gx-cal__btn" data-cal="google" href="#" target="_blank" rel="noopener">Google</a>' +
          '<button type="button" class="gx-cal__btn" data-cal="apple">Apple</button>' +
          '<a class="gx-cal__btn" data-cal="outlook" href="#" target="_blank" rel="noopener">Outlook</a>' +
        "</div>" +
        '<p class="gx-cal__hint">Add it once, then set it to repeat in your calendar.</p>' +
      "</div>";

    return '<article class="gx-class" data-id="' + esc(c.id) + '" data-tone="' + esc(tone) + '">' +
      '<button type="button" class="gx-class__head" aria-expanded="false">' +
        '<span class="gx-class__time"><b>' + esc(c.time) + "</b><i>" + esc(c.duration) + "</i></span>" +
        '<span class="gx-class__main">' +
          '<span class="gx-class__live"><i aria-hidden="true"></i>Happening Now</span>' +
          '<span class="gx-class__name">' + esc(c.name) + "</span>" +
          '<span class="gx-class__meta">' + esc(titleCase(c.category)) +
            (c.room ? ' <span class="gx-class__dot">&middot;</span> ' + esc(titleCase(c.room)) : "") +
          "</span>" +
        "</span>" +
        who +
        '<span class="gx-class__site">' + esc(siteShort(c.site)) + "</span>" +
        '<span class="gx-class__chev" aria-hidden="true"></span>' +
      "</button>" +
      '<div class="gx-class__body"><div class="gx-class__body-inner">' + detail + "</div></div>" +
      "</article>";
  }

  function render() {
    var total = 0;
    var html = days.map(function (d) {
      var list = d.classes.filter(matches);
      if (!list.length) return "";
      total += list.length;
      return '<section class="gx-day">' +
        '<h3 class="gx-day__head">' + esc(d.heading) +
          '<span class="gx-day__count">' + list.length + "</span>" +
        "</h3>" +
        '<div class="gx-day__list">' + list.map(classHtml).join("") + "</div>" +
        "</section>";
    }).join("");

    if (total) {
      elDays.innerHTML = html;
      setStatus("");
    } else {
      elDays.innerHTML = "";
      setStatus('<p>No classes match those filters. <button type="button" class="gx__link" data-reset>Clear them</button> to see everything.</p>');
    }

    elCount.textContent = total
      ? (total + (total === 1 ? " class" : " classes") + (isFiltered() ? " match" : " this week"))
      : "";
    elReset.hidden = !isFiltered();
    markTime();
  }

  /* ---------- clock ---------- */

  /* Mutates the rows already in the DOM. Deliberately does NOT call render():
     that replaces elDays.innerHTML wholesale and would collapse any expanded
     row on every tick. */
  function markTime() {
    var now = Date.now();
    var rows = elDays.querySelectorAll(".gx-class");
    for (var i = 0; i < rows.length; i++) {
      var c = byId(rows[i].getAttribute("data-id"));
      if (!c) continue;
      rows[i].classList.toggle("is-now", c._start <= now && now < c._end);
      rows[i].classList.toggle("is-past", c._end > 0 && c._end <= now);
    }
    syncNow();
  }

  /* first visible row that is live, else the next one still to come */
  function nowTarget() {
    var now = Date.now();
    var rows = elDays.querySelectorAll(".gx-class");
    var upcoming = null;
    for (var i = 0; i < rows.length; i++) {
      var c = byId(rows[i].getAttribute("data-id"));
      if (!c) continue;
      if (c._start <= now && now < c._end) return rows[i];
      if (!upcoming && c._start > now) upcoming = rows[i];
    }
    return upcoming;
  }

  function syncNow() {
    if (elNow) elNow.hidden = !nowTarget();
  }

  function jumpToNow() {
    var el = nowTarget();
    if (!el) return;
    var top = el.getBoundingClientRect().top + window.scrollY - 90; /* sticky header */
    window.scrollTo({ top: top, behavior: "smooth" });
    el.classList.add("is-flash");
    setTimeout(function () { el.classList.remove("is-flash"); }, 1600);
  }

  /* ---------- instructor photo lightbox ---------- */

  function openPhoto(src, who, trigger) {
    if (!lb) return;
    lbLastFocus = trigger || null;
    lbImg.src = src;
    lbImg.alt = who || "";
    lbName.textContent = who || "";
    lb.hidden = false;
    /* next frame so the transition runs from the hidden state */
    requestAnimationFrame(function () { lb.classList.add("is-open"); });
    document.body.style.overflow = "hidden";
    setTimeout(function () { lbClose.focus(); }, 60);
  }

  function closePhoto() {
    if (!lb || lb.hidden) return;
    lb.classList.remove("is-open");
    document.body.style.overflow = "";
    setTimeout(function () {
      lb.hidden = true;
      lbImg.src = "";
    }, 450);
    if (lbLastFocus) { lbLastFocus.focus(); lbLastFocus = null; }
  }

  function bindLightbox() {
    if (!lb) return;
    lbClose.addEventListener("click", closePhoto);
    lb.querySelector(".gx-lb__scrim").addEventListener("click", closePhoto);
    document.addEventListener("keydown", function (e) {
      if (lb.hidden) return;
      if (e.key === "Escape") { closePhoto(); return; }
      if (e.key !== "Tab") return;
      /* only the close button is focusable in here — keep focus inside */
      e.preventDefault();
      lbClose.focus();
    });
  }

  function setStatus(html) {
    elStatus.innerHTML = html;
    elStatus.hidden = !html;
  }

  /* ---------- calendar ---------- */

  function stamp(iso) {
    return clean(iso).replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  }

  function calTitle(c) {
    return c.name + " — Gainesville Health & Fitness";
  }

  function calBody(c) {
    return (c.instructor ? "Instructor: " + titleCase(c.instructor) + "\n" : "") +
      "Location: " + c.location;
  }

  function googleUrl(c) {
    return "https://calendar.google.com/calendar/render?action=TEMPLATE" +
      "&text=" + encodeURIComponent(calTitle(c)) +
      "&dates=" + stamp(c.startTime) + "/" + stamp(c.endTime) +
      "&details=" + encodeURIComponent(calBody(c)) +
      "&location=" + encodeURIComponent(c.location);
  }

  function outlookUrl(c) {
    return "https://outlook.live.com/calendar/0/action/compose?path=" +
      encodeURIComponent("/calendar/action/compose") + "&rru=addevent" +
      "&subject=" + encodeURIComponent(calTitle(c)) +
      "&startdt=" + encodeURIComponent(c.startTime) +
      "&enddt=" + encodeURIComponent(c.endTime) +
      "&location=" + encodeURIComponent(c.location) +
      "&body=" + encodeURIComponent(calBody(c));
  }

  function icsEscape(v) {
    return String(v == null ? "" : v)
      .replace(/\\/g, "\\\\").replace(/;/g, "\\;")
      .replace(/,/g, "\\,").replace(/\n/g, "\\n");
  }

  function icsFor(list) {
    var now = stamp(new Date().toISOString());
    var lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Gainesville Health & Fitness//GX Schedule//EN", "CALSCALE:GREGORIAN"];
    list.forEach(function (c) {
      lines.push("BEGIN:VEVENT",
        "UID:" + c.id + "@ghf",
        "DTSTAMP:" + now,
        "DTSTART:" + stamp(c.startTime),
        "DTEND:" + stamp(c.endTime),
        "SUMMARY:" + icsEscape(calTitle(c)),
        "DESCRIPTION:" + icsEscape(calBody(c)),
        "LOCATION:" + icsEscape(c.location),
        "END:VEVENT");
    });
    lines.push("END:VCALENDAR");
    return lines.join("\r\n");
  }

  function downloadIcs(c) {
    var name = (c.name || "class").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    var blob = new Blob([icsFor([c])], { type: "text/calendar;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "ghf-" + name + ".ics";
    /* keep the synthetic click off main.js's document-level link handler */
    a.addEventListener("click", function (ev) { ev.stopPropagation(); });
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function byId(id) {
    for (var i = 0; i < all.length; i++) if (all[i].id === id) return all[i];
    return null;
  }

  /* ---------- events ---------- */

  function bind() {
    elSearch.addEventListener("input", function () {
      state.q = clean(elSearch.value).toLowerCase();
      elClear.hidden = !elSearch.value;
      render();
    });

    elClear.addEventListener("click", function () {
      elSearch.value = "";
      state.q = "";
      elClear.hidden = true;
      elSearch.focus();
      render();
    });

    elChips.addEventListener("click", function (e) {
      var b = e.target.closest(".gx__chip");
      if (!b) return;
      var site = b.getAttribute("data-site");
      var i = state.sites.indexOf(site);
      if (i === -1) state.sites.push(site); else state.sites.splice(i, 1);
      b.classList.toggle("is-on", i === -1);
      b.setAttribute("aria-pressed", i === -1 ? "true" : "false");
      render();
    });

    [[elType, "category"], [elRoom, "room"], [elDay, "day"], [elInstructor, "instructor"]]
      .forEach(function (pair) {
        pair[0].addEventListener("change", function () {
          state[pair[1]] = pair[0].value;
          render();
        });
      });

    elReset.addEventListener("click", resetAll);
    if (elNow) elNow.addEventListener("click", jumpToNow);
    elStatus.addEventListener("click", function (e) {
      if (e.target.closest("[data-reset]")) resetAll();
    });

    /* expand / collapse + calendar, delegated so injected rows just work */
    elDays.addEventListener("click", function (e) {
      /* checked first: the avatar sits inside .gx-class__head, so without this
         the row would expand behind the lightbox */
      var av = e.target.closest(".gx-class__avatar--zoom");
      if (av) {
        e.preventDefault();
        e.stopPropagation();
        openPhoto(av.getAttribute("data-photo"), av.getAttribute("data-who"), av);
        return;
      }

      var head = e.target.closest(".gx-class__head");
      if (head) {
        var card = head.closest(".gx-class");
        var open = card.classList.toggle("is-open");
        head.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) syncCal(card);
        return;
      }

      var apple = e.target.closest('[data-cal="apple"]');
      if (apple) {
        e.preventDefault();
        var card2 = apple.closest(".gx-class");
        var c = byId(card2.getAttribute("data-id"));
        if (c) downloadIcs(c);
      }
    });

    elDays.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " " && e.key !== "Spacebar") return;
      var av = e.target.closest && e.target.closest(".gx-class__avatar--zoom");
      if (!av) return;
      e.preventDefault();
      e.stopPropagation();
      openPhoto(av.getAttribute("data-photo"), av.getAttribute("data-who"), av);
    });

    bindLightbox();
  }

  function syncCal(card) {
    var c = byId(card.getAttribute("data-id"));
    if (!c) return;
    card.querySelector('[data-cal="google"]').href = googleUrl(c);
    card.querySelector('[data-cal="outlook"]').href = outlookUrl(c);
  }

  function resetAll() {
    state = { q: "", sites: [], category: "", room: "", day: "", instructor: "" };
    elSearch.value = "";
    elClear.hidden = true;
    elType.value = elRoom.value = elDay.value = elInstructor.value = "";
    elChips.querySelectorAll(".gx__chip").forEach(function (b) {
      b.classList.remove("is-on");
      b.setAttribute("aria-pressed", "false");
    });
    render();
  }

  /* ---------- load ---------- */

  function fail(err) {
    if (window.console && console.error) console.error("[gx] schedule failed:", err);
    elFilters.hidden = true;
    elDays.innerHTML = "";
    /* the feed loaded fine, there is just nothing in this studio this week (or the
       room was renamed upstream) — say that, rather than "we can't load it" */
    if (err && err.message === "empty-room") {
      setStatus('<p>No classes are scheduled in this studio this week. ' +
        'See the <a href="group-fitness.html#schedule">full class schedule</a>, ' +
        'or view it at <a href="' + PERCH_URL + '" rel="noopener">app.perchteams.com</a>.</p>');
      return;
    }
    setStatus('<p class="gx__error">We can&rsquo;t load the class schedule right now. ' +
      'You can view it at <a href="' + PERCH_URL + '" rel="noopener">app.perchteams.com</a>, ' +
      'or call us at <a href="tel:3523774955">(352) 377-4955</a> and we&rsquo;ll walk you through it.</p>');
  }

  function load() {
    var ctl = window.AbortController ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctl) ctl.abort(); }, TIMEOUT);

    fetch(ENDPOINT, ctl ? { signal: ctl.signal } : undefined)
      .then(function (res) {
        if (!res.ok) throw new Error("API " + res.status);
        return res.json();
      })
      .then(function (data) {
        parse(data);
        if (!all.length) throw new Error(ONLY_ROOM ? "empty-room" : "empty");
        buildFilters();
        bind();
        elFilters.hidden = false;
        render();
        setInterval(markTime, TICK);
      })
      .catch(fail)
      .finally(function () { clearTimeout(timer); });
  }

  elFilters.hidden = true;
  load();
})();
