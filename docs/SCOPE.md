# Bounded completion criteria

Target: the Germanium reaction and species PDFs in **JESS Thermodynamic Database v8.9**, DOI **10.5281/zenodo.7700024**, and the 11-reaction summary on the existing equilibriumdata Germanium page.

Complete when:

1. Exact input files are pinned by version, URL, size, repository checksum and SHA-256, with reproducible acquisition and an offline integrity check.
2. Every reaction table and species entry in the selected PDFs is represented in documented JSON/CSV/SQLite, with raw strings, page provenance, source quality weights, techniques, references, notes, conditions and explicit nulls. No inferred value is inserted as an observation.
3. A second extraction path checks all parameter rows; mass/charge and referential integrity checks expose contradictions rather than silently rewriting sources. Source fidelity is distinguished from scientific validity.
4. The reference-page discrepancies are checked against the source paper and chemical balance, and a minimal patch is prepared against a pinned upstream revision. Corrected representations stay separate from original transcriptions.
5. A practitioner task demonstrates reliable parameter retrieval and reaction import, compares with the best accessible free alternatives actually inspected, and reports preparation/rebuild/query costs with honest limits.
6. Attribution, rights, uncertainty, preservation and maintenance instructions accompany the versioned local deliverable. The companion is prepared for public distribution; the upstream patch remains unsubmitted.

This is a restoration of usable **access and validation**, not recovery of a lost JESS database, a new measurement, a new fitted thermodynamic model, or a replacement for the maintained/licensed JESS software. Historical records, calculated estimates and published recommendations remain separate classes. More decimal digits do not imply smaller uncertainty.
