# Verified Germanium data-access repair — 20 September 2026

We restored a usable path from preserved thermodynamic tables to qualified machine queries and executable reaction input. The bounded result is a versioned transcription of the JESS v8.9 Germanium subset and a contribution-ready correction to two equations on its maintainers' reference website. The archived database was **not lost**: its authors had already preserved it, and a newer JESS service survives.

Automated extraction and validation were supplemented by separate source-equation and note audits. Original data and recommendations remain the credited authors' work. No external expert review or maintainer endorsement is claimed.

## Why this target

The initial [Grömping CAs reference](https://github.com/ugroempi/CAs/blob/main/ColbournTables.md) demonstrates recovery of an inaccessible custodian-hosted resource. Its existing preservation and construction work made duplication unattractive. This companion follows that preservation pattern while addressing a different data-access gap.

JESS offered a more precise repair opportunity. The [v8.9 archive](https://doi.org/10.5281/zenodo.7700024) names a small compilation/preservation team, and the attached terms specifically name Bonet, Filella and May as the people authorised to render the database into PDFs. The [SC Database history](https://equilibriumdata.github.io/sc-database.html) documents a discontinued predecessor and partial PDF preservation. This is evidence of custodian dependence; it is not evidence that all underlying literature disappeared.

The [Germanium source assessment](https://doi.org/10.1016/j.apgeochem.2023.105631) identifies environmental chemistry and ecotoxicology as intended users of coherent aqueous equilibrium data. Practitioners need reaction conventions, conditions and source reliability to choose parameters and run speciation calculations. In this case, flattening PDFs loses qualifiers, while two website equation errors block an ordinary chemical-equilibrium import. These are demonstrated technical costs. Market size, commercial licence prices and speculative financial savings played no part in selection. No customer interview or downstream deployment is claimed.

## What survives, and what was repaired

| Layer | Verified state | Result of this work |
|---|---|---|
| Historical JESS v8.9 Germanium contents | Public, versioned PDFs with original notes and bibliography | Complete structured transcription; no lost original claimed |
| Current JESS service/software | [Live database access](https://jess.may.org.au/jess_databases.shtml) and [licensed software](https://jess.may.org.au/jess_supply.shtml) still exist | Successor acknowledged; no live-site bulk copy or engine replacement |
| Published 2023 recommendations | Article and author repository survive | Separately attributed machine-readable representation and PHREEQC extension |
| Reference webpage | Two equations disagree with the published table and fail balance checks | Minimal correction patch against a pinned commit; not submitted |
| Original empirical evidence | 85 citations retained; not all underlying papers reacquired | Uncertainty and provenance preserved; no new empirical validation claimed |
| Scientific gaps | Source assessment still regards parts of the chemistry as tentative | Unresolved; this conversion does not create missing measurements |

The source files, acquisition URLs, hashes, version and rights discrepancy are in `sources/manifest.json`. Public archive bytes were freshly downloaded and verified. The package includes the original terms and mandatory disclaimer; the article, whole upstream webpage and installed dependency binaries are not redistributed. See [RIGHTS.md](../RIGHTS.md).

## Actual restoration

The 44-page reaction PDF and 21-page species PDF yield **174 reactions, 537 parameter records, 223 participating species, 85 bibliographic entries and 85 notes**. These counts establish selected-scope completeness, not scientific novelty or a count of independent measurements. The 537 rows include 422 log K values, 32 potentials, 24 Gibbs energies, 52 enthalpies and 7 heat capacities. All 117 source-weight-zero rows remain available and identifiable.

Each row preserves source page, raw token/cells, units, temperature, ionic-strength basis, medium, quality weight, technique, citation and applicable notes. Bounds and other qualifications survive machine access. Examples include a source-stated `<3.0` limit, a wrong-sugar assignment, saturated ionic strength wrongly represented by a bare `5` in the numeric column, and a variable ionic medium. No inferred number replaces a missing observation. The original value and its qualified interpretation coexist.

The reference-page corrections are narrowly specified:

| Table 6 row | Website discrepancy | Published equation restored |
|---:|---|---|
| 1 | Four reactant protons omitted | Ge(OH)₄ + 2e⁻ + 4H⁺ = Ge²⁺ + 4H₂O |
| 11 | Difluorohydroxo product has the wrong charge sign | Ge(OH)₄ + 3H⁺ + 2F⁻ = GeF₂(OH)⁺ + 3H₂O |

All 11 numerical constants match the paper and are unchanged. Acid formation reactions are converted explicitly: reverse the first protonation to obtain log K = −9.099; reverse and add both protonations to obtain the cumulative dianion formation log K = −21.859. This is transparent algebra on published recommendations, not a new fit. The reference-page discrepancies were newly detected in this audit; priority or absence of an earlier report has not been established.

## Validation and practitioner demonstration

Two extraction mechanisms agree: table geometry via pdfplumber and independent content-stream parsing via pypdf. Every parameter field, reaction equation, note, linked species name/formula/charge and bibliography entry reconciles. All 174 source reactions and all 11 selected published equations pass exact rational atom/charge checks. Referential integrity, SQLite integrity and focused regression checks pass. Rendered pages were inspected for footnotes, continuation boundaries, final-page completeness, names and citations. Evidence is in `results/independent-extraction.json`, `validation.json`, `regression-tests.txt` and `visual-checks.json`.

**Task 1 — select traceable parameters.** `recover.py query --reaction-id 75139 --temperature 25 --min-weight 0` returns all six matching records, their conditions and bibliography, and the note identifying a calculated value. It differentiates significant figures from reported deviations. The full result is in `results/practitioner-query.json`; a default query excludes weight-zero records. Filtering on ionic strength no longer mistakes the source-disclaimed “5 M” entry for a known 5 M condition.

**Task 2 — import published reactions.** Using the same PHREEQC base, constants and synthetic solution, the page-as-written equations cause two species-equation failures (hydrogen/charge imbalance); the corrected set is accepted. Four acid-only fixtures at pH 7, 9.099, 9.2 and 10.5 verify activity-based mass action and total-Ge conservation. At pH 9.099, neutral and monoanion activities agree. This establishes a reproducible formerly blocked import and correct conversion arithmetic.

Fixtures specify 25 °C, approximately 1 bar, pe 4, 1 µmol Ge/kg water and a charge-balanced NaCl medium. The new species use PHREEQC's default activity model; this does not reproduce the source's SIT fitting procedure. Full-model acceptance does not validate redox/fluoride/polymer predictions. Missing enthalpy fits mean the extension must not be extrapolated to other temperatures. [PHREEQC species conventions](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-50.htm) and [solution defaults](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-48.htm) informed these explicit limits.

## Best accessible alternatives and measured improvement

| Alternative actually inspected | Existing capability | Increment established here |
|---|---|---|
| Original JESS PDFs | Full historical rows, notes and citations are readable | Repeatable qualified JSON/CSV/SQLite query and integrity checks; no claim of faster human reading measured |
| Live JESS, newer version | Browser reaction/data access remains available | Offline pinned historical snapshot; not a claim to supersede newer data or match its harmonisation |
| Maintainer reference page | Compact 11-reaction selected summary | Two source-verified equation repairs change a controlled import from rejected to accepted |
| CHNOSZ 2.3.0, pinned default inorganic files | Machine-readable Ge(OH)₄ and GeO(OH)₃⁻, both GeO₂ polymorphs and other Ge solids | Adds the JESS evidence layer and an executable representation of all 11 source recommendations; does not replace CHNOSZ's wider thermodynamic engine |

[CHNOSZ's current OBIGT documentation](https://chnosz.net/vignettes/OBIGT.html) and commit-pinned files were checked, not dismissed as obsolete. Direct arithmetic on its rounded standard Gibbs energies gives pKa₁ ≈ 9.31 at 25 °C, whereas the 2023 selected recommendation is 9.099. This discrepancy is preserved. The difference does **not** establish predictive superiority; approximately 0.073 pKa of worst-case rounding alone follows if each stored energy was rounded to the nearest 100 cal/mol, and that conditional rounding bound is not an empirical confidence interval. R/CHNOSZ itself was not executed.

`results/demo.json` records measured local query latency and native-engine timings. `results/reconstruction-cost.json` records fresh acquisition, cold reconstruction, independent verification, cached rebuild and storage costs. `results/reproducibility.json` establishes that all data files, including SQLite, reproduce byte for byte. These measured costs concern this fixed release. No guessed practitioner hours, salary savings or reduction in experimental uncertainty is asserted.

Final measured run on the shared Windows workstation (load was not controlled):

| Operation / storage | Measured cost |
|---|---:|
| Fresh download and hash verification of five source PDFs | 6.30 s |
| Cold PDF reconstruction | 37.37 s |
| Independent content-stream verification | 19.05 s |
| Rebuild from checked extraction cache | 0.32 s |
| Complete reproduction command, including patch/test checks | 64.33 s |
| Six-record qualified query, 100 repeated local calls | median 8.02 ms |
| Source PDFs / delivered data | 1.08 MB / 3.24 MB (decimal) |
| Local installed dependency directory | 241 MB; Python runtime can be outside it |

These are observed execution costs, not an estimate of human effort saved. Initial research, installation and review are additional preparation costs. Future source-change review costs were not measured.

## Status and handoff

Downloaded: five hash-verified existing archive files. Transcribed: complete selected PDFs. Reconstructed: new machine-readable and PHREEQC representations, **not recovered historical executables**. Verified: source fidelity, record links, chemical balance, controlled import, mass-action arithmetic and repeatable bytes. Newly measured scientific observations: **none**. Independently generated replacement measurements: **none**.

This release is an unofficial versioned companion and a minimal upstream patch, with a [preservation and maintenance plan](MAINTENANCE.md). The upstream patch has not been submitted. Independent domain-expert review and empirical reassessment remain future work.
