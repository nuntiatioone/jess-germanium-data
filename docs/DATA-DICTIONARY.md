# Data dictionary and interpretation — schema 1 / resource 0.1.1

JSONL is the authoritative structured transcription; one object per line. CSV contains the same fields, with nested arrays/objects encoded as JSON strings and nulls represented by empty cells. SQLite stores selected indexed columns plus the **complete** JSON in `document`. Decimal strings retain source precision; SQLite numeric condition columns are only filter indexes. No data were fitted or interpolated.

| File | Grain / key | Meaning |
|---|---|---|
| `reactions.jsonl` | JESS reaction `id` | Raw/normalised equation, all notes and note pages, heading page/bounding box, exact balance result |
| `parameters.jsonl` | `JESS-8.9:Ge:<reaction>:<row>` | One source parameter row with its conditions, uncertainty notation, weight, technique, bibliography link and applicable notes |
| `species.jsonl` | JESS `symbol` | Names, formal charge, CAS or null, formula, source mass and source-wide usage count |
| `references.jsonl` | source reference `id` | Original label and citation, with PDF page; no fabricated DOI |
| `vocabularies.json` | source code | Meanings of all source weight and technique codes |
| `recommended-2023.json` | article Table 6 row | Separately attributed critically selected recommendations and conversion arithmetic; not observations |
| `*.pqi` | PHREEQC extension | Machine-generated representations of the published 25 °C recommendations |

`provenance.page` is one-based within the PDF; `bbox_points` uses pdfplumber's `(x0, top, x1, bottom)` coordinates in PDF points. A species heading and its numeric row can have different pages (`data_page`). Notes preserve their own page. Raw cells and the immutable source PDF allow every parsed parameter to be checked.

## Values, conditions and uncertainty

| Field | Rule |
|---|---|
| `value`, `value_raw` | Exact numeric string and complete source token respectively; apply `value_relation` before interpretation |
| `value_relation` | `=` for the tabulated representation or `<` when an explicit source note makes it an upper bound; equality does not imply exact physical knowledge |
| `quantity`, `unit` | `lgK`: base-10 conditional equilibrium constant under the source convention; `E`: V; `dG`/`dH`: kcal/mol by default or explicit kJ/mol; `Cp`: cal/(K mol) by default or explicit J/(K mol) |
| `deviation_type` | `SF` counts significant figures and is **not** a confidence interval; `SD` and `MD` retain the reported standard/maximum deviation without reinterpretation |
| `temperature_C` | Source degrees Celsius; no inferred temperature correction |
| `ionic_strength_raw` | Source numeric string, including values later contradicted by the source's own note |
| `ionic_strength` | Numeric condition usable for filtering, or null when missing/disclaimed; source row 54447:11 has raw `5` but effective null because the note says saturated, not 5 M |
| `ionic_strength_unit` | mol/dm³ by instruction default; mol/kg when the source medium has `/m`. Never combine these bases without additional information |
| `medium_raw`, `medium_qualifier` | Preserve exact text; a separate qualifier identifies variable NaOH/NaCl–NaOH media in 59434:1. “Unknown” and “Self Medium” are source labels, not resolved chemical compositions |
| `pressure_default` | Source instructions say “1 bar / 1 atm”; this ambiguity is retained, not silently converted |
| `reference_id` | Links the compilation's citation, not proof the original experiment was rechecked. Null is meaningful for compilation-derived values; 33 are blank in the source |
| `record_origin` | Derived classification from the technique code or an explicit calculation note. `ENS` is unspecified. A measurement technique code does not prove the tabulated number was directly measured |
| `source_status`, `source_annotation_flags` | Machine-readable source qualifications, including deprecated species, wrong-species data, an upper bound, saturated conditions and phase identity limitations |

All 537 source rows remain available, including 117 with source weight 0 (problematic/inconsistent). They are not 537 independent experiments. Multiple entries can cite compilations or re-express the same source reaction. The SQL/CLI minimum-weight filter is an access convenience, not a scientific selection procedure. Neither averaging the rows nor treating `SF` as an error bar is justified.

Reaction symbols include JESS composite species such as negative formal H counts. Their dictionary formula/charge, rather than guessed chemical-name parsing, is used for exact rational atom/charge checks. The electron's `E(1)` pseudoformula contributes charge but no chemical element. The species `source_count` refers to the whole JESS database, not occurrences in this subset. The table's mass-column unit is not stated explicitly; `molar_mass_raw` is retained without claiming an independently verified unit.

## Reviewed source-note exceptions

| Record / reaction | Typed interpretation | Source page |
|---|---|---:|
| 28606:2 | Source says the value belongs to DMannose; flag erroneous wrong species, retain raw value | GER 5 |
| 37342:2 | Source limit `<3.0`, not an ordinary equality | GER 8 |
| 54447:11 | Saturated ionic strength; literal 5 is explicitly rejected | GER 11 |
| 59434:1 | Variable NaOH or NaCl/NaOH medium | GER 17 |
| 54627, all four rows | GeO₂ polymorph not identified in original source; row 4 says probably hexagonal | GER 14 |
| 74246:2 | Original phase unspecified and reaction re-expressed by JESS | GER 24 |
| Notes saying deprecated | Flag the compilation's warning; do not infer an independently usable species from a balanced formula | Various |

Rules are source-version-specific and assert that the expected note remains present. Other editorial re-expressions stay in the full notes; the underlying 85 cited publications have not all been reacquired or empirically reassessed. Source contradictions are exposed, not adjudicated by this package.
