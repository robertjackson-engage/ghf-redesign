/* GHF — job application form, rendered from the Perch application API.

   The field definitions, their order, which are required and the knock-out rules all live
   in Perch, so this renders whatever that posting currently asks for rather than hard-coding
   a form that would drift. Contract, confirmed against the live API:

     GET  /apply/<org>/<posting>              -> { data: { job, posting, form: { sections[] } } }
     POST /apply/<org>/<posting>/upload-url   -> { data: { uploadUrl, key } }   then PUT the file
     POST /apply/<org>/<posting>              -> 201 { data: { status: "SUBMITTED" } }
                                              -> 422 { data: { status: "REJECTED", triggeredRules } }

   A 422 is not an error: it means the answers tripped a knock-out rule (under 16, unable to
   commit a weekend, and so on). It gets its own message, not a failure notice. */
(function () {
  "use strict";

  var root = document.querySelector(".apply");
  if (!root) return;

  var API = root.getAttribute("data-api");
  var form = root.querySelector(".apply__form");
  var out = root.querySelector(".apply__out");
  var fieldsEl = root.querySelector(".apply__fields");
  var submitBtn = root.querySelector(".apply__submit");
  var def = null;          /* the posting + form definition */
  var answers = {};        /* fieldId -> value, in the shapes the API expects */
  var busy = false;

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function note(kind, html) {
    out.innerHTML = '<div class="jn-note' + (kind === "warn" ? " warn" : "") + '">' + html + "</div>";
  }

  /* ---------- rendering ---------- */

  function fieldControl(f) {
    var id = "af-" + f.id;
    var req = f.required ? " required" : "";
    switch (f.type) {
      case "LONG_TEXT":
      case "ADDRESS":
        return '<textarea id="' + id + '" rows="5" placeholder=" "' + req + '></textarea>';
      case "NUMBER":
        return '<input id="' + id + '" type="number" min="0" placeholder=" "' + req + '>';
      case "YES_NO":
        return '<div class="apply__choices" role="radiogroup" aria-labelledby="' + id + '-l">' +
          ["Yes", "No"].map(function (v) {
            return '<label class="apply__choice"><input type="radio" name="' + id + '" value="' + v + '">' +
              "<span>" + v + "</span></label>";
          }).join("") + "</div>";
      case "MULTI_SELECT":
        return '<div class="apply__choices">' +
          (f.options || []).map(function (o) {
            return '<label class="apply__choice"><input type="checkbox" value="' + esc(o.value) + '">' +
              "<span>" + esc(o.label) + "</span></label>";
          }).join("") + "</div>";
      case "FILE_UPLOAD":
        return '<div class="apply__file">' +
          '<input id="' + id + '" type="file" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png">' +
          '<p class="apply__filenote">PDF, Word, JPG or PNG, up to 10&nbsp;MB.</p></div>';
      default:
        return '<input id="' + id + '" type="text" placeholder=" "' + req + '>';
    }
  }

  function render() {
    var html = "";
    var sections = (def.form.sections || []).slice().sort(function (a, b) { return a.order - b.order; });
    sections.forEach(function (sec) {
      html += '<fieldset class="apply__section">';
      if (sec.name) html += "<legend>" + esc(sec.name) + "</legend>";
      (sec.fields || []).slice().sort(function (a, b) { return (a.order || 0) - (b.order || 0); })
        .forEach(function (f) {
          var boxy = f.type === "YES_NO" || f.type === "MULTI_SELECT" || f.type === "FILE_UPLOAD";
          html += '<div class="apply__field' + (boxy ? " apply__field--boxy" : "") +
            '" data-fid="' + f.id + '" data-ftype="' + f.type + '">';
          /* a floating label cannot sit over a radio group, so those get a plain heading */
          if (boxy) {
            html += '<p class="apply__label" id="af-' + f.id + '-l">' + esc(f.label) +
              (f.required ? ' <span class="apply__req">required</span>' : "") + "</p>" + fieldControl(f);
          } else {
            html += fieldControl(f) + '<label for="af-' + f.id + '">' + esc(f.label) + "</label>";
          }
          html += "</div>";
        });
      html += "</fieldset>";
    });
    fieldsEl.innerHTML = html;
    wire();
  }

  function wire() {
    fieldsEl.querySelectorAll(".apply__field").forEach(function (wrap) {
      var fid = wrap.getAttribute("data-fid"), type = wrap.getAttribute("data-ftype");

      if (type === "YES_NO") {
        wrap.querySelectorAll('input[type="radio"]').forEach(function (r) {
          r.addEventListener("change", function () { answers[fid] = r.value; });
        });
      } else if (type === "MULTI_SELECT") {
        wrap.querySelectorAll('input[type="checkbox"]').forEach(function (c) {
          c.addEventListener("change", function () {
            var on = [];
            wrap.querySelectorAll('input[type="checkbox"]').forEach(function (x) { if (x.checked) on.push(x.value); });
            /* the API expects an array, or the key absent entirely — never an empty array */
            if (on.length) answers[fid] = on; else delete answers[fid];
          });
        });
      } else if (type === "FILE_UPLOAD") {
        wrap.querySelector('input[type="file"]').addEventListener("change", function (e) {
          uploadResume(e.target.files && e.target.files[0], wrap, fid);
        });
      } else {
        var el = wrap.querySelector("input, textarea");
        el.addEventListener("input", function () {
          var v = el.value.trim();
          if (!v) { delete answers[fid]; return; }
          /* NUMBER must go as a real number; everything else as a string */
          answers[fid] = type === "NUMBER" ? Number(v) : v;
        });
      }
    });
  }

  /* ---------- resume ---------- */

  function uploadResume(file, wrap, fid) {
    var noteEl = wrap.querySelector(".apply__filenote");
    if (!file) { delete answers[fid]; return; }
    if (file.size > 10 * 1024 * 1024) {
      noteEl.innerHTML = '<span class="bad">That file is over 10&nbsp;MB. Please attach a smaller one.</span>';
      wrap.querySelector('input[type="file"]').value = "";
      return;
    }
    noteEl.textContent = "Uploading " + file.name + "…";
    fetch(API + "/upload-url", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, contentType: file.type, size: file.size })
    }).then(function (r) {
      if (!r.ok) throw new Error("upload-url");
      return r.json();
    }).then(function (j) {
      return fetch(j.data.uploadUrl, { method: "PUT", body: file, headers: { "Content-Type": file.type } })
        .then(function (up) {
          if (!up.ok) throw new Error("PUT " + up.status);
          /* the answer is the file descriptor, not the file */
          answers[fid] = { key: j.data.key, filename: file.name, contentType: file.type, size: file.size };
          noteEl.innerHTML = '<span class="ok">Attached ' + esc(file.name) + "</span>";
        });
    }).catch(function () {
      delete answers[fid];
      noteEl.innerHTML = '<span class="bad">That upload did not work. You can still apply without a resume.</span>';
    });
  }

  /* ---------- validation + submit ---------- */

  function missing() {
    var out = [];
    (def.form.sections || []).forEach(function (sec) {
      (sec.fields || []).forEach(function (f) {
        if (!f.required) return;
        var v = answers[f.id];
        var empty = v === undefined || v === null || v === "" ||
          (Array.isArray(v) && v.length === 0);
        if (empty) out.push(f.label);
      });
    });
    return out;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (busy) return;
    var name = form.querySelector("#ap-name").value.trim();
    var email = form.querySelector("#ap-email").value.trim();
    var phone = form.querySelector("#ap-phone").value.trim();
    if (!name || !email) { note("warn", "Please add your name and email so we can reply."); return; }

    var gaps = missing();
    if (gaps.length) {
      note("warn", "Please answer: " + gaps.map(function (g) {
        return "<b>" + esc(g.length > 60 ? g.slice(0, 60) + "…" : g) + "</b>";
      }).join(", "));
      return;
    }

    busy = true; submitBtn.disabled = true;
    note("", "Sending your application…");
    fetch(API, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidateName: name, candidateEmail: email,
        candidatePhone: phone || undefined, answers: answers
      })
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { return { r: r, j: j }; });
    }).then(function (res) {
      /* 422 is a decision, not a failure: the answers tripped a knock-out rule */
      if (res.r.status === 422) { finish("rejected", res.j); return; }
      if (res.r.ok) { finish("success", res.j); return; }
      busy = false; submitBtn.disabled = false;
      note("warn", esc((res.j && res.j.error) || "Something went wrong. Please try again."));
    }).catch(function () {
      busy = false; submitBtn.disabled = false;
      note("warn", "We could not reach the application service. Please try again in a moment, " +
        'or call <a href="tel:+13523774955">(352) 377-4955</a>.');
    });
  });

  function finish(kind, j) {
    var p = def.posting || {};
    var head, msg;
    if (kind === "success") {
      head = p.successHeading || "Thank you — your application is in.";
      msg = p.successMessage ||
        "Our hiring team reviews every application. If you look like a fit for the team, we will be in touch.";
    } else {
      var rule = (j && j.data && j.data.triggeredRules && j.data.triggeredRules[0]) || {};
      head = p.rejectedHeading || "Thank you for your interest.";
      msg = rule.applicantMessage || p.rejectedMessage ||
        "Based on your answers this particular role is not a match right now. " +
        "Other roles at GHF have different requirements, and you are welcome to apply for those.";
    }
    root.querySelector(".apply__body").innerHTML =
      '<div class="apply__done"><h2 class="h-display">' + esc(head) + "</h2>" +
      '<p class="lede">' + esc(msg) + "</p>" +
      '<p style="margin-top:28px"><a class="btn btn--solid" href="careers.html#roles">' +
      'See other roles <span class="arr">&rarr;</span></a></p></div>';
    root.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  /* ---------- boot ---------- */

  fetch(API).then(function (r) {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }).then(function (j) {
    def = j.data;
    if (def.posting && def.posting.isActive === false) {
      root.querySelector(".apply__body").innerHTML =
        '<div class="apply__done"><h2 class="h-display">This role is not open right now.</h2>' +
        '<p class="lede">It has closed since this page was linked. Other teams are still hiring.</p>' +
        '<p style="margin-top:28px"><a class="btn btn--solid" href="careers.html#roles">' +
        'See open roles <span class="arr">&rarr;</span></a></p></div>';
      return;
    }
    render();
    form.hidden = false;
    root.querySelector(".apply__loading").hidden = true;
  }).catch(function () {
    root.querySelector(".apply__loading").innerHTML =
      '<div class="jn-note warn">We could not load the application form. ' +
      'Please try again in a moment, or call <a href="tel:+13523774955">(352) 377-4955</a>.</div>';
  });
})();
