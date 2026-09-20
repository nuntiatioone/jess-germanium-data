"""Independent PDF-content-stream cross-check, using pypdf, not table geometry.

Does not import the production parser. Checks every parameter and species numeric
row and reaction-header set. This verifies transcription, not the cited experiments.
"""
from pathlib import Path
from collections import Counter
import json
import re
import sys
import time
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
ROW = re.compile(r"^\s*(\d+)\s+("+NUM+r")\s+(.*?)((?:lgK|E|dG|dH|Cp):\S+)\s+([0-9])\s+([A-Z]{3})(?:\s+(\d+))?\s*$")
SPECIES_ROW = re.compile(r"^\s*(-?\d+)\s+(---|\d+-\d+-\d+)\s+(\d+)\s+(.*?)\s+("+NUM+r")\s*$")


def jsonl(name):
    return [json.loads(s) for s in (ROOT / "data" / name).read_text(encoding="utf-8").splitlines()]


def check():
    started = time.perf_counter()
    observed = jsonl("parameters.jsonl")
    source = []
    headers = []
    current = None
    source_equations = {}
    collecting_equation = False
    source_notes = []
    pending_note = None
    for page_no, page in enumerate(PdfReader(ROOT/"sources/jess-8.9/GER.PDF").pages, 1):
        for line in page.extract_text(extraction_mode="layout").splitlines():
            flat = " ".join(line.split())
            if not flat or flat.startswith(("JESS Thermodynamic", "doi:", "– Page ")):
                continue
            header = re.match(r"^\s*Reaction No\.\s*(\d+)\s*$",line)
            if header:
                current = int(header[1])
                headers.append(current)
                source_equations[current] = ""
                collecting_equation = True
                pending_note = None
                continue
            if flat == "Data Assessment":
                collecting_equation = False
                pending_note = None
            if flat.startswith("Note"):
                collecting_equation = False
                pending_note = [current,page_no,flat]
                source_notes.append(pending_note)
                continue
            if flat.startswith("No t "):
                collecting_equation = False
                pending_note = None
            match = ROW.fullmatch(line)
            if match:
                pending_note = None
                number, temp, middle, value, weight, tech, reference = match.groups()
                condition = middle.strip()
                if condition:
                    parts = re.fullmatch(r"("+NUM+r")\s+(.+)",condition)
                    if not parts:
                        raise ValueError(f"Unsupported condition p{page_no}: {condition}")
                    ionic, medium = parts.groups()
                    medium = " ".join(medium.split())
                else:
                    ionic, medium = None, None
                source.append((current,int(number),temp,ionic,medium,value,int(weight),tech,int(reference) if reference else None,page_no))
            elif collecting_equation:
                source_equations[current] += (" " if source_equations[current] else "") + flat
            elif pending_note is not None:
                pending_note[2] += " " + flat
    normalized = [(o['reaction_id'],o['source_row'],o['temperature_C'],o['ionic_strength_raw'],o['medium_raw'],o['value_raw'],o['weight'],o['technique'],o['reference_id'],o['provenance']['page']) for o in observed]
    missing = list((Counter(source)-Counter(normalized)).elements())
    extra = list((Counter(normalized)-Counter(source)).elements())
    expected_headers = [r['id'] for r in jsonl('reactions.jsonl')]
    equations_mismatched = [r['id'] for r in jsonl('reactions.jsonl') if source_equations.get(r['id'],'').replace(' >','>') != r['equation_normalized']]
    normalized_notes = [(r['id'],n['page'],' '.join(n['text'].split())) for r in jsonl('reactions.jsonl') for n in r['notes']]
    note_missing = list((Counter(tuple(n) for n in source_notes)-Counter(normalized_notes)).elements())
    note_extra = list((Counter(normalized_notes)-Counter(tuple(n) for n in source_notes)).elements())
    species_source = []
    species_headers = []
    pending_species = []
    pending_species_page = None
    started_species = False
    for page_no,page in enumerate(PdfReader(ROOT/'sources/jess-8.9/GES.PDF').pages,1):
        for line in page.extract_text(extraction_mode='layout').splitlines():
            flat = ' '.join(line.split())
            if not flat or flat.startswith(('JESS Thermodynamic','doi:','– Page ')):
                continue
            if flat.startswith('Charge CAS Count'):
                started_species = True
                continue
            if not started_species:
                continue
            m=SPECIES_ROW.fullmatch(line)
            if m:
                charge,cas,count,formula,mass=m.groups()
                species_source.append((int(charge),None if cas=='---' else cas,int(count),formula.strip(),mass,page_no))
                if not pending_species:
                    raise ValueError('Species data without a heading')
                species_headers.append((pending_species[0],' '.join(pending_species[1:]) or None,pending_species_page,
                                        int(charge),formula.strip()))
                pending_species=[]
                pending_species_page=None
            else:
                if not pending_species:
                    pending_species_page=page_no
                pending_species.append(flat)
    if pending_species:
        raise ValueError('Species heading without data')
    species_normalized = [(s['charge'],s['cas'],s['source_count'],s['formula_raw'],s['molar_mass_raw'],s['data_page']) for s in jsonl('species.jsonl')]
    species_missing=list((Counter(species_source)-Counter(species_normalized)).elements())
    species_extra=list((Counter(species_normalized)-Counter(species_source)).elements())
    resource_headers=[(s['symbol'],' '.join(s['names_raw'].split()) if s['names_raw'] else None,
                       s['provenance']['page'],s['charge'],s['formula_raw']) for s in jsonl('species.jsonl')]
    species_heading_missing=list((Counter(species_headers)-Counter(resource_headers)).elements())
    species_heading_extra=list((Counter(resource_headers)-Counter(species_headers)).elements())
    bibliography=[]
    reference=None
    for page_no,page in enumerate(PdfReader(ROOT/'sources/jess-8.9/GER.PDF').pages,1):
        for line in page.extract_text(extraction_mode='layout').splitlines():
            flat=' '.join(line.split())
            if not flat or flat.startswith(('JESS Thermodynamic','doi:','– Page ')):
                continue
            heading=re.fullmatch(r'Reference No\.: (\d+)\((.+)\)',flat)
            if heading:
                reference=[int(heading[1]),heading[2],page_no,'']
                bibliography.append(reference)
            elif reference is not None:
                reference[3]+= (' ' if reference[3] else '')+flat
    resource_bibliography=[(r['id'],r['label'],r['provenance']['page'],' '.join(r['citation_raw'].split()))
                           for r in jsonl('references.jsonl')]
    reference_missing=list((Counter(tuple(r) for r in bibliography)-Counter(resource_bibliography)).elements())
    reference_extra=list((Counter(resource_bibliography)-Counter(tuple(r) for r in bibliography)).elements())
    result={
        'method':'pypdf content-stream line extraction; no production-parser import',
        'reaction_headers':len(headers), 'reaction_header_set_matches': sorted(headers)==sorted(expected_headers),
        'parameter_rows_in_independent_source':len(source), 'parameter_rows_in_resource':len(normalized),
        'parameter_fields_compared':['reaction_id','row','temperature','ionic_strength','medium','value/deviation/unit token','weight','technique','reference','page'],
        'source_rows_missing_from_resource':missing,'resource_rows_not_in_source':extra,
        'equation_mismatches':equations_mismatched,
        'notes_in_independent_source':len(source_notes),'notes_in_resource':len(normalized_notes),
        'source_notes_missing_from_resource':note_missing,'resource_notes_not_in_source':note_extra,
        'species_numeric_rows_in_source':len(species_source),'species_numeric_rows_in_resource':len(species_normalized),
        'species_fields_compared':['charge','CAS','source count','formula','molar mass','page'],
        'species_missing':species_missing,'species_extra':species_extra,
        'species_heading_fields_compared':['symbol','names','heading page','linked charge','linked formula'],
        'species_heading_missing':species_heading_missing,'species_heading_extra':species_heading_extra,
        'bibliography_entries':len(bibliography),'bibliography_missing':reference_missing,'bibliography_extra':reference_extra,
        'passed':not(missing or extra or species_missing or species_extra or equations_mismatched or note_missing or note_extra or species_heading_missing or species_heading_extra or reference_missing or reference_extra) and sorted(headers)==sorted(expected_headers),
        'seconds':time.perf_counter()-started,
        'limits':'Independent text/geometry extraction establishes source fidelity, not empirical validity. Selected rendered pages additionally checked during preparation.'}
    (ROOT/'results/independent-extraction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result['passed']


if __name__=='__main__':
    sys.exit(0 if check() else 1)
