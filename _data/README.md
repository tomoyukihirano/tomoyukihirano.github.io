# Achievement master data

This directory contains the public source-of-truth data used to generate academic achievement lists.

## Files

- `publications/YYYY.yml`: peer-reviewed journal articles grouped by publication year.
- `people.yml`: public author-name dictionary keyed by stable `person_id`.
- `journals.yml`: journal-level JCR quartile / impact-factor metadata.

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
