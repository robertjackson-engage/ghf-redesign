/* GHF — Member Savings directory: category filter + keyword search.
   Every business is already in the HTML; this only shows and hides, so the
   page is a complete directory with JavaScript off. */
(function () {
  "use strict";

  var root = document.querySelector(".sv");
  if (!root) return;

  var elSearch = root.querySelector("#svSearch");
  var elClear = root.querySelector(".sv__clear");
  var elCat = root.querySelector("#svCat");
  var elCount = root.querySelector(".sv__count");
  var elReset = root.querySelector(".sv__reset");
  var elEmpty = root.querySelector(".sv__empty");
  var cards = [].slice.call(root.querySelectorAll(".biz"));
  var total = cards.length;

  var state = { q: "", cat: "" };

  function isFiltered() {
    return !!(state.q || state.cat);
  }

  function apply() {
    var shown = 0;
    for (var i = 0; i < cards.length; i++) {
      var c = cards[i];
      var ok = true;
      if (state.cat && c.getAttribute("data-cat") !== state.cat) ok = false;
      if (ok && state.q && c.getAttribute("data-find").indexOf(state.q) === -1) ok = false;
      c.hidden = !ok;
      if (ok) shown++;
    }
    elCount.textContent = shown + (shown === 1 ? " business" : " businesses") +
      (isFiltered() ? " match" : "");
    elEmpty.hidden = shown !== 0;
    elReset.hidden = !isFiltered();
    elClear.hidden = !state.q;
  }

  function reset() {
    state = { q: "", cat: "" };
    elSearch.value = "";
    elCat.value = "";
    apply();
  }

  elSearch.addEventListener("input", function () {
    state.q = elSearch.value.trim().toLowerCase();
    apply();
  });
  elCat.addEventListener("change", function () {
    state.cat = elCat.value;
    apply();
  });
  elClear.addEventListener("click", function () {
    elSearch.value = "";
    state.q = "";
    apply();
    elSearch.focus();
  });
  elReset.addEventListener("click", reset);
  elEmpty.addEventListener("click", function (e) {
    if (e.target.closest("[data-sv-reset]")) reset();
  });

  elCount.textContent = total + " businesses";
})();
