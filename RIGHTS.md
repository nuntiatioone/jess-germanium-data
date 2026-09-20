# Attribution, rights and disclaimer

## Original archive

Bonet, Josep; Filella, Montserrat; May, Peter M.; May, Ruth F.; Murray, Kevin (2023). **JESS Thermodynamic database of chemical reactions**, Zenodo, published 5 March 2023, DOI [10.5281/zenodo.7700024](https://doi.org/10.5281/zenodo.7700024). The selected Germanium PDFs identify JESS v8.9 and 24-Jan-2023. Original literature citations are retained per record in `data/references.jsonl`.

JESS intellectual-property rights are retained by its owners. This package relies on the attached [Licence, copyright and disclaimer](sources/jess-8.9/03-Licence%20copyright%20and%20disclaimer.pdf), whose final paragraph permits anyone to use the PDF contents freely with appropriate attribution, subject to its disclaimer. It also requires that dissemination include that disclaimer. The complete attached terms accompany this package; they govern the JESS material and its transformed contents.

**Required source disclaimer, transcribed from the attached licence:**

> Whilst considerable effort is made to ensure that JESS and JPD are error-free and user-friendly, we give no warranties. All JESS material is made available on an 'as is' basis, under the condition that you use it entirely at your own risk. No person or agency involved in JESS development assumes any responsibility for losses incurred through the use of JESS or of its documentation.

The archive's Zenodo metadata say `zenodo-freetoread-1.0`; the [Murdoch catalogue](https://researchportal.murdoch.edu.au/esploro/outputs/dataset/JESS-Thermodynamic-database-of-chemical-reactions/991005571670207891) labels it CC BY 4.0. We retain this discrepancy and do **not** replace the attached specific terms with a blanket CC BY licence. The attached first paragraph names people authorised to create the PDF compilation; this package does not claim to be that original compilation or to own its rights.

The current JESS website has [separate copying restrictions](https://jess.may.org.au/disclaimer.shtml). Its live database was inspected only to establish that a successor survives; it is not the acquisition source for the distributed records. JESS software/source code is not included or reimplemented.

## Published recommendations and website correction

Filella, M.; May, P. M. (2023). **The aqueous solution chemistry of germanium under conditions of environmental and biological interest: Inorganic ligands.** Applied Geochemistry 155, 105631. [DOI](https://doi.org/10.1016/j.apgeochem.2023.105631); [author repository](https://archive-ouverte.unige.ch/unige:169459).

The article is CC BY-NC-ND 4.0. The article PDF, figures and altered article are not distributed. `recommended-2023.json` records scientific values/equations with attribution and explicit conversion arithmetic; no new empirical result is claimed. The minimal patch targets the existing [equilibriumdata reference page](https://equilibriumdata.github.io/TCE/germanium.html). Its complete Markdown page is not redistributed; repository licensing was not established. The upstream patch is supplied for review and has not been submitted or accepted.

## New code and comparison dependencies

Original scripts and tests in `src/` and `tests/` are provided under [MIT](LICENSE-CODE). This grant does not relicense source data, publications or other software. The accompanying original documentation may be reused with attribution to this project; preserve source notices and the distinction between historical data and this conversion.

CHNOSZ 2.3.0 (GPL-3) is a maintained comparison source, acquired separately by the demo. PhreeqPy 0.6.0 (BSD-3-Clause) and its native PHREEQC library are installed separately; their notices remain in their distributions. The pinned USGS PHREEQC database is acquired separately. No dependency binaries are in this release.

## Verification credit

This conversion was prepared with automated extraction and validation, with separate source-equation and note audits. It has not received external expert review. Original scientific and preservation work remains attributed above.
