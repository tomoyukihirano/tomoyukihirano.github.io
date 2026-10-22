/* Enhance the existing journal list without duplicating its citations.
 * Roles come from the displayed author order and the documented * marker.
 * Keep the original links usable when JavaScript is unavailable or the
 * expected markup is missing. Reviews, books and other sections are unchanged.
 */
(function () {
  "use strict";

  function initializePublicationFilters() {
    const content = document.querySelector(".page-id-35 .entry-content");
    if (!content || content.querySelector(".publication-filters")) return;

    const heading = Array.from(content.querySelectorAll("h2")).find(function (element) {
      return /^Peer-reviewed Journal Articles\b/.test(element.textContent.trim());
    });
    const list = heading && heading.nextElementSibling;
    if (!list || list.tagName !== "OL") return;

    const items = Array.from(list.children).filter(function (element) {
      return element.tagName === "LI";
    });
    if (!items.length) return;

    const records = items.map(function (item) {
      const text = item.textContent.replace(/\s+/g, " ").trim();
      return {
        item: item,
        first: /^Tomoyuki\s+Hirano(?=[\s*,，])/.test(text),
        corresponding: /\bTomoyuki\s+Hirano\s*\*/.test(text)
      };
    });
    // Fail safely rather than presenting an empty or misleading filter.
    if (!records.some(function (record) { return record.first; })) return;

    const legacyLinks = Array.from(content.querySelectorAll("p")).find(function (paragraph) {
      const paths = Array.from(paragraph.querySelectorAll("a[href]")).map(function (link) {
        return new URL(link.href, window.location.href).pathname.replace(/\/$/, "");
      });
      return paths.some(function (path) { return path.endsWith("/first-author"); }) &&
        paths.some(function (path) { return path.endsWith("/first-corresponding"); });
    });

    const modes = [
      { value: "all", label: "全論文", matches: function () { return true; } },
      { value: "first", label: "筆頭著者", matches: function (record) { return record.first; } },
      { value: "first-or-corresponding", label: "筆頭著者または責任著者", matches: function (record) {
        return record.first || record.corresponding;
      } }
    ];
    list.id = list.id || "peer-reviewed-publication-list";
    list.classList.add("publication-filter-list");

    // Preserve each paper's original number when other entries are hidden.
    let number = list.hasAttribute("start") ? Number(list.getAttribute("start")) :
      (list.reversed ? records.length : 1);
    records.forEach(function (record) {
      if (record.item.hasAttribute("value")) number = Number(record.item.getAttribute("value"));
      record.item.value = number;
      number += list.reversed ? -1 : 1;
    });

    const controls = document.createElement("div");
    controls.className = "publication-filters";
    const buttons = document.createElement("div");
    buttons.className = "publication-filters__buttons";
    buttons.setAttribute("role", "group");
    buttons.setAttribute("aria-label", "査読付き論文を平野知之の著者区分で絞り込む");
    const status = document.createElement("p");
    status.className = "publication-filters__status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.setAttribute("aria-atomic", "true");

    modes.forEach(function (mode) {
      const count = records.filter(mode.matches).length;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "publication-filters__button";
      button.dataset.authorFilter = mode.value;
      button.textContent = mode.label + "（" + count + "）";
      button.setAttribute("aria-controls", list.id);
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", function () { applyFilter(mode.value); });
      buttons.appendChild(button);
      mode.button = button;
    });
    controls.append(buttons, status);
    if (legacyLinks) legacyLinks.replaceWith(controls);
    else content.insertBefore(controls, heading);

    function applyFilter(value) {
      const active = modes.find(function (mode) { return mode.value === value; }) || modes[0];
      let visible = 0;
      records.forEach(function (record) {
        const matches = active.matches(record);
        record.item.hidden = !matches;
        if (matches) visible += 1;
      });
      modes.forEach(function (mode) {
        mode.button.setAttribute("aria-pressed", String(mode === active));
      });
      status.textContent = active.value === "all"
        ? "査読付き論文：全" + records.length + "件を表示しています。"
        : "査読付き論文：" + active.label + "の" + visible + "件を表示しています（全" + records.length + "件）。";

    }

    applyFilter("all");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializePublicationFilters, { once: true });
  } else {
    initializePublicationFilters();
  }
}());
