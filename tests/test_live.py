import tempfile
import unittest
from unittest.mock import patch

from agent_core.live import LiveMonitor


class LiveTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.monitor = LiveMonitor(directory.name, mode='workflow')
        self.addCleanup(self.monitor.stop)

    def test_business_change_detects_violation_and_triggers_agent(self):
        result = self.monitor.change('HF-025', 'terminate')
        self.assertTrue(result['changed'])
        state = self.monitor.state()
        issue = next(c for c in state['controls'] if c['control_id'] == 'A.6.5')
        self.assertEqual(issue['findings'][0]['person_id'], 'HF-025')
        self.assertIn('thu hồi quyền', issue['recommended_action'])
        self.assertTrue(self.monitor.process_pending())
        state = self.monitor.state()
        self.assertEqual(state['status'], 'complete')
        self.assertEqual(state['report']['trigger_revision'], 1)
        self.assertTrue(state['report']['tasks'])
        self.assertFalse(self.monitor.process_pending())

    def test_remediation_is_rechecked_and_noop_does_not_rerun(self):
        self.monitor.change('HF-025', 'terminate')
        self.monitor.process_pending()
        self.assertFalse(self.monitor.change('HF-025', 'terminate')['changed'])
        self.assertEqual(self.monitor.state()['revision'], 1)
        self.monitor.change('HF-025', 'recover_access')
        self.monitor.process_pending()
        state = self.monitor.state()
        self.assertEqual(next(c for c in state['controls'] if c['control_id'] == 'A.6.5')['status'], 'Compliant')
        self.assertTrue(all(c['status'] == 'Compliant' for c in state['controls']), 'Closed VPN of terminated staff must not cause a remote-work evidence gap')
        self.assertIn('HF-TASK-A.6.5', [t['task_id'] for t in state['report']['verified_clear_tasks']])

    def test_new_change_during_run_remains_pending(self):
        self.monitor.change('HF-001', 'training_missing')
        from agent_core.autonomous import agent_events
        def changing_agent(*args, **kwargs):
            self.monitor.change('HF-002', 'nda_missing')
            yield from agent_events(*args, **kwargs)
        with patch('agent_core.live.agent_events', side_effect=changing_agent):
            self.monitor.process_pending()
        state = self.monitor.state()
        self.assertEqual(state['revision'], 2)
        self.assertEqual(state['processed_revision'], 1)
        self.assertEqual(state['status'], 'pending')
        self.monitor.process_pending()
        self.assertEqual(self.monitor.state()['report']['trigger_revision'], 2)

    def test_failed_model_keeps_rule_findings_and_does_not_loop(self):
        self.monitor.mode = 'ai'
        self.monitor.change('HF-026', 'remote_unprotected')
        with patch('agent_core.autonomous.choose_with_ollama', side_effect=RuntimeError('Model unavailable')):
            self.monitor.process_pending()
        state = self.monitor.state()
        self.assertEqual(state['status'], 'failed')
        self.assertTrue(next(c for c in state['controls'] if c['control_id'] == 'A.6.7')['findings'])
        self.assertFalse(self.monitor.process_pending())

    def test_invalid_actions_and_persistence(self):
        with self.assertRaises(ValueError):
            self.monitor.change('unknown', 'terminate')
        with self.assertRaises(ValueError):
            self.monitor.change('HF-001', 'shell')
        self.monitor.change('HF-001', 'nda_missing')
        restored = LiveMonitor(self.monitor.store.directory, mode='workflow')
        self.assertEqual(restored.state()['revision'], 1)
        restored.process_pending()
        self.assertEqual(restored.state()['status'], 'complete')

    def test_background_worker_needs_no_audit_request(self):
        self.monitor.start()
        self.monitor.change('HF-001', 'training_missing')
        import time
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if self.monitor.state()['status'] == 'complete':
                break
            time.sleep(.02)
        self.assertEqual(self.monitor.state()['status'], 'complete')

    def test_business_actions_map_to_controls_and_repair_evidence(self):
        cases = [
            ('screening_missing', 'screening_complete', {'A.6.1'}),
            ('nda_missing', 'nda_signed', {'A.6.2', 'A.6.6'}),
            ('training_missing', 'training_complete', {'A.6.3'}),
            ('discipline_missing', 'discipline_complete', {'A.6.4'}),
            ('remote_unprotected', 'remote_protected', {'A.6.7'}),
            ('report_missing', 'report_complete', {'A.6.8'}),
            ('terminate', 'recover_access', {'A.6.5'}),
        ]
        for cause, repair, expected in cases:
            with self.subTest(action=cause):
                self.monitor.change('HF-001', cause)
                actual = {c['control_id'] for c in self.monitor.state()['controls'] if c['status'] != 'Compliant'}
                self.assertEqual(actual, expected)
                self.monitor.change('HF-001', repair)
                self.assertTrue(all(c['status'] == 'Compliant' for c in self.monitor.state()['controls']))
