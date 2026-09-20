"""Transparent transcription of Filella & May (2023), Table 6 (not raw data).

The numerical recommendations are prior work. Equations are mapped to the
archived JESS species dictionary and separately to PHREEQC input syntax.
"""
from decimal import Decimal
from pathlib import Path
import difflib
import hashlib
import json
import urllib.request

from recover import ROOT, balance_reaction, write_json, read_json

# Table order is preserved. The strings express scientific facts; the article
# itself is not included or modified. The two public-page discrepancies are
# retained below, never mixed into the archived observation records.
TABLE = [
    (1, '-7.206', 'Ge+4_OH-1(4) + 2<e-1> + 4<H+1> = Ge+2 + 4<H2O>',
     'Ge(OH)4 + 2 e- + 4 H+ = Ge+2 + 4 H2O'),
    (2, '12.76', 'GeO2_OH-1(2) + H+1 = GeO+2_OH-1(3)', None),
    (3, '9.099', 'GeO+2_OH-1(3) + H+1 = Ge+4_OH-1(4)', None),
    (4, '28.33', '8<Ge+4_OH-1(4)> + 3<OH-1> = Ge+4(8)_OH-1(35)',
     '8 Ge(OH)4 + 3 OH- = Ge8(OH)35-3'),
    (5, '-1.373', 'GeO2(hexag,s) + 2<H2O> = Ge+4_OH-1(4)', None),
    (6, '-4.999', 'GeO2(tetrag,s) + 2<H2O> = Ge+4_OH-1(4)', None),
    (7, '27.98', 'Ge+4_OH-1(4) + 4<H+1> + 6<F-1> = Ge+4_F-1(6) + 4<H2O>',
     'Ge(OH)4 + 4 H+ + 6 F- = GeF6-2 + 4 H2O'),
    (8, '28.80', 'Ge+4_OH-1(4) + 5<H+1> + 6<F-1> = Ge+4_H+1_F-1(6) + 4<H2O>',
     'Ge(OH)4 + 5 H+ + 6 F- = GeHF6- + 4 H2O'),
    (9, '20.14', 'Ge+4_OH-1(4) + 4<H+1> + 4<F-1> = Ge+4_F-1(4) + 4<H2O>',
     'Ge(OH)4 + 4 H+ + 4 F- = GeF4 + 4 H2O'),
    (10, '19.08', 'Ge+4_OH-1(4) + 3<H+1> + 4<F-1> = Ge+4_F-1(4)_OH-1 + 3<H2O>',
     'Ge(OH)4 + 3 H+ + 4 F- = GeF4(OH)- + 3 H2O'),
    (11, '9.345', 'Ge+4_OH-1(4) + 3<H+1> + 2<F-1> = Ge+4_F-1(2)_OH-1 + 3<H2O>',
     'Ge(OH)4 + 3 H+ + 2 F- = GeF2(OH)+ + 3 H2O'),
]


def records():
    species = {s['symbol']:s for s in map(json.loads,(ROOT/'data/species.jsonl').read_text(encoding='utf-8').splitlines())}
    rows=[]
    for row,value,equation,phreeqc in TABLE:
        obj={'id':f'FilellaMay2023:Table6:{row}', 'table_row':row,
             'record_class':'published_critically_selected_recommendation',
             'is_observation':False,'new_measurement':False,'log10_K':value,
             'temperature_C':'25','pressure_bar':'1','ionic_strength':'0','standard_state':'infinite dilution; source standard thermodynamic convention',
             'equation_normalized':equation,'phreeqc_direct_equation':phreeqc,
             'source':{'doi':'10.1016/j.apgeochem.2023.105631','table':6,'printed_page':9,'repository_pdf_page':10},
             'uncertainty':'Not a statistical error bar. Table footnote retains four significant figures to limit arithmetic rounding, not to assert four-digit physical accuracy.',
             'limitations':'Source assessment: redox data especially tentative; halogen complexes poorly investigated; no new fit or empirical verification.'}
        obj['balance']=balance_reaction(obj,species)
        assert obj['balance']['status']=='balanced',obj
        rows.append(obj)
    return rows


def model_text(rows, original_web=False, acid_only=False):
    # Formation conventions required by PHREEQC: invert row3; combine inverted
    # row2+row3 to express the dianion from the neutral primary master species.
    byrow={r['table_row']:r for r in rows}
    pka1=Decimal(byrow[3]['log10_K']); pka2=Decimal(byrow[2]['log10_K'])
    lines=[
      '# Filella & May 2023 Table 6; 25 C, infinite-dilution reference constants.',
      '# Machine-readable transcription and format conversion; not a new assessment.',
      '# Do not use at other temperatures: no temperature-dependence fit supplied.',
      '# Extension: requires a compatible base database defining H+, OH-, e-, F-, H2O.',
      '# Missing activity parameters use PHREEQC defaults, not the source SIT model.',
      '# Full extension: total Ge equilibrates at specified pe; no separate valence pools.',
      'SOLUTION_MASTER_SPECIES','Ge Ge(OH)4 0 Ge 72.63','SOLUTION_SPECIES',
      'Ge(OH)4 = Ge(OH)4','    log_k 0',
      'Ge(OH)4 = GeO(OH)3- + H+',f'    log_k {-pka1}',
      'Ge(OH)4 = GeO2(OH)2-2 + 2 H+',f'    log_k {-pka1-pka2}',
    ]
    if not acid_only:
        for row in (1,4,7,8,9,10,11):
            r=byrow[row]
            eq=r['phreeqc_direct_equation']
            if original_web and row==1:
                eq=eq.replace(' + 4 H+','')
            if original_web and row==11:
                eq=eq.replace('GeF2(OH)+','GeF2(OH)-')
            lines += [eq,f"    log_k {r['log10_K']}"]
        lines += ['PHASES','GeO2_hexagonal_FM2023','GeO2 + 2 H2O = Ge(OH)4',f"    log_k {byrow[5]['log10_K']}",
                  'GeO2_tetragonal_FM2023','GeO2 + 2 H2O = Ge(OH)4',f"    log_k {byrow[6]['log10_K']}"]
    return '\n'.join(lines)+'\n'


def upstream_patch():
    m=read_json(ROOT/'sources/upstream.json')
    local=ROOT/'.cache/germanium-upstream.md'
    if not local.exists():
        local.parent.mkdir(exist_ok=True)
        local.write_bytes(urllib.request.urlopen(m['url'],timeout=60).read())
    if hashlib.sha256(local.read_bytes()).hexdigest()!=m['sha256']:
        raise ValueError('Pinned upstream Markdown changed')
    before=local.read_text(encoding='utf-8')
    old1='Ge(OH)<sub>4</sub> + 2 e<sup>-</sup> = Ge<sup>2+</sup>'
    new1='Ge(OH)<sub>4</sub> + 2 e<sup>-</sup> + 4 H<sup>+</sup> = Ge<sup>2+</sup>'
    old2='= GeF<sub>2</sub>(OH)<sup>-</sup> + 3 H<sub>2</sub>O'
    new2='= GeF<sub>2</sub>(OH)<sup>+</sup> + 3 H<sub>2</sub>O'
    if before.count(old1)!=1 or before.count(old2)!=1:
        raise ValueError('Expected upstream context does not match')
    after=before.replace(old1,new1).replace(old2,new2)
    diff=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/TCE/germanium.md',tofile='b/TCE/germanium.md',n=2))
    (ROOT/'patches/equilibriumdata-germanium.patch').write_text(diff,encoding='utf-8',newline='\n')
    # Whole upstream page stays in local cache; only minimal contribution patch ships.
    write_json(ROOT/'results/upstream-patch.json',{'base_commit':m['commit'],'file':m['file'],
      'base_sha256':m['sha256'],'patched_sha256':hashlib.sha256(after.encode()).hexdigest(),
      'changed_reactions':[1,11],'numeric_constants_changed':False,'published':False,
      'checks':'Checked against Table 6 in two separate equation comparisons; chemical balance and PHREEQC checks are separate results.'})


def main():
    rows=records()
    write_json(ROOT/'data/recommended-2023.json',{'resource_version':'0.1.1','records':rows,
       'conversion_rules':[{'target':'GeO(OH)3- formation','source_rows':[3],'operation':'reverse','log10_K':'-9.099'},
                           {'target':'GeO2(OH)2-2 formation','source_rows':[2,3],'operation':'reverse both, add and cancel intermediate','log10_K':'-21.859'}]})
    (ROOT/'data/germanium-2023.pqi').write_text(model_text(rows),encoding='utf-8',newline='\n')
    (ROOT/'data/germanium-acid-only-2023.pqi').write_text(model_text(rows,acid_only=True),encoding='utf-8',newline='\n')
    upstream_patch()
    print(json.dumps({'recommendations':len(rows),'balanced':sum(r['balance']['status']=='balanced' for r in rows),'patch':'patches/equilibriumdata-germanium.patch'}))


if __name__=='__main__':
    main()
