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
- `top10_percent`: Top-10% journal flag from the source workbook.
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

Presentation records preserve `raw_citation_html` and `citation_text` as the source of truth. Automatically extracted fields such as `authors_raw`, `presenter_raw`, and `title_raw` are convenience fields and are marked as partial parsing. One 2024 source line appears to contain two concatenated presentations; it is intentionally preserved as one record with `quality.needs_review: true` until manually confirmed.
