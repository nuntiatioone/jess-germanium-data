"""Regression cases exposed by actual archive and source-note failures."""
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from recover import query_records, balance_reaction


def rows(name):
    return [json.loads(s) for s in (ROOT/'data'/name).read_text(encoding='utf-8').splitlines()]


class PreservationRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters={r['id']:r for r in rows('parameters.jsonl')}
        cls.reactions={r['id']:r for r in rows('reactions.jsonl')}
        cls.species={r['symbol']:r for r in rows('species.jsonl')}

    def test_continuation_and_final_page_are_not_dropped(self):
        self.assertEqual(self.reactions[80937]['provenance']['page'],37)
        continued=self.parameters['JESS-8.9:Ge:80907:1']['notes']
        self.assertTrue(any(n['page']==32 and 'simplified here' in n['text'] for n in continued))

    def test_source_note_changes_numeric_semantics_without_erasing_raw_cell(self):
        bounded=self.parameters['JESS-8.9:Ge:37342:2']
        self.assertEqual((bounded['value'],bounded['value_relation']),('3.0','<'))
        self.assertEqual(bounded['value_raw'],'lgK:3.0(2SF)')
        self.assertEqual(self.parameters['JESS-8.9:Ge:28606:2']['source_status'],'erroneous_wrong_species')
        saturated=self.parameters['JESS-8.9:Ge:54447:11']
        self.assertEqual(saturated['ionic_strength_raw'],'5')
        self.assertIsNone(saturated['ionic_strength'])
        ids={r['id'] for r in query_records(reaction_id=54447,ionic_strength=5,min_weight=0)}
        self.assertNotIn(saturated['id'],ids)
        self.assertIn('variable',self.parameters['JESS-8.9:Ge:59434:1']['medium_qualifier'])

    def test_query_carries_calculation_note_and_uncertainty_semantics(self):
        answer=query_records(reaction_id=75139,temperature=25,min_weight=0)
        self.assertEqual(len(answer),6)
        self.assertEqual(answer[1]['record_origin'],'calculated_value_reported_in_literature')
        self.assertIn('Calculated from',answer[1]['notes'][0]['text'])
        self.assertEqual(answer[1]['deviation_type'],'SF')
        self.assertEqual(answer[3]['deviation_type'],'MD')
        self.assertEqual(answer[4]['deviation_type'],'SD')
        self.assertTrue(answer[1]['reference']['citation_raw'])

    def test_balance_check_detects_the_actual_website_errors(self):
        missing_protons={'equation_normalized':'Ge+4_OH-1(4) + 2<e-1> = Ge+2 + 4<H2O>'}
        result=balance_reaction(missing_protons,self.species)
        self.assertNotEqual(result['status'],'balanced')
        from recommended import records
        self.assertTrue(all(r['balance']['status']=='balanced' for r in records()))


if __name__=='__main__':
    unittest.main()
