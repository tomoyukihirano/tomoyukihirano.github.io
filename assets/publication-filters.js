/* Filter the existing journal list by author role AND printed publication year.
 * Do not duplicate or rewrite citations. In-press items with no publication year
 * have their own option; never infer a publication year from an acceptance date.
 * Original links remain usable without JavaScript. Other sections are unchanged.
 */
(function () {
  "use strict";

  function initializePublicationFilters() {
    const content = document.querySelector(".page-id-35 .entry-content");
    if (!content || content.querySelector(".publication-filters")) return;

    const heading = Array.from(content.querySelectorAll("h2")).find(function (element) {
      return /^Peer-reviewed Journal Articles\b/.test(element.textContent.trim());
    });
    let list = heading && heading.nextElementSibling;
    while (list && list.tagName !== "OL" && !/^H[1-6]$/.test(list.tagName)) {
      list = list.nextElementSibling;
    }
    if (!list || list.tagName !== "OL") return;

    const items = Array.from(list.children).filter(function (element) {
      return element.tagName === "LI";
    });
    if (!items.length) return;

    function publicationYear(item, text) {
      // Allow explicit metadata, but otherwise use the year printed at the end
      // of the citation, not a year embedded in a title, DOI, or article URL.
      const explicit = item.getAttribute("data-publication-year");
      if (explicit && /^(?:19|20)\d{2}$/.test(explicit)) return explicit;
      const printed = text.match(/\b((?:19|20)\d{2})[.。]?(?:\s+(?:Invited|Review))?\s*$/i);
      if (printed) return printed[1];
      if (/\bin\s+press\b/i.test(text)) return "in-press";
      return "unknown";
    }

    const records = items.map(function (item) {
      const text = item.textContent.replace(/\s+/g, " ").trim();
      return {
        item: item,
        first: /^Tomoyuki\s+Hirano(?=[\s*,，])/.test(text),
        corresponding: /\bTomoyuki\s+Hirano\s*\*/.test(text),
        year: publicationYear(item, text)
      };
    });
    // Leave the original navigation intact if author parsing cannot succeed.
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
    const years = Array.from(new Set(records.map(function (record) { return record.year; })))
      .filter(function (year) { return /^(?:19|20)\d{2}$/.test(year); })
      .sort(function (a, b) { return Number(b) - Number(a); });
    const yearOptions = [{ value: "all", label: "すべての出版年" }].concat(
      years.map(function (year) { return { value: year, label: year + "年" }; })
    );
    if (records.some(function (record) { return record.year === "in-press"; })) {
      yearOptions.push({ value: "in-press", label: "In press（出版年未確定）" });
    }
    if (records.some(function (record) { return record.year === "unknown"; })) {
      yearOptions.push({ value: "unknown", label: "出版年未記載" });
    }

    list.id = list.id || "peer-reviewed-publication-list";
    list.classList.add("publication-filter-list");
    const reverseNumbering = list.reversed;
    const controls = document.createElement("div");
    controls.className = "publication-filters";
    const fields = document.createElement("div");
    fields.className = "publication-filters__fields";
    fields.setAttribute("role", "group");
    fields.setAttribute("aria-label", "査読付き論文の絞り込み");

    function createSelect(id, labelText, options) {
      const field = document.createElement("div");
      field.className = "publication-filters__field";
      const label = document.createElement("label");
      label.className = "publication-filters__label";
      label.htmlFor = id;
      label.textContent = labelText;
      const select = document.createElement("select");
      select.id = id;
      select.className = "publication-filters__select";
      select.setAttribute("aria-controls", list.id);
      options.forEach(function (entry) {
        const option = document.createElement("option");
        option.value = entry.value;
        option.textContent = entry.label;
        select.appendChild(option);
      });
      select.value = "all";
      select.addEventListener("change", applyFilters);
      field.append(label, select);
      fields.appendChild(field);
      return select;
    }

    const authorSelect = createSelect("publication-author-filter", "著者区分", modes);
    const yearSelect = createSelect("publication-year-filter", "出版年", yearOptions);
    const status = document.createElement("p");
    status.className = "publication-filters__status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.setAttribute("aria-atomic", "true");
    controls.append(fields, status);

    const correspondingNote = Array.from(content.querySelectorAll("p")).find(function (paragraph) {
      return paragraph.textContent.replace(/\s+/g, "").trim() === "*は責任著者を表しています。";
    });
    if (legacyLinks) legacyLinks.remove();
    if (correspondingNote) {
      heading.insertAdjacentElement("afterend", correspondingNote);
      correspondingNote.insertAdjacentElement("afterend", controls);
    } else {
      heading.insertAdjacentElement("afterend", controls);
    }

    const empty = document.createElement("p");
    empty.className = "publication-filters__empty";
    empty.textContent = "選択した条件に該当する論文はありません。";
    empty.hidden = true;
    list.insertAdjacentElement("afterend", empty);

    function applyFilters() {
      const active = modes.find(function (mode) { return mode.value === authorSelect.value; }) || modes[0];
      const activeYear = yearOptions.find(function (entry) { return entry.value === yearSelect.value; }) || yearOptions[0];
      function matches(record) {
        return active.matches(record) && (activeYear.value === "all" || record.year === activeYear.value);
      }
      const visible = records.filter(matches).length;
      list.start = reverseNumbering ? visible : 1;
      let number = list.start;
      records.forEach(function (record) {
        const show = matches(record);
        record.item.hidden = !show;
        if (show) {
          record.item.value = number;
          number += reverseNumbering ? -1 : 1;
        } else {
          record.item.removeAttribute("value");
        }
      });
      empty.hidden = visible !== 0;
      status.textContent = active.value === "all" && activeYear.value === "all"
        ? "査読付き論文：全" + records.length + "件を表示しています。"
        : "査読付き論文：" + active.label + "・" + activeYear.label + "の" + visible + "件を表示しています（全" + records.length + "件）。";
    }

    applyFilters();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializePublicationFilters, { once: true });
  } else {
    initializePublicationFilters();
  }
}());
