"""Reproducible, fail-closed recovery of the pinned JESS v8.9 Germanium PDFs.

Source rows are never changed to repair chemistry. Raw and parsed values coexist.
The geometry extractor is checked separately by check_stream.py (pypdf).
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sqlite3
import sys
import time
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.1"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_manifest():
    m = read_json(ROOT / "sources/manifest.json")
    paths = [f["path"] for f in m["files"]]
    if len(set(paths)) != len(paths):
        raise ValueError("Duplicate source paths")
    return m


def verify_sources():
    verified = []
    for f in source_manifest()["files"]:
        p = ROOT / f["path"]
        b = p.read_bytes()
        if len(b) != f["size"] or hashlib.sha256(b).hexdigest() != f["sha256"]:
            raise ValueError(f"Source integrity failure: {p}")
        if "md5:" + hashlib.md5(b).hexdigest() != f["repository_checksum"]:
            raise ValueError(f"Repository checksum failure: {p}")
        verified.append(f["id"])
    return verified


def acquire():
    receipts = []
    for f in source_manifest()["files"]:
        p = ROOT / f["path"]
        start = time.perf_counter()
        cached = p.exists()
        if not cached:
            req = urllib.request.Request(f["url"], headers={"User-Agent": "JESS-Ge-preservation/0.1 (local research)"})
            with urllib.request.urlopen(req, timeout=60) as response:
                b = response.read()
            if hashlib.sha256(b).hexdigest() != f["sha256"]:
                raise ValueError(f"Downloaded source differs from pinned input: {f['url']}")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
        receipts.append({"source": f["id"], "cached": cached,
                         "seconds": time.perf_counter() - start,
                         "checked_utc": datetime.now(timezone.utc).isoformat()})
    verify_sources()
    write_json(ROOT / "results/acquisition.json", receipts)
    print(json.dumps({"verified_source_files": len(receipts), "downloaded_now": sum(not r["cached"] for r in receipts)}))


def extracted_pages(name, use_cache=False):
    import pdfplumber
    p = ROOT / "sources/jess-8.9" / name
    cache = ROOT / ".cache" / (name + ".extraction.json")
    digest = sha256(p)
    if use_cache and cache.exists():
        saved = read_json(cache)
        if saved["sha256"] == digest and saved["pdfplumber"] == pdfplumber.__version__:
            return saved["pages"]
    pages = []
    with pdfplumber.open(p) as pdf:
        for number, page in enumerate(pdf.pages, 1):
            pages.append({"page": number, "text": page.extract_text(), "tables": [
                {"bbox": t.bbox, "rows": [{"bbox": row.bbox, "cells": cells}
                                          for row, cells in zip(t.rows, t.extract())]}
                for t in page.find_tables()]})
    write_json(cache, {"sha256": digest, "pdfplumber": pdfplumber.__version__, "pages": pages})
    return pages


def cleaned_cells(cells):
    return [c.strip() for c in cells if c is not None]


def raw_provenance(filename, page, bbox=None):
    return {"source_file": filename, "page": page, "bbox_points": bbox,
            "doi": "10.5281/zenodo.7700024"}


def exact_number(s):
    if s == "":
        return None
    Decimal(s)  # fail rather than coerce unsupported text
    return s


VALUE = re.compile(r"^(lgK|E|dG|dH|Cp):([+-]?(?:\d+(?:\.\d*)?|\.\d+))\(([\d.]+)(SF|SD|MD)\)(kJ|J/K)?$")


def observation(cells, reaction_id, page, bbox):
    original_cells = cells.copy()
    # Thin PDF rules sometimes merge Value/W or W/Tech; accept only explicit grammar.
    if len(cells) == 7:
        m = re.fullmatch(r"(.+\)(?:kJ|J/K)?) ([0-9])", cells[4])
        n = re.fullmatch(r"([0-9]) ([A-Z]{3})", cells[5])
        if m:
            cells = cells[:4] + list(m.groups()) + cells[5:]
        elif n:
            cells = cells[:5] + list(n.groups()) + cells[6:]
    if len(cells) != 8:
        raise ValueError(f"Unsupported observation geometry: {reaction_id}, p{page}: {cells}")
    no, temp, ionic, medium, value_raw, weight, technique, ref = cells
    value = VALUE.fullmatch(value_raw)
    if not value:
        raise ValueError(f"Unsupported value: {reaction_id}:{no}: {value_raw}")
    kind, magnitude, deviation, deviation_type, explicit_unit = value.groups()
    if kind == "lgK":
        unit = "log10 equilibrium constant (source concentration/activity convention)"
    elif kind == "E":
        unit = "V"
    elif kind in ("dG", "dH"):
        unit = "kJ mol-1" if explicit_unit == "kJ" else "kcal mol-1"
    else:
        unit = "J K-1 mol-1" if explicit_unit == "J/K" else "cal K-1 mol-1"
    return {"id": f"JESS-8.9:Ge:{reaction_id}:{no}", "reaction_id": reaction_id,
            "source_row": int(no), "temperature_C": exact_number(temp),
            "ionic_strength_raw": exact_number(ionic),
            "ionic_strength": exact_number(ionic),
            "ionic_strength_qualifier": "numeric_as_tabulated" if ionic else "not_reported",
            "ionic_strength_unit": ("mol kg-1" if "/m" in medium else "mol dm-3") if ionic else None,
            "ionic_strength_unit_basis": "explicit /m medium marker" if "/m" in medium else "Instructions default" if ionic else "missing",
            "medium_raw": medium or None, "medium_qualifier": "as_tabulated; consult notes", "solvent_default": "water unless otherwise specified in source",
            "pressure_default": "1 bar / 1 atm unless explicitly specified (source ambiguity retained)",
            "quantity": kind, "value": magnitude, "unit": unit,
            "value_relation": "=", "source_status": "as_tabulated",
            "source_phase_identity": None,
            "value_raw": value_raw, "deviation_value": deviation,
            "deviation_type": deviation_type,
            "deviation_meaning": {"SF": "significant figures; not an uncertainty interval", "SD": "standard deviation as reported", "MD": "maximum deviation as reported"}[deviation_type],
            "weight": int(weight), "technique": technique, "reference_id": int(ref) if ref else None,
            "record_origin": "unspecified" if technique == "ENS" else "calculated_or_compiled" if technique.startswith(("E", "C")) or technique == "MDG" else "literature_measurement_technique",
            "record_origin_basis": "derived classification from source technique; not proof that the tabulated value was directly measured",
            "empirical_validity": "not independently remeasured; retain source weight and notes",
            "raw_cells": original_cells, "provenance": raw_provenance("GER.PDF", page, bbox)}


def reactions_and_observations(pages):
    reactions, observations = {}, []
    current = None
    table_rows = 0
    reached_assessments = False
    for p in pages:
        for table in p["tables"]:
            if any("Weight" in row["cells"] and "Assessment" in row["cells"] for row in table["rows"]):
                reached_assessments = True
                break
            for row in table["rows"]:
                c = cleaned_cells(row["cells"])
                nonempty = [s for s in c if s]
                if not nonempty:
                    continue
                text = "\n".join(nonempty)
                header = re.fullmatch(r"Reaction No\. (\d+)", text)
                if header:
                    current = int(header[1])
                    if current in reactions:
                        raise ValueError(f"Repeated reaction id {current}")
                    reactions[current] = {"id": current, "equation_raw": None, "notes": [],
                                          "provenance": raw_provenance("GER.PDF", p["page"], row["bbox"])}
                elif c[0].isdigit():
                    if current is None:
                        raise ValueError("Orphan observation")
                    observations.append(observation(c, current, p["page"], row["bbox"]))
                    table_rows += 1
                elif text.startswith("No\n") or text == "No":
                    pass
                elif text.startswith("Note"):
                    reactions[current]["notes"].append({"text": text, "page": p["page"]})
                elif " = " in text:
                    if current is None or reactions[current]["equation_raw"] is not None:
                        raise ValueError(f"Orphan/repeated equation: {text}")
                    bits = re.split(r"\n(?=Note(?: \(\d+\))?:)", text)
                    reactions[current]["equation_raw"] = bits[0]
                    reactions[current]["notes"].extend({"text": n, "page": p["page"]} for n in bits[1:])
                else:
                    raise ValueError(f"Unrecognised table row p{p['page']}: {text}")
        if reached_assessments:
            break
    expected_ids = [int(i) for p in pages for i in re.findall(r"Reaction No\.\s*(\d+)", p["text"])]
    if set(reactions) != set(expected_ids) or len(reactions) != len(expected_ids):
        raise ValueError("Reaction headers do not reconcile with page text")
    for r in reactions.values():
        if r["equation_raw"] is None:
            raise ValueError(f"Missing equation: {r['id']}")
        r["equation_normalized"] = re.sub(r"\s+", " ", r["equation_raw"]).replace(" >", ">")
        r["status"] = "transcribed_existing_published_record"
    # A note continuing onto p32 is above the first closed table border. Reconcile
    # ALL notes through the page text, including such unboxed continuations.
    notes = extract_notes(pages)
    for r in reactions.values():
        geometry_notes = {" ".join(n["text"].split()) for n in r["notes"]}
        text_notes = {" ".join(n["text"].split()) for n in notes.get(r["id"], [])}
        if not geometry_notes <= text_notes:
            raise ValueError(f"Note extraction disagreement for {r['id']}")
        r["notes"] = notes.get(r["id"], [])
    for o in observations:
        applicable = []
        for n in reactions[o["reaction_id"]]["notes"]:
            m = re.match(r"Note \((\d+)\):", n["text"])
            if not m or int(m[1]) == o["source_row"]:
                applicable.append(n)
        o["notes"] = applicable
        if any("Calculated from" in n["text"] for n in applicable):
            o["record_origin"] = "calculated_value_reported_in_literature"
            o["record_origin_basis"] = "explicit source row note"
        apply_source_annotations(o)
    return list(reactions.values()), observations


def apply_source_annotations(o):
    """Type explicit source corrections while retaining the original table cells.

    These are reviewed rules for this pinned archive, not language-model inference
    applied at run time. Fail closed if the expected source note changes.
    """
    note_text = " ".join(n['text'] for n in o['notes'])
    o['source_annotation_flags'] = []
    if 'deprecated' in note_text:
        o['source_status'] = 'deprecated_species'
        o['source_annotation_flags'].append('source_deprecates_species')
    if o['id'] == 'JESS-8.9:Ge:28606:2':
        assert 'Error, this value is for DMannose' in note_text
        o['source_status'] = 'erroneous_wrong_species'
        o['source_annotation_flags'].append('source_reports_wrong_species')
    elif o['id'] == 'JESS-8.9:Ge:37342:2':
        assert '<3.0' in note_text
        o['value_relation'] = '<'
        o['source_status'] = 'upper_bound_in_source_note'
        o['source_annotation_flags'].append('tabulated_number_is_upper_bound')
    elif o['id'] == 'JESS-8.9:Ge:54447:11':
        assert 'I is saturated, not 5 M' in note_text
        o['ionic_strength'] = None
        o['ionic_strength_qualifier'] = 'saturated; source explicitly rejects tabulated 5 M'
        o['source_annotation_flags'].append('tabulated_ionic_strength_disclaimed_by_source')
    elif o['id'] == 'JESS-8.9:Ge:59434:1':
        assert 'Ionic media variable, either NaOH or mix NaCl and NaOH' in note_text
        o['medium_qualifier'] = 'variable: NaOH or NaCl/NaOH mixture; not uniformly NaOH'
        o['source_annotation_flags'].append('variable_ionic_medium')
    if o['reaction_id'] == 54627:
        assert 'Polymorph of GeO2 not identified' in note_text
        o['source_phase_identity'] = 'probably hexagonal, not identified' if o['source_row']==4 else 'not identified in original source'
        o['source_annotation_flags'].append('compiled_phase_identity_exceeds_original_source')
    if o['id'] == 'JESS-8.9:Ge:74246:2':
        assert 'Phase not specified in source' in note_text
        o['source_phase_identity'] = 'not specified in original source'
        o['source_annotation_flags'].append('source_reaction_reexpressed_with_unspecified_phase')


def extract_notes(pages):
    notes = collections.defaultdict(list)
    current = None
    pending = None
    for p in pages:
        for line in p["text"].splitlines():
            s = line.strip()
            if not s or s.startswith(("JESS Thermodynamic", "doi:", "– Page ")):
                continue
            if s == "Data Assessment":
                return dict(notes)
            m = re.fullmatch(r"Reaction No\. (\d+)", s)
            if m:
                current, pending = int(m[1]), None
            elif s.startswith("Note"):
                pending = {"text": s, "page": p["page"]}
                notes[current].append(pending)
            elif s.startswith("No t ") or re.match(r"\d+ \d+ .*?(?:lgK|E|dH|dG|Cp):", s):
                pending = None
            elif pending is not None:
                pending["text"] += "\n" + s
    return dict(notes)


def species(pages):
    found = []
    pending = None
    for p in pages:
        for table in p["tables"]:
            for row in table["rows"]:
                c = cleaned_cells(row["cells"])
                nonempty = [s for s in c if s]
                if not nonempty or "Charge" in nonempty:
                    continue
                if re.fullmatch(r"-?\d+", c[0]):
                    if pending is None or len(c) != 5:
                        raise ValueError(f"Unsupported species data p{p['page']}: {c}")
                    charge, cas, count, formula, mass = c
                    pending.update({"charge": int(charge), "cas": None if cas == "---" else cas,
                                    "source_count": int(count), "formula_raw": formula,
                                    "molar_mass_raw": mass, "molar_mass_unit": "source column Mol. mass (unit not stated on table)",
                                    "raw_cells": c, "data_page": p["page"]})
                    found.append(pending)
                    pending = None
                elif len(nonempty) == 1:
                    if pending is not None:
                        raise ValueError(f"Orphan species heading: {pending}")
                    lines = nonempty[0].splitlines()
                    pending = {"symbol": lines[0], "names_raw": "\n".join(lines[1:]) or None,
                               "provenance": raw_provenance("GES.PDF", p["page"], row["bbox"])}
                else:
                    raise ValueError(f"Unsupported species row p{p['page']}: {c}")
    if pending is not None:
        raise ValueError("Last species has no data")
    if len({s["symbol"] for s in found}) != len(found):
        raise ValueError("Duplicate species symbol")
    return found


def reference_data(pages):
    refs, techniques, weights = [], {}, {}
    state = None
    current = None
    for p in pages:
        for line in p["text"].splitlines():
            s = line.strip()
            if not s or s.startswith(("JESS Thermodynamic", "doi:", "– Page ")):
                continue
            if s == "Data Assessment":
                state = "weight"
            elif s == "Techniques":
                state = "technique"
            elif s == "References":
                state = "reference"
            elif s.startswith("Reference No.:"):
                m = re.fullmatch(r"Reference No\.: (\d+)\((.+)\)", s)
                if not m:
                    raise ValueError(s)
                current = {"id": int(m[1]), "label": m[2], "citation_raw": "", "provenance": raw_provenance("GER.PDF", p["page"])}
                refs.append(current)
            elif state == "reference" and current:
                current["citation_raw"] += ("\n" if current["citation_raw"] else "") + s
            elif state == "weight" and re.match(r"\d ", s):
                n, desc = s.split(" ", 1)
                weights[n] = desc
            elif state == "technique" and re.match(r"[A-Z]{3} ", s):
                n, desc = s.split(" ", 1)
                techniques[n] = desc
    return refs, techniques, weights


def composition(formula):
    if formula == "":
        return {}
    parts = re.findall(r"([A-Z][a-z]?)\((-?\d+)\)", formula)
    if "".join(f"{e}({n})" for e, n in parts) != formula:
        raise ValueError(f"Unsupported formula {formula!r}")
    return {e: int(n) for e, n in parts}


def stoichiometry(equation):
    left, right = equation.split(" = ")
    result = collections.defaultdict(Fraction)
    for side, sign in ((left, -1), (right, 1)):
        tokens = re.split(r" (\+|-) ", side)
        next_sign = sign
        for token in tokens:
            if token in ("+", "-"):
                next_sign = sign if token == "+" else -sign
                continue
            token = token.strip()
            m = re.fullmatch(r"([\d.]+)<(.+)>", token)
            coefficient, symbol = (Fraction(m[1]), m[2].strip()) if m else (Fraction(1), token)
            if " " in symbol or "<" in symbol or ">" in symbol:
                raise ValueError(f"Unsupported reaction token {token!r}")
            result[symbol] += next_sign * coefficient
    return {s: n for s, n in result.items() if n}


def balance_reaction(reaction, species_index):
    try:
        terms = stoichiometry(reaction["equation_normalized"])
        atoms = collections.defaultdict(Fraction)
        charge = Fraction(0)
        for symbol, coefficient in terms.items():
            s = species_index[symbol]
            # E(1) denotes the electron, not a chemical element; its charge counts.
            comp = {} if symbol == "e-1" else composition(s["formula_raw"])
            for e, n in comp.items():
                atoms[e] += coefficient * n
            charge += coefficient * s["charge"]
        residual = {e: str(n) for e, n in atoms.items() if n}
        return {"status": "balanced" if not residual and not charge else "source_discrepancy",
                "atom_residual_products_minus_reactants": residual, "charge_residual": str(charge),
                "terms": {s: str(n) for s, n in terms.items()}}
    except (ValueError, KeyError) as exc:
        return {"status": "unresolved", "reason": str(exc)}


def validate(reactions, observations, sp, refs, techniques, weights):
    errors = []
    ri = {r["id"]: r for r in reactions}
    si = {s["symbol"]: s for s in sp}
    ref_ids = {r["id"] for r in refs}
    seen = set()
    for o in observations:
        if o["id"] in seen:
            errors.append(f"duplicate {o['id']}")
        seen.add(o["id"])
        if o["reaction_id"] not in ri or o["technique"] not in techniques or str(o["weight"]) not in weights:
            errors.append(f"broken record link: {o['id']}")
        if o["reference_id"] is not None and o["reference_id"] not in ref_ids:
            errors.append(f"broken reference {o['id']} -> {o['reference_id']}")
    for r in reactions:
        row_nums = sorted(o["source_row"] for o in observations if o["reaction_id"] == r["id"])
        if row_nums != list(range(1, len(row_nums) + 1)):
            errors.append(f"non-contiguous observations {r['id']}: {row_nums}")
        r["balance"] = balance_reaction(r, si)
    return {"resource_version": VERSION, "counts": {"reactions": len(ri), "parameter_records": len(observations), "species": len(si), "references": len(refs)},
            "referential_integrity_errors": errors,
            "balance_counts": dict(collections.Counter(r["balance"]["status"] for r in reactions)),
            "source_discrepancies": [{"reaction_id": r["id"], "equation": r["equation_raw"], "provenance": r["provenance"], "balance": r["balance"]} for r in reactions if r["balance"]["status"] != "balanced"],
            "quantity_counts": dict(collections.Counter(o["quantity"] for o in observations)),
            "weight_counts": dict(collections.Counter(str(o["weight"]) for o in observations)),
            "missing_conditions": {"temperature": sum(o["temperature_C"] is None for o in observations), "ionic_strength_source_blank": sum(o["ionic_strength_raw"] is None for o in observations), "ionic_strength_effective_unknown": sum(o["ionic_strength"] is None for o in observations)},
            "source_annotation_counts":dict(collections.Counter(flag for o in observations for flag in o['source_annotation_flags'])),
            "scientific_validation": "Checks establish transcription structure and chemical balance only, not empirical accuracy or a self-consistent selected thermodynamic database."}


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8", newline="\n")


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def write_database(path, reactions, observations, sp, refs):
    # Build into a new file so failures never destroy a previous usable snapshot.
    tmp = path.with_suffix(".sqlite.tmp")
    if tmp.exists():
        tmp.unlink()
    with closing(sqlite3.connect(tmp)) as db:
        db.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE reactions(id INTEGER PRIMARY KEY, equation TEXT NOT NULL, balance_status TEXT NOT NULL, source_page INTEGER NOT NULL, document TEXT NOT NULL);
        CREATE TABLE species(symbol TEXT PRIMARY KEY, charge INTEGER NOT NULL, formula TEXT NOT NULL, names TEXT, document TEXT NOT NULL);
        CREATE TABLE literature(id INTEGER PRIMARY KEY, label TEXT NOT NULL, citation TEXT NOT NULL, document TEXT NOT NULL);
        CREATE TABLE parameters(id TEXT PRIMARY KEY, reaction_id INTEGER NOT NULL REFERENCES reactions(id), quantity TEXT NOT NULL,
          value_text TEXT NOT NULL, temperature_C REAL, ionic_strength REAL, ionic_strength_unit TEXT, medium TEXT, weight INTEGER NOT NULL,
          technique TEXT NOT NULL, reference_id INTEGER REFERENCES literature(id), source_page INTEGER NOT NULL, document TEXT NOT NULL);
        CREATE INDEX parameter_conditions ON parameters(quantity,temperature_C,ionic_strength,weight);
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        jd = lambda r: json.dumps(r, ensure_ascii=False, sort_keys=True)
        db.executemany("INSERT INTO reactions VALUES(?,?,?,?,?)", [(r["id"],r["equation_normalized"],r["balance"]["status"],r["provenance"]["page"],jd(r)) for r in reactions])
        db.executemany("INSERT INTO species VALUES(?,?,?,?,?)", [(s["symbol"],s["charge"],s["formula_raw"],s["names_raw"],jd(s)) for s in sp])
        db.executemany("INSERT INTO literature VALUES(?,?,?,?)", [(r["id"],r["label"],r["citation_raw"],jd(r)) for r in refs])
        db.executemany("INSERT INTO parameters VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", [(o["id"],o["reaction_id"],o["quantity"],o["value"],o["temperature_C"],o["ionic_strength"],o["ionic_strength_unit"],o["medium_raw"],o["weight"],o["technique"],o["reference_id"],o["provenance"]["page"],jd(o)) for o in observations])
        db.execute("INSERT INTO metadata VALUES(?,?)", ("resource_version",VERSION))
        db.execute("INSERT INTO metadata VALUES(?,?)", ("source_manifest_sha256",sha256(ROOT / "sources/manifest.json")))
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("SQLite integrity failure")
        db.commit()
    tmp.replace(path)


def build(use_cache=False):
    started = time.perf_counter()
    verify_sources()
    pages = extracted_pages("GER.PDF",use_cache)
    sp_pages = extracted_pages("GES.PDF",use_cache)
    reactions, observations = reactions_and_observations(pages)
    sp = species(sp_pages)
    refs, techniques, weights = reference_data(pages)
    report = validate(reactions,observations,sp,refs,techniques,weights)
    if report["referential_integrity_errors"]:
        raise ValueError(report["referential_integrity_errors"])
    out = ROOT / "data"
    out.mkdir(exist_ok=True)
    for name, rows in (("reactions",reactions),("parameters",observations),("species",sp),("references",refs)):
        write_jsonl(out / (name+".jsonl"), rows)
        write_csv(out / (name+".csv"), rows)
    write_json(out / "vocabularies.json", {"weights":weights,"techniques":techniques})
    write_json(out / "resource.json", read_json(ROOT/'sources/resource-template.json'))
    write_database(out / "jess-ge.sqlite", reactions,observations,sp,refs)
    write_json(ROOT / "results/validation.json", report)
    write_json(ROOT / "results/build-cost.json", {"seconds":time.perf_counter()-started,"used_extraction_cache":use_cache,"resource_version":VERSION,"input_bytes":sum(f['size'] for f in source_manifest()['files']),"output_bytes":sum(p.stat().st_size for p in out.glob('*') if p.is_file())})
    print(json.dumps(report,ensure_ascii=False,indent=2))


def query_records(contains="", quantity="lgK", min_weight=1, temperature=None,
                  ionic_strength=None, reaction_id=None):
    vocab = read_json(ROOT/'data/vocabularies.json')
    with closing(sqlite3.connect(f"file:{(ROOT/'data/jess-ge.sqlite').as_posix()}?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute("""SELECT p.document,r.equation,r.balance_status,l.document AS literature
            FROM parameters p JOIN reactions r ON p.reaction_id=r.id LEFT JOIN literature l ON p.reference_id=l.id
            WHERE p.quantity=? AND p.weight>=? AND (? IS NULL OR p.temperature_C=?)
            AND (? IS NULL OR p.ionic_strength=?) AND (? IS NULL OR p.reaction_id=?)
            AND instr(r.equation,?)>0 ORDER BY p.reaction_id, CAST(json_extract(p.document,'$.source_row') AS INTEGER)""",
            (quantity,min_weight,temperature,temperature,ionic_strength,ionic_strength,
             reaction_id,reaction_id,contains)).fetchall()
    answer=[]
    for row in rows:
        obj=json.loads(row['document'])
        obj.update(equation=row['equation'],balance_status=row['balance_status'],
                   reference=json.loads(row['literature']) if row['literature'] else None,
                   weight_meaning=vocab['weights'][str(obj['weight'])],
                   technique_meaning=vocab['techniques'][obj['technique']])
        answer.append(obj)
    return answer


def query(args):
    print(json.dumps(query_records(args.contains,args.quantity,args.min_weight,args.temperature,
                                  args.ionic_strength,args.reaction_id),ensure_ascii=False,indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command",required=True)
    subs.add_parser("acquire")
    subs.add_parser("verify-sources")
    b = subs.add_parser("build")
    b.add_argument("--cache",action="store_true",help="Reuse hash/version-checked local PDF extraction; default rebuilds it")
    q = subs.add_parser("query")
    q.add_argument("--contains",default="")
    q.add_argument("--quantity",choices=["lgK","E","dG","dH","Cp"],default="lgK")
    q.add_argument("--min-weight",type=int,choices=range(10),default=1)
    q.add_argument("--temperature",type=float)
    q.add_argument("--ionic-strength",type=float)
    q.add_argument("--reaction-id",type=int)
    args = parser.parse_args()
    if args.command == "acquire": acquire()
    elif args.command == "verify-sources": print(json.dumps({"verified":verify_sources()}))
    elif args.command == "build": build(args.cache)
    else: query(args)


if __name__ == "__main__":
    main()
