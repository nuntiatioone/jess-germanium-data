"""Executable practitioner task and an explicitly limited baseline comparison.

This checks access, input compatibility and mass-action arithmetic. It does not
validate empirical accuracy, activity-coefficient models or redox equilibrium.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata
import math
import platform
import statistics
import time
import urllib.request
from pathlib import Path

from recover import ROOT, read_json, write_json, query_records, sha256
from recommended import records, model_text


def acquire_comparators():
    receipts=[]
    for f in read_json(ROOT/'sources/comparators.json')['files']:
        p=ROOT/f['path']; cached=p.exists(); start=time.perf_counter()
        if not cached:
            b=urllib.request.urlopen(f['url'],timeout=60).read()
            if hashlib.sha256(b).hexdigest()!=f['sha256']:
                raise ValueError('Downloaded comparator hash mismatch: '+f['path'])
            p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
        if sha256(p)!=f['sha256'] or p.stat().st_size!=f['bytes']:
            raise ValueError('Comparator hash mismatch: '+f['path'])
        receipts.append({'path':f['path'],'cached':cached,'seconds':time.perf_counter()-start})
    return receipts


def solution(ph=9.2, full=False):
    # A synthetic, specified-pH NaCl solution, not an observed water sample.
    # Cl is adjusted to balance charge; all Ge calculations use mol/kg water.
    species=['Ge(OH)4','GeO(OH)3-','GeO2(OH)2-2']
    sum_expr='+'.join(f'MOL("{s}")' for s in species)
    if full:
        sum_expr+='+MOL("Ge+2")+8*MOL("Ge8(OH)35-3")'
        sum_expr+='+'+'+'.join(f'MOL("{s}")' for s in ['GeF6-2','GeHF6-','GeF4','GeF4(OH)-','GeF2(OH)+'])
    return f'''SELECTED_OUTPUT
    -reset false
    -high_precision true
USER_PUNCH
    -headings pH total_Ge log_a_neutral log_a_mono log_a_di sum_Ge ionic_strength
    -start
    10 PUNCH -LA("H+"), TOT("Ge"), LA("Ge(OH)4"), LA("GeO(OH)3-"), LA("GeO2(OH)2-2")
    20 PUNCH {sum_expr}, MU
    -end
SOLUTION 1
    temp 25
    pressure 0.9869232667
    pH {ph}
    pe 4
    units mol/kgw
    Na 0.01
    Cl 0.01 charge
    Ge 1e-6
END
'''


def execute(text):
    from phreeqpy.iphreeqc.phreeqc_dll import IPhreeqc
    start=time.perf_counter(); engine=IPhreeqc()
    try:
        engine.load_database(str(ROOT/'.cache/phreeqc-3.7.3.dat'))
        if engine.phc_database_error_count:
            raise ValueError(engine.get_error_string())
        accepted=True
        try:
            engine.run_string(text)
        except Exception:
            accepted=False
        error=engine.get_error_string()
        if not accepted and not error:
            raise RuntimeError('Engine failed without a diagnostic')
        return {'accepted':accepted,'diagnostic':error,'seconds':time.perf_counter()-start,
                'selected_output':engine.get_selected_output_array() if accepted else []}
    finally:
        engine.destroy_iphreeqc()


def alternative():
    found={}
    for name in ('inorganic_aq.csv','inorganic_cr.csv'):
        with (ROOT/'.cache/chnosz'/name).open(encoding='utf-8',newline='') as f:
            found[name]=[r for r in csv.DictReader(f) if 'Ge' in r['formula']]
    aqueous={r['name']:r for r in found['inorganic_aq.csv']}
    neutral=aqueous['Ge(OH)4']; mono=aqueous['GeO(OH)3-']
    assert neutral['E_units']==mono['E_units']=='cal'
    dg=float(mono['G'])-float(neutral['G'])  # H+ formation G=0 by convention
    denominator=(8.31446261815324/4.184)*298.15*math.log(10)
    return {'source':'CHNOSZ 2.3.0 OBIGT, pinned commit in sources/comparators.json',
            'method':'Direct arithmetic from stored standard molal G values; R/CHNOSZ was not executed',
            'temperature_K':298.15,'pressure_bar':1,'delta_G_cal_per_mol':dg,
            'calculated_pKa1_from_rounded_G':dg/denominator,
            'rounding_only_bound_if_each_G_rounded_to_nearest_100_cal_mol':100/denominator,
            'rounding_bound_is_statistical_uncertainty':False,
            'germanium_aqueous_species':[r['name'] for r in found['inorganic_aq.csv']],
            'germanium_solids':[{'name':r['name'],'formula':r['formula']} for r in found['inorganic_cr.csv']],
            'source_refs':sorted({r['ref1']+':'+r['ref2'] for r in found['inorganic_aq.csv']}),
            'raw_JESS_conditions_weights_notes_available':False,
            'dianion_available':any('GeO2(OH)2' in r['formula'] for r in found['inorganic_aq.csv']),
            'interpretation':'A maintained, useful executable alternative already exists for two aqueous species and both GeO2 polymorphs. The different pKa is not evidence that either source predicts observations more accurately.'}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    receipts=acquire_comparators()
    before=model_text(records(),original_web=True)+solution(full=True)
    after=model_text(records())+solution(full=True)
    old=execute(before); new=execute(after)
    assert not old['accepted'] and new['accepted'],(old,new)
    assert 'Ge+2' in old['diagnostic'] and 'GeF2(OH)-' in old['diagnostic'],old
    full_row=dict(zip(*new['selected_output']))
    assert abs(full_row['sum_Ge']-full_row['total_Ge'])<1e-14
    scenarios=[]
    for ph in (7.0,9.099,9.2,10.5):
        result=execute(model_text(records(),acid_only=True)+solution(ph))
        assert result['accepted'],result
        row=dict(zip(*result['selected_output']))
        residual1=row['log_a_mono']-row['pH']-row['log_a_neutral']-(-9.099)
        residual2=row['log_a_di']-row['pH']-row['log_a_mono']-(-12.76)
        cumulative=row['log_a_di']-2*row['pH']-row['log_a_neutral']-(-21.859)
        mass_residual=row['sum_Ge']-1e-6
        assert max(abs(residual1),abs(residual2),abs(cumulative))<1e-10
        assert abs(mass_residual)<1e-14
        assert abs(row['sum_Ge']-row['total_Ge'])<1e-14
        if ph==9.099:
            assert abs(row['log_a_mono']-row['log_a_neutral'])<1e-10
        scenarios.append({'input_pH':ph,'engine':row,'log_activity_ratio_residuals':[residual1,residual2],
                          'cumulative_log_activity_residual':cumulative,
                          'Ge_mass_balance_residual_mol_kgw':mass_residual})
    timings=[]
    for _ in range(101):
        start=time.perf_counter()
        answer=query_records(reaction_id=75139,temperature=25,min_weight=0)
        timings.append(time.perf_counter()-start)
    assert len(answer)==6
    assert [r['source_row'] for r in answer]==list(range(1,7))
    assert answer[1]['record_origin']=='calculated_value_reported_in_literature'
    write_json(ROOT/'results/practitioner-query.json',answer)
    import phreeqpy.iphreeqc.phreeqc_dll as binding
    module=Path(binding.__file__).parent
    native=list((module/'phreeqc3').glob('IPhreeqc-3.7.3.dll')) if platform.system()=='Windows' else []
    report={'resource_version':'0.1.1','synthetic_scenario_not_measurement':True,
      'environment':{'python':platform.python_version(),'platform':platform.platform(),
        'phreeqpy':importlib.metadata.version('phreeqpy'),
        'native_library':[{'name':p.name,'sha256':sha256(p)} for p in native]},
      'acquisition':receipts,'reference_page_as_written':old,'corrected_published_reactions':new,
      'negative_control_scope':'Same PHREEQC transcription, base database, solution and constants; only the two website equation errors differ.',
      'fixture_conditions':{'temperature_C':25,'pressure_atm':0.9869232667,'pressure_bar_approximately':1,
        'pe':4,'Ge_mol_kgw':1e-6,'Na_mol_kgw':0.01,'Cl':'adjusted for charge balance',
        'activity_model':'PHREEQC defaults: Davies for new charged species; default neutral expression'},
      'acid_base_mass_action_checks':scenarios,
      'query':{'reaction_id':75139,'temperature_C':25,'rows':len(answer),'repeats':len(timings),
        'first_seconds':timings[0],'median_seconds':statistics.median(timings[1:]),
        'p95_seconds':sorted(timings[1:])[94],
        'includes':['all six source rows','conditions and units','SF/SD/MD distinction','quality weight and meaning','technique','bibliographic link','calculated-value note','source page']},
      'best_open_machine_readable_alternative':alternative(),
      'limitations':['Input acceptance and mass-action residuals do not establish empirical validity.',
        'Only 25 C is supported by this conversion; no temperature dependence was fitted.',
        'PHREEQC default activity coefficients and base-water chemistry are modelling assumptions, not new Germanium measurements.',
        'Specified-pH NaCl solutions are synthetic validation fixtures; mass balance does not prove a field-water prediction.',
        'Full-model acceptance does not validate tentative redox, polynuclear or fluoride parameters.',
        'No timed human transcription experiment or monetary savings claim is made.']}
    write_json(ROOT/'results/demo.json',report)
    print({'before_accepted':old['accepted'],'after_accepted':new['accepted'],
           'checked_scenarios':len(scenarios),'query_rows':len(answer),'query_median_ms':report['query']['median_seconds']*1000})


if __name__=='__main__':
    main()
