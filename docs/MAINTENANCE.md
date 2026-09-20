# Contribution and preservation plan

## Smallest useful upstream contribution

The intended first contribution is `patches/equilibriumdata-germanium.patch`, targeting `TCE/germanium.md` at commit `8ed9e849f49d1a8cfdf4b77c4bad4374d2e588a2`. It changes two equation strings and no constants. `sources/upstream.json` and `results/upstream-patch.json` pin the source and resulting hashes. The proposed contribution text is in `patches/PROPOSED-CONTRIBUTION.md`.

The complete extraction can be offered as an optional machine-readable companion to the existing JESS/Zenodo preservation effort if its maintainers want it. Do not create a competing public database by default. Do not call this an official JESS release, replace the current JESS engine, or claim author endorsement.

The dataset is prepared for public distribution. No upstream issue or pull request has been submitted. Before contributing the patch, check whether the two equations have already been fixed and follow the maintainer's contribution process. Automated checks do not substitute for domain-expert review.

## Maintain the pinned release

1. Preserve the source files, terms, manifests, machine-readable output, scripts, lockfiles and checks together. `SHA256SUMS` detects byte changes. The deterministic ZIP can be rebuilt from a clean verified checkout.
2. Preserve immutable versioned releases and verify downloaded copies. A GitHub repository is one preservation copy; retain a separate archive with source terms and checksums. Do not treat an unverified backup or proposed archival deposit as completed.
3. Before each substantive reuse, run `integrity.py check`. Rebuild in a copy when revalidating measured reports. No ongoing paid service, scheduler or automatic network monitor is necessary for an immutable release.
4. For a new source version, inspect the attached rights first, acquire to a **new** version directory, pin hashes, and compare identifiers, rows, notes, bibliographic links and conditions. Never silently replace v8.9 with live v9 data. A changed input hash is a review event, not a reason to disable the check.
5. Re-run independent extraction, source-note regressions, exact balance and native PHREEQC fixtures. Review every added/removed row and changed note; the parser intentionally fails on unknown geometry/tokens. Render affected pages and check them visually. New notes require a scientific interpretation review, especially limits, incorrect labels and nonnumeric conditions.
6. Record source changes separately from conversion corrections. Use a patch version for a parser/documentation repair, a minor version for additional independently validated coverage, and a major schema version for incompatible field semantics. Keep source IDs stable and issue explicit supersession links if source rows move.

## Measured and unmeasured maintenance cost

`results/reconstruction-cost.json` measures a full PDF rebuild, an independent second-parser check, a hash-checked cached rebuild and byte-for-byte output comparison on this machine. `results/demo.json` measures local query and native-engine execution. These are the repeatable compute costs for the **same** source version. They exclude initial investigation, download latency, dependency installation and future scientific review; those must not be presented as zero.

The current archive is small enough for a local release. Dependency storage is much larger than the source PDFs; its measured local size is included in the cost report. A new upstream version's manual review cost is unknown and depends on its changes. No monetary saving, staffing estimate or annual maintenance commitment is asserted.

## Reusable recovery method

The reusable result is a workflow, not a universal PDF parser: classify the alleged loss; check successors and rights; pin original bytes; preserve record grain and raw tokens; type qualifications hidden in prose; use a genuinely different extraction path; check domain invariants; reproduce a blocked task with a controlled negative case; measure rebuild costs; propose the smallest upstream repair.

This case exposed two traps that should be retained in future work: a later archive index does not prove later child artifacts (the CAs reference case), and a numeric table cell can be explicitly contradicted by its own footnote. Counts and successful parsing cannot establish empirical validity.
