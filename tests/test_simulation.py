import unittest

from agent_core.simulation import build_enterprise, evaluate_enterprise, run_simulation


class SimulationTests(unittest.TestCase):
    def control(self, result, control_id):
        return next(c for c in result['controls'] if c['control_id'] == control_id)

    def test_baseline_has_linked_assets_and_eight_controls(self):
        result = run_simulation('baseline')
        self.assertEqual(len(result['enterprise']['people']), 50)
        self.assertEqual(len(result['controls']), 8)
        self.assertTrue(all(c['status'] == 'Compliant' for c in result['controls']))
        ids = {p['id'] for p in result['enterprise']['people']}
        self.assertTrue(all(a['person_id'] in ids for a in result['enterprise']['accounts']))
        self.assertTrue(all(a['person_id'] in ids for a in result['enterprise']['devices']))

    def test_training_missing_for_eight_sales_people(self):
        control = self.control(run_simulation('training'), 'A.6.3')
        self.assertEqual(control['status'], 'Partially Compliant')
        self.assertEqual(len(control['findings']), 8)
        self.assertTrue(control['evidences'])

    def test_new_hire_missing_nda(self):
        result = run_simulation('new-hire')
        self.assertEqual(len(self.control(result, 'A.6.6')['findings']), 1)

    def test_offboarding_checks_accounts_and_laptop(self):
        control = self.control(run_simulation('offboarding'), 'A.6.5')
        self.assertNotEqual(control['status'], 'Compliant')
        evidence_id = control['findings'][0]['evidence_id']
        observed = next(e for e in control['evidences'] if e['evidence_id'] == evidence_id)['content']
        self.assertTrue(observed['active_accounts'])
        self.assertTrue(observed['unreturned_devices'])

    def test_remote_and_reporting_scenarios(self):
        self.assertNotEqual(self.control(run_simulation('remote'), 'A.6.7')['status'], 'Compliant')
        self.assertNotEqual(self.control(run_simulation('phishing'), 'A.6.8')['status'], 'Compliant')

    def test_missing_evidence_is_not_compliant(self):
        enterprise = build_enterprise()
        enterprise['people'][0]['nda_signed'] = None
        self.assertEqual(self.control({'controls': evaluate_enterprise(enterprise)}, 'A.6.6')['status'], 'Insufficient Evidence')

    def test_missing_account_inventory_is_not_compliant(self):
        enterprise = build_enterprise()
        enterprise['accounts'] = None
        self.assertEqual(self.control({'controls': evaluate_enterprise(enterprise)}, 'A.6.5')['status'], 'Insufficient Evidence')

    def test_runs_are_independent(self):
        run_simulation('offboarding')
        first = run_simulation('baseline')
        first['enterprise']['people'][0]['nda_signed'] = False
        self.assertTrue(run_simulation('baseline')['enterprise']['people'][0]['nda_signed'])

    def test_unknown_scenario_and_mode(self):
        with self.assertRaises(ValueError):
            run_simulation('unknown')
        with self.assertRaises(ValueError):
            run_simulation('baseline', 'unknown')


if __name__ == '__main__':
    unittest.main()
