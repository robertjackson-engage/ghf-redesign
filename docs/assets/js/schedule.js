/* GHF — group fitness class schedule (Perch public API) */
(function () {
  "use strict";

  var root = document.querySelector(".gx");
  if (!root) return;

  var ENDPOINT = root.getAttribute("data-endpoint");
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
      var list = (d.classes || []).map(function (c) {
        var o = {
          id: clean(c.id) || (key + "-" + Math.random().toString(36).slice(2)),
          name: clean(c.name),
          /* 'CIRCUIT/ HIIT' and 'CIRCUIT/HIIT' are the same category */
          category: clean(c.category).replace(/\s*\/\s*/g, "/"),
          time: clean(c.time),
          duration: clean(c.duration),
          startTime: clean(c.startTime),
          endTime: clean(c.endTime),
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
    var photo = c.photo
      ? '<img class="gx-class__avatar" src="' + esc(c.photo) + '" alt="" loading="lazy" width="34" height="34">'
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
        '<div class="gx-cal__scope" role="group" aria-label="Calendar scope">' +
          '<button type="button" class="is-on" data-scope="one">This class only</button>' +
          '<button type="button" data-scope="all">All in next 8 days</button>' +
        "</div>" +
        '<div class="gx-cal__links">' +
          '<span class="gx-cal__label">Add to calendar</span>' +
          '<a class="gx-cal__btn" data-cal="google" href="#" target="_blank" rel="noopener">Google</a>' +
          '<button type="button" class="gx-cal__btn" data-cal="apple">Apple</button>' +
          '<a class="gx-cal__btn" data-cal="outlook" href="#" target="_blank" rel="noopener">Outlook</a>' +
        "</div>" +
      "</div>";

    return '<article class="gx-class" data-id="' + esc(c.id) + '" data-tone="' + esc(tone) + '">' +
      '<button type="button" class="gx-class__head" aria-expanded="false">' +
        '<span class="gx-class__time"><b>' + esc(c.time) + "</b><i>" + esc(c.duration) + "</i></span>" +
        '<span class="gx-class__main">' +
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
  }

  function setStatus(html) {
    elStatus.innerHTML = html;
    elStatus.hidden = !html;
  }

  /* ---------- calendar ---------- */

  function stamp(iso) {
    return clean(iso).replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  }

  function seriesFor(c, scope) {
    if (scope !== "all") return [c];
    return all.filter(function (x) {
      return x.name === c.name && x.time === c.time && x.room === c.room && x.site === c.site;
    });
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

  /* one VEVENT per real occurrence — the API exposes no recurrence rule, so
     emitting an RRULE would go stale the moment the timetable changes */
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

  function downloadIcs(c, scope) {
    var list = seriesFor(c, scope);
    var name = (c.name || "class").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    var blob = new Blob([icsFor(list)], { type: "text/calendar;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "ghf-" + name + ".ics";
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
    elStatus.addEventListener("click", function (e) {
      if (e.target.closest("[data-reset]")) resetAll();
    });

    /* expand / collapse + calendar, delegated so injected rows just work */
    elDays.addEventListener("click", function (e) {
      var head = e.target.closest(".gx-class__head");
      if (head) {
        var card = head.closest(".gx-class");
        var open = card.classList.toggle("is-open");
        head.setAttribute("aria-expanded", open ? "true" : "false");
        if (open) syncCal(card);
        return;
      }

      var scope = e.target.closest("[data-scope]");
      if (scope) {
        var box = scope.closest(".gx-cal__scope");
        box.querySelectorAll("[data-scope]").forEach(function (x) { x.classList.remove("is-on"); });
        scope.classList.add("is-on");
        syncCal(scope.closest(".gx-class"));
        return;
      }

      var apple = e.target.closest('[data-cal="apple"]');
      if (apple) {
        e.preventDefault();
        var card2 = apple.closest(".gx-class");
        var c = byId(card2.getAttribute("data-id"));
        if (c) downloadIcs(c, currentScope(card2));
      }
    });
  }

  function currentScope(card) {
    var on = card.querySelector(".gx-cal__scope .is-on");
    return on ? on.getAttribute("data-scope") : "one";
  }

  function syncCal(card) {
    var c = byId(card.getAttribute("data-id"));
    if (!c) return;
    /* Google and Outlook take a single event; "all" is served by the .ics */
    card.querySelector('[data-cal="google"]').href = googleUrl(c);
    card.querySelector('[data-cal="outlook"]').href = outlookUrl(c);
    var many = currentScope(card) === "all";
    var n = many ? seriesFor(c, "all").length : 1;
    card.querySelector('[data-cal="apple"]').textContent = many ? "Apple (" + n + ")" : "Apple";
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
        if (!all.length) throw new Error("empty");
        buildFilters();
        bind();
        elFilters.hidden = false;
        render();
      })
      .catch(fail)
      .finally(function () { clearTimeout(timer); });
  }

  elFilters.hidden = true;
  load();
})();
