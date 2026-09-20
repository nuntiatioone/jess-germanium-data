# Germanium equilibrium data: usable archive and checked import

Version **0.1.1**, 20 September 2026. A contribution package built on the existing **JESS v8.9** preservation effort and **Filella & May (2023)**. Unofficial companion resource; the original maintainers have not endorsed this conversion.

The result is an offline, queryable transcription of the complete Germanium reaction/species PDFs, plus a checked PHREEQC conversion of 11 published recommendations. A minimal patch fixes two equation transcription errors in the maintained reference webpage. The original paper's numbers are unchanged.

- [Result, evidence and comparison](docs/REPORT.md)
- [Bounded acceptance criteria](docs/SCOPE.md)
- [Data dictionary and uncertainty](docs/DATA-DICTIONARY.md)
- [Provenance, rights and required disclaimer](RIGHTS.md)
- [Maintainer contribution and preservation plan](docs/MAINTENANCE.md)
- [Minimal upstream patch](patches/equilibriumdata-germanium.patch)

[Download the complete v0.1.1 bundle](jess-germanium-data-0.1.1.zip), including source PDFs, data, scripts and validation reports.

## Use without installing packages

The JSONL, CSV and SQLite files in `data/` are ready to use. Python 3.12's standard library is sufficient for the query and integrity commands:

```powershell
python src/integrity.py check
python src/recover.py query --reaction-id 75139 --temperature 25 --min-weight 0
```

This returns all six 25 °C source records, with conditions, units, quality weights, uncertainty notation, calculation notes, citation and PDF page. Results are historical parameter records, **not six independent new measurements**. The default minimum weight is 1; set 0 to include source-marked problematic records. Even weight 1 means only “no information but consistent,” not a recommendation.

For SQL, `parameters.document` contains the complete JSON record. `parameters.ionic_strength` is the qualified numeric condition; the source's literal value is `document.ionic_strength_raw`. Always retain `value_relation`, notes and units when exporting values. `NULL` is not zero.

## Rebuild and validate

Tested on Windows 11, Python 3.12.14. A conventional local environment works:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe src/recover.py acquire
.\.venv\Scripts\python.exe src/recover.py build
.\.venv\Scripts\python.exe src/check_stream.py
.\.venv\Scripts\python.exe src/recommended.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`python src/reproduce.py` additionally tests fresh acquisition into a temporary directory, times the reconstruction/checks, compares all regenerated data bytes, and checks that the patch applies. It requires Git as well as the core Python dependencies.

`acquire` obtains missing files from the pinned Zenodo release and refuses changed hashes. Included source PDFs make the core rebuild usable offline after dependencies are installed. The default build re-extracts both PDFs; `build --cache` uses a source-hash/package-version-checked extraction cache. `recommended.py` needs the pinned upstream Markdown once to regenerate the contribution patch; that whole page is cached locally, not redistributed.

Run the native PHREEQC demonstration separately:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-demo.lock.txt
.\.venv\Scripts\python.exe src/demo.py
```

The demo downloads hash-pinned CHNOSZ comparison files and the matching PHREEQC 3.7.3 base database into `.cache/`. It demonstrates the two rejected website equations, accepted corrections, and activity/mass-balance checks in four synthetic solutions. The `.pqi` files are **extensions**, not complete databases. Use the acid-only extension for the narrow acid–base demonstration. The full extension includes tentative redox and fluoride recommendations and assumes one redox-equilibrated total-Ge pool.

These conversions support **25 °C only**. Missing temperature and activity-coefficient parameters have not been reconstructed. Input acceptance establishes usable syntax and chemical balance, not experimental accuracy or reproduction of JESS's harmonisation/SIT machinery.

## Integrity and release

`SHA256SUMS` verifies the delivered snapshot, including source PDFs, code, data and recorded results. Rebuilding rewrites measured result timings, so verify the release **before** rebuilding, or rebuild in a fresh copy. Data output reproducibility is separately recorded in `results/reproducibility.json`. `python src/integrity.py package` creates the deterministic release ZIP; `seal` is for deliberately issuing a reviewed new snapshot, never for concealing a failed check.

Original measurements, compilation, preservation and thermodynamic recommendations belong to the credited source authors. Automated verification is not external expert review.
