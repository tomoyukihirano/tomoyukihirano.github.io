/* Filter structured presentation scopes without guessing from venue or language. */
(function () {
  "use strict";
  function initializePresentationFilters() {
    const list = document.getElementById("presentation-list");
    const controls = document.getElementById("presentation-controls");
    if (!list || !controls || controls.dataset.initialized === "true") return;
    const status = controls.querySelector(".presentation-controls__status");
    const buttons = Array.from(controls.querySelectorAll("button[data-presentation-filter]"));
    const records = Array.from(list.children).filter(function (item) { return item.tagName === "LI"; })
      .map(function (item) { return { item: item, scope: item.dataset.conferenceScope || "unclassified" }; });
    if (!status || buttons.length !== 3 || !records.length) return;
    const labels = { all: "全発表", domestic: "国内学会", international: "国際学会" };
    const counts = { all: records.length, domestic: 0, international: 0, other: 0, unclassified: 0 };
    records.forEach(function (record) {
      if (!Object.prototype.hasOwnProperty.call(counts, record.scope) || record.scope === "all") record.scope = "unclassified";
      counts[record.scope] += 1;
    });
    const reversed = list.reversed;
    function applyFilter(value) {
      const mode = Object.prototype.hasOwnProperty.call(labels, value) ? value : "all";
      const visible = counts[mode];
      list.start = reversed ? visible : 1;
      let number = list.start;
      records.forEach(function (record) {
        const matches = mode === "all" || record.scope === mode;
        record.item.hidden = !matches;
        if (matches) { record.item.value = number; number += reversed ? -1 : 1; }
        else record.item.removeAttribute("value");
      });
      buttons.forEach(function (button) { button.setAttribute("aria-pressed", String(button.dataset.presentationFilter === mode)); });
      status.textContent = labels[mode] + "：" + visible + "件を表示しています。";
      if (mode === "all" && (counts.other || counts.unclassified)) {
        status.textContent += "（国内" + counts.domestic + "件，国際" + counts.international + "件，その他" + counts.other + "件" +
          (counts.unclassified ? "，未分類" + counts.unclassified + "件" : "") + "）";
      }
    }
    buttons.forEach(function (button) {
      const mode = button.dataset.presentationFilter;
      button.textContent = labels[mode] + "（" + counts[mode] + "）";
      button.addEventListener("click", function () { applyFilter(mode); });
    });
    applyFilter("all");
    controls.dataset.initialized = "true";
    controls.hidden = false;
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initializePresentationFilters, { once: true });
  else initializePresentationFilters();
}());
