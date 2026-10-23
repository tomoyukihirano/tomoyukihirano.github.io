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
        citationText: text,
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

    // Join by a unique article URL or title, never by the visible list number.
    // Read citation text before adding dates so year/author filters stay intact.
    function addPublicationDates() {
      const script = Array.from(document.scripts).find(function (element) {
        return /\/publication-filters\.js(?:[?#]|$)/.test(element.src);
      });
      if (!script || typeof window.fetch !== "function") return;
      const source = new URL("publication-dates.json", script.src);
      function normalized(text) {
        return String(text || "").normalize("NFKC").toLowerCase()
          .replace(/[\u2010-\u2015\u2212]/g, "-").replace(/\s+/g, " ").trim();
      }
      function urlKey(value) {
        try {
          const url = new URL(value, window.location.href);
          if (!/^https?:$/.test(url.protocol)) return "";
          return url.hostname.toLowerCase() + url.pathname.toLowerCase()
            .replace(/\/doi\/(?:abs|full)\//, "/doi/")
            .replace(/\/article\/(?:abs\/)?pii\//, "/article/pii/")
            .replace(/\/article-abstract\//, "/article/")
            .replace(/\/article(?:html|landing)\//, "/article/")
            .replace(/\/$/, "");
        } catch (_) { return ""; }
      }
      function validDate(value) {
        if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
        const parsed = new Date(value + "T00:00:00Z");
        return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
      }
      fetch(source.href, { credentials: "same-origin" })
        .then(function (response) {
          if (!response.ok) throw new Error("Date metadata unavailable");
          return response.json();
        })
        .then(function (data) {
          if (data.schema_version !== 1 || !Array.isArray(data.records)) return;
          const ids = data.records.map(function (paper) { return paper.id; });
          if (ids.some(function (id) { return !id; }) || new Set(ids).size !== ids.length) return;
          const used = new Set();
          const fields = [
            { key: "submitted", label: "投稿日" },
            { key: "accepted", label: "採択日" },
            { key: "published_online", label: "オンライン公開日" }
          ];
          records.forEach(function (record) {
            if (record.item.querySelector(".publication-timeline")) return;
            const urls = Array.from(record.item.querySelectorAll("a[href]"))
              .map(function (link) { return urlKey(link.href); }).filter(Boolean);
            let matches = data.records.filter(function (paper) {
              return paper.article_url && urls.includes(urlKey(paper.article_url));
            });
            if (!matches.length) {
              matches = data.records.filter(function (paper) {
                const title = normalized(paper.title);
                return title.length > 20 && normalized(record.citationText).includes(title);
              });
            }
            const paper = matches.length === 1 && !used.has(matches[0].id) ? matches[0] : null;
            if (paper) {
              used.add(paper.id);
              record.item.dataset.publicationId = paper.id;
            }
            const dates = paper && paper.dates || {};
            const reviews = paper && paper.review && paper.review.fields || {};
            const chronologyIssues = new Set();
            [["submitted", "accepted"], ["accepted", "published_online"]].forEach(function (pair) {
              if (validDate(dates[pair[0]]) && validDate(dates[pair[1]]) && dates[pair[0]] > dates[pair[1]]) {
                chronologyIssues.add(pair[0]); chronologyIssues.add(pair[1]);
              }
            });
            const line = document.createElement("span");
            line.className = "publication-timeline";
            line.setAttribute("aria-label", "投稿・採択・オンライン公開の日付");
            fields.forEach(function (field) {
              const value = dates[field.key];
              const review = reviews[field.key] || {};
              const checking = review.status === "conflict" || review.status === "pending" ||
                chronologyIssues.has(field.key) || (value && !validDate(value)) ||
                (review.status === "verified" && review.checked_value !== value);
              const fieldItem = document.createElement("span");
              fieldItem.className = "publication-timeline__item";
              fieldItem.dataset.dateField = field.key;
              fieldItem.appendChild(document.createTextNode(field.label + "："));
              if (!checking && validDate(value)) {
                const time = document.createElement("time");
                time.dateTime = value;
                time.textContent = value;
                fieldItem.appendChild(time);
                fieldItem.title = review.status === "verified"
                  ? "出版社の記載と照合済み（" + paper.review.checked_on + "）"
                  : "既存の論文管理資料に登録された日付";
              } else {
                fieldItem.appendChild(document.createTextNode(checking ? "確認中" : "未確認"));
              }
              line.appendChild(fieldItem);
            });
            record.item.appendChild(line);
          });
          const note = document.createElement("p");
          note.className = "publication-filters__date-note";
          note.textContent = "日付は登録済み情報に基づきます。未取得の項目は「未確認」，不一致のある項目は「確認中」と表示します。";
          controls.appendChild(note);
          list.dataset.datesLoaded = "true";
          list.dataset.dateMatchedCount = String(used.size);
        })
        .catch(function () {
          // A missing metadata file must not break the existing list or filters.
          list.dataset.datesLoaded = "unavailable";
        });
    }

    applyFilters();
    addPublicationDates();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializePublicationFilters, { once: true });
  } else {
    initializePublicationFilters();
  }
}());
