# Achievement master data

This directory contains the public source-of-truth data used to generate academic achievement lists.

## Files

- `publications/YYYY.yml`: peer-reviewed journal articles grouped by publication year.
- `people.yml`: public author-name dictionary keyed by stable `person_id`.
- `journals.yml`: journal-level JCR quartile / impact-factor metadata.
- `presentations/YYYY.yml`: public presentation records grouped by year. The initial import preserves the exact existing website citation and adds safe structured fields where parsing is unambiguous.

## Publication record

Each publication has a stable ID such as `pub-0078` and stores bibliographic data, ordered author IDs, corresponding-author IDs, submission / acceptance / online-publication dates when known, and Hiroshima University reporting classifications.

Important classification fields:

- `hiroshima_academic_year`: institutional reporting year from the supplied Hiroshima-format workbook.
- `domestic_society_journal`: Japanese society journal classification.
- `english_journal`: English-language journal classification.
- `sci_or_equivalent`: SCI/equivalent classification.
- `hirano_corresponding`: Tomoyuki Hirano is a corresponding author.
- `hirano_first_author`: Tomoyuki Hirano is first author.
- `top10_percent`: Article citation Top-10% flag from the source workbook; any assessed field qualifies. This is not a journal-rank flag.
- `legacy_list_codes`: old A–T style list categories retained only for traceability.

## Public/private boundary

Only already-public achievement and author information belongs in this repository.

Private relationship data such as whether a student is primarily supervised by Tomoyuki Hirano must be stored in a separate private repository and joined by `person_id` only when producing internal reports.

Do not add student IDs, email addresses, grades, evaluations, or other internal personal information to this public repository.

## Source precedence

For the initial import:

1. Detailed bibliographic / date / author information: `論文データ管理_広大様式修正`.
2. Hiroshima University classifications and papers 77–78: the supplied Hiroshima-format workbook.
3. Journal metrics: `Journal Info` in the detailed workbook.

When source values conflict, do not silently overwrite them; record and review the discrepancy.

## Presentation records

Presentation records preserve `raw_citation_html` and `citation_text` as the source of truth. Automatically extracted fields such as `authors_raw`, `presenter_raw`, and `title_raw` are convenience fields and are marked as partial parsing. The owner-confirmed 2024 combined record has been split into pres-0072 and pres-0091; the original is retained in source_before_split.

## Confirmed author identity corrections

Eight identity merges were confirmed by the repository owner on 2026-10-22.
Canonical person records keep alternate spellings/order in `aliases` and retired IDs in `legacy_ids`.
`people.yml` also contains `id_redirects` so old exported IDs can be resolved.
Publication author and corresponding-author IDs were redirected without changing their order.
`author_names_as_imported` and `corresponding_author_names_as_imported` preserve the names
resolved from the pre-correction master; these are NOT independently verified publisher spellings.
Original website citations and all presentation `*_raw` / `citation_text` fields are unchanged.
Presentation `author_id_links` use 1-based positions and only exact, confirmed name matches.
Missing links mean unresolved, not absence of the person from the work.
Unconfirmed spelling variants must not be merged automatically.

## Presentation display format (2026-10-22)

The presentation page is generated from `_data/presentations/YYYY.yml` through
`_includes/presentation-list.html`. Do not maintain a second citation list in `presentations.md`.

The display order is authors, title, conference, location, date.
International conference entries use English for every visible citation field, with `, `
as the separator and `Invited talk` as the invitation label (owner-confirmed 2026-10-23).
Dates use `September 9, 2026` or `May 11–15, 2026`; repeat the month when a range
crosses months and both years when it crosses years. Use verified English author names
from `people.yml` or the original source, retaining author order. Existing English
titles and conference names are preserved. Other entries retain `，` and Japanese
date labels such as `YYYY年M月D日－D日`. A language-only correction does not alter
ISO dates, individual talk dates, original citations or `dates.source_text`.
Chemical subscripts/superscripts from source HTML are preserved.
Tomoyuki Hirano's name is bold and underlined. No presenter symbol is displayed.
The owner confirmed on 2026-10-22 that all 91 existing presentations were given by
the first author. Their `display.presenter_position` is 1 and `presenter_evidence`
is `owner_confirmed_first_author`. The presenter remains queryable for reports
even though the website does not print a symbol. This confirmation applies to
the existing records; explicitly verify the presenter of each future addition.
The older auto-parsed `presenter_raw` is retained only as imported source text;
use `display.authors[display.presenter_position - 1]` for the confirmed presenter.
`display.dates` describes recorded conference dates, not a verified individual talk date.
Original citation fields remain immutable except for the owner-approved split of pres-0072.
That original combined record is preserved in `source_before_split`; the new second record
is pres-0091. Existing IDs are never renumbered. `display_order` controls view ordering.
The `display` fields are the structured citation used by the template. `title_html` permits
only sub/sup markup; all other display text is HTML-escaped by the template.
Unconfirmed name variants, conference editions and presenter identities require review.

## Confirmed Japanese names (2026-10-22)

The owner confirmed 鬼頭 佑輔 / 鬼頭 祐輔 as the same person,
with canonical Japanese name 鬼頭 佑輔 (yusuke-kitou).
The owner confirmed 渡邊 真衣 / 渡邉 麻衣 as the same person,
with canonical Japanese name 渡邊 真衣 (mai-watanabe).
These public Japanese names and alternate forms are stored in the people dictionary.
Only structured presentation display names are normalized; raw citations are unchanged.

## Batched review corrections (2026-10-22)

Owner-confirmed aliases and Japanese names are linked by stable person IDs.
Questions 16-24 were applied as one coherent production batch.
Four records moved from the 2020 data file to 2021 without changing record IDs or display order.
The recorded conference dates are corrected; original citation text and date source text remain unchanged.
`quality.date_correction` preserves the previous structured dates and confirmation.
`quality.invited_status` and `invited_confirmed_on` distinguish confirmed invitation classifications
from legacy boolean values with no explicit confirmation.

## Consolidated review and reporting policy

Confirmed review items 25–72 are applied as one data batch.
`reporting_policy.yml` records conference classification, website date conventions,
retired record IDs, ignored award metadata, citation-metric definitions and output-time scope selection.
A null award value with `award_reporting: excluded_by_owner` means excluded metadata, not proof of no award.
The retired record is removed from the active list; its ID must not be reused.
`journals.metrics_context.checked_month` is an investigation month, not a JCR edition or metric year.
The actual metric year and subject categories remain unknown. No indicator values were refreshed.
Private relationship records are never loaded by the public site build.
The output rules do not constitute an implemented Excel/Word export tool.
