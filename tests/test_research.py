import tempfile
import unittest
from unittest.mock import patch
from agent_core.autonomous import AgentStore, agent_events
from agent_core.live import LiveMonitor
from agent_core.research_benchmark import benchmark_cases, case_snapshot, predictions, run_case, score
from agent_core.simulation import evaluate_enterprise


class ResearchTests(unittest.TestCase):
    def test_all_eight_controls_have_true_false_unknown_cases(self):
        cases = benchmark_cases()
        self.assertEqual(len(cases), 28)
        self.assertEqual(len({c['id'] for c in cases}), 28)
        for case in cases:
            with self.subTest(case=case['id']):
                result = score(case['expected'], predictions(evaluate_enterprise(case_snapshot(case))))
                self.assertTrue(result['exact_match'], result)

    def test_scorer_detects_false_positives_and_missing_evidence_errors(self):
        result = score([['A.6.3', 'HF-042', 'missing']], {('A.6.3', 'HF-042', 'finding')})
        self.assertFalse(result['exact_match'])
        self.assertEqual((result['fp'], result['fn']), (1, 1))

    def test_missing_evidence_causes_real_inspection_and_no_inferred_values(self):
        case = next(c for c in benchmark_cases() if c['id'] == 'A.6.3-unknown')
        with tempfile.TemporaryDirectory() as directory:
            events = list(agent_events('Kiểm tra', 'workflow', AgentStore(directory),
                                      snapshot=(case_snapshot(case), 'TEST', 'test')))
        self.assertEqual(events[-1]['type'], 'complete')
        inspection = next(e for e in events if e.get('tool') == 'inspect_evidence' and e['type'] == 'tool_result')
        self.assertFalse(inspection['observation']['inferred_values'])
        self.assertEqual(inspection['observation']['gaps'][0]['missing_fields'], ['training_passed'])
        self.assertGreater(events[-1]['report']['metrics']['tool_calls'], 0)
        self.assertEqual(events[-1]['report']['metrics']['model_calls'], 0)
        self.assertIn('SIM-A.6.3-HF-042', next(t for t in events[-1]['report']['tasks'] if t['task_id'] == 'HF-TASK-A.6.3')['evidence_ids'])
        for event in events:
            if event['type'] == 'action':
                self.assertIn(event['tool'], event['available_tools'])

    def test_before_after_preserves_unknown_and_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = LiveMonitor(directory, mode='workflow')
            monitor.change('HF-042', 'training_unverified')
            self.assertIsNone(monitor.state()['events'][0]['changes'][0]['after'])
            monitor.process_pending()
            self.assertIn('HF-042', next(c for c in monitor.state()['controls'] if c['control_id'] == 'A.6.3')['missing_evidence'])
            monitor.change('HF-042', 'training_complete')
            monitor.process_pending()
            state = monitor.state()
            self.assertIsNone(state['events'][0]['changes'][0]['before'])
            self.assertTrue(state['events'][0]['changes'][0]['after'])
            self.assertIn('HF-TASK-A.6.3', [t['task_id'] for t in state['report']['verified_clear_tasks']])

    def test_workflow_benchmark_uses_snapshot_and_records_success(self):
        case = next(c for c in benchmark_cases() if c['id'] == 'offboarding-open-assets')
        result = run_case(case, 'workflow')
        self.assertTrue(result['success'], result)
        self.assertTrue(result['exact_match'])
        self.assertEqual(result['model_calls'], 0)
        self.assertIn('inspect_offboarding', [a['tool'] for a in result['decisions']])

    def test_failed_model_is_counted_as_failure_and_real_call_attempt(self):
        case = next(c for c in benchmark_cases() if c['id'] == 'A.6.3-unknown')
        with patch('agent_core.autonomous.choose_with_ollama', side_effect=RuntimeError('Model unavailable')):
            result = run_case(case, 'ai')
        self.assertFalse(result['success'])
        self.assertFalse(result['exact_match'])
        self.assertEqual(result['model_calls'], 1)
