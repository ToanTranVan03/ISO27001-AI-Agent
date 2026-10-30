import copy
import tempfile
import unittest
from datetime import date
from agent_core.evidence_context import valid_retention
from agent_core.live import LiveMonitor
from agent_core.simulation import evaluate_enterprise
from agent_core.research_benchmark import advanced_cases, case_snapshot, predictions, score, run_case, run_study, paired_analysis


class EvidenceContextTests(unittest.TestCase):
    def test_advanced_cases_match_all_labels_and_workflow_plans(self):
        for case in advanced_cases():
            with self.subTest(case=case['id']):
                result = run_case(case, 'workflow')
                self.assertTrue(result['success'], result)
                self.assertTrue(result['exact_match'], result)
                self.assertTrue(result['required_tools_found'], result)
                self.assertTrue(result['all_choices_valid'])

    def test_exception_scope_approval_expiry_and_malformed_values_cannot_bypass(self):
        case = next(c for c in advanced_cases() if c['id'] == 'retention-approved')
        account = next(a for a in case_snapshot(case)['accounts'] if a['id'] == 'HF-025-HR')
        self.assertTrue(valid_retention(account, date(2026, 10, 31)))
        self.assertFalse(valid_retention(account, date(2026, 11, 1)))
        for field, value in [('approved', 'true'), ('scope', 'all'), ('account_id', 'HF-025-VPN'), ('approver', None), ('reason', ''), ('expires_on', 'invalid')]:
            changed = copy.deepcopy(account)
            changed['retention_exception'][field] = value
            self.assertFalse(valid_retention(changed, date(2026, 10, 30)), field)
        account['retention_exception'] = 'approved'
        self.assertFalse(valid_retention(account, date(2026, 10, 30)))
        vpn = next(a for a in case_snapshot(case)['accounts'] if a['id'] == 'HF-025-VPN')
        vpn['retention_exception'] = {'account_id': vpn['id'], 'scope': 'offboarding-retention',
                                     'approved': True, 'approver': 'IT', 'reason': 'Request', 'expires_on': '2026-10-31'}
        self.assertFalse(valid_retention(vpn, date(2026, 10, 30)))

    def test_conflicting_false_hr_and_true_lms_do_not_create_unverified_violation(self):
        case = next(c for c in advanced_cases() if c['id'] == 'training-source-conflict')
        enterprise = case_snapshot(case)
        person = next(p for p in enterprise['people'] if p['id'] == 'HF-042')
        person.update(training_passed=False, lms_training_passed=True)
        result = predictions(evaluate_enterprise(enterprise))
        self.assertIn(('A.6.3', 'HF-042', 'missing'), result)
        self.assertNotIn(('A.6.3', 'HF-042', 'finding'), result)

    def test_live_temporal_conflict_role_and_exception_lifecycles(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = LiveMonitor(directory, mode='workflow')
            for cause, repair, expected in [('training_expired', 'training_complete', ('A.6.3', 'HF-042', 'finding')),
                                            ('training_conflict', 'training_complete', ('A.6.3', 'HF-042', 'missing')),
                                            ('role_change', 'role_review', ('A.6.5', 'HF-042', 'finding'))]:
                monitor.change('HF-042', cause)
                self.assertIn(expected, predictions(monitor.state()['controls']))
                monitor.process_pending()
                monitor.change('HF-042', repair)
                monitor.process_pending()
                self.assertFalse(predictions(monitor.state()['controls']))
            with self.assertRaises(ValueError):
                monitor.change('HF-042', 'retention_approve')
            monitor.change('HF-025', 'terminate')
            monitor.change('HF-025', 'retention_request')
            self.assertIn(('A.6.5', 'HF-025', 'finding'), predictions(monitor.state()['controls']))
            monitor.change('HF-025', 'retention_approve')
            self.assertFalse(predictions(monitor.state()['controls']))
            monitor.change('HF-025', 'retention_expire')
            self.assertIn(('A.6.5', 'HF-025', 'finding'), predictions(monitor.state()['controls']))
            monitor.change('HF-025', 'recover_access')
            self.assertFalse(predictions(monitor.state()['controls']))

    def test_repeated_paired_study_has_same_snapshots_and_reports_variance(self):
        # No LLM in unit tests; an empty selection yields no trials, not fabricated results.
        result = run_study((), paired=True, repeats=3)
        self.assertEqual(result['case_count'], 0)
        self.assertEqual(result['summary']['ai']['trials'], 0)
        self.assertIsNone(result['summary']['ai']['stdev_ms'])

    def test_simulation_clock_expiry_changes_evidence_without_changing_account(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = LiveMonitor(directory, mode='workflow')
            for action in ['terminate', 'retention_request', 'retention_approve']:
                monitor.change('HF-025', action)
            self.assertFalse(predictions(monitor.state()['controls']))
            monitor.change('HF-025', 'advance_day')
            self.assertFalse(predictions(monitor.state()['controls']))
            monitor.change('HF-025', 'advance_day')
            state = monitor.state()
            self.assertIn(('A.6.5', 'HF-025', 'finding'), predictions(state['controls']))
            self.assertEqual(state['events'][0]['changes'][0]['record_id'], 'SIM-CLOCK')
            self.assertEqual(state['enterprise']['assessment_date'], '2026-11-01')
            monitor.process_pending()
            self.assertEqual(monitor.state()['status'], 'complete')

    def test_pair_audit_detects_unbalanced_or_different_snapshots(self):
        rows = [dict(case_id='case', mode=mode, snapshot_hash='same', success=True, exact_match=True,
                     elapsed_ms=1, tool_calls=0, model_calls=0) for mode in ('rules', 'workflow', 'ai')]
        self.assertTrue(paired_analysis(rows, 1)['same_snapshots'])
        self.assertTrue(paired_analysis(rows, 1)['balanced_trials'])
        rows[-1]['snapshot_hash'] = 'changed'
        self.assertFalse(paired_analysis(rows, 1)['same_snapshots'])
        self.assertFalse(paired_analysis(rows[:-1], 1)['balanced_trials'])
