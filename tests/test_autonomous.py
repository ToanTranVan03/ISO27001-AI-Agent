import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_core.autonomous import AgentStore, agent_events, build_operating_demo
from agent_core.simulation import build_enterprise


class AutonomousTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = AgentStore(Path(self.directory.name))

    def run_agent(self, mode='workflow'):
        events = list(agent_events('Kiểm tra HiveFive, ưu tiên con người', mode, self.store))
        self.assertEqual(events[-1]['type'], 'complete', events[-1])
        return events, events[-1]['report']

    def test_discovers_mixed_issues_without_scenario_selection(self):
        events, report = self.run_agent()
        self.assertEqual(report['scope']['catalog_controls'], 56)
        self.assertEqual(report['scope']['evaluated_controls'], 8)
        self.assertEqual(report['scope']['not_evaluated_controls'], 48)
        tools = [e['tool'] for e in events if e['type'] == 'tool_result']
        self.assertIn('inspect_offboarding', tools)
        self.assertIn('inspect_remote', tools)
        self.assertEqual(report['mode'], 'workflow')
        self.assertTrue(report['tasks'])
        self.assertTrue(all(t['status'] == 'proposed' for t in report['tasks']))
        self.assertEqual(self.store.latest()['run_id'], report['run_id'])

    def test_repeated_run_reuses_tasks_instead_of_duplicates(self):
        _, first = self.run_agent()
        _, second = self.run_agent()
        self.assertEqual({t['task_id'] for t in first['tasks']}, {t['task_id'] for t in second['tasks']})
        self.assertTrue(all(t['reused'] for t in second['tasks']))

    def test_recheck_uses_new_evidence_and_verifies_clear_tasks(self):
        self.run_agent()
        self.store.snapshot_path.write_text(json.dumps(build_enterprise()), encoding='utf-8')
        events, report = self.run_agent()
        self.assertEqual(report['summary']['controls_with_findings'], 0)
        self.assertEqual(len(report['verified_clear_tasks']), 8)
        self.assertNotIn('inspect_offboarding', [e.get('tool') for e in events])
        self.assertEqual(report['scope']['not_evaluated_controls'], 48)

    def test_model_selects_real_tools_and_disallowed_action_is_rejected(self):
        with patch('agent_core.autonomous.choose_with_ollama', side_effect=lambda goal, available, observations: {'tool': available[-1], 'reason': 'Kiểm tra công cụ khả dụng.'}) as planner:
            _, report = self.run_agent('ai')
        self.assertGreater(planner.call_count, 3)
        self.assertEqual(report['mode'], 'ai')
        with patch('agent_core.autonomous.choose_with_ollama', return_value={'tool': 'run_shell', 'reason': 'invalid'}):
            events = list(agent_events('Kiểm tra', 'ai', self.store))
        self.assertEqual(events[-1]['type'], 'error')
        self.assertNotIn('run_shell', [e.get('tool') for e in events if e['type'] == 'tool_result'])

    def test_model_failure_does_not_pretend_to_be_ai_success(self):
        with patch('agent_core.autonomous.choose_with_ollama', side_effect=RuntimeError('Model unavailable')):
            events = list(agent_events('Kiểm tra', 'ai', self.store))
        self.assertEqual(events[-1]['type'], 'error')
        self.assertNotIn('complete', [e['type'] for e in events])

    def test_source_fixture_is_not_modified_by_agent(self):
        snapshot = build_operating_demo()
        original = json.dumps(snapshot, ensure_ascii=False)
        self.store.snapshot_path.write_text(original, encoding='utf-8')
        self.run_agent()
        self.assertEqual(self.store.snapshot_path.read_text(encoding='utf-8'), original)

    def test_string_boolean_cannot_create_false_compliance(self):
        snapshot = build_enterprise()
        snapshot['people'][0]['nda_signed'] = 'false'
        self.store.snapshot_path.write_text(json.dumps(snapshot), encoding='utf-8')
        events = list(agent_events('Kiểm tra', 'workflow', self.store))
        self.assertEqual(events[-1]['type'], 'error')
        self.assertIsNone(self.store.latest())

    def test_storage_failure_is_reported_without_complete(self):
        with patch.object(self.store, 'save', side_effect=OSError('Unavailable')):
            events = list(agent_events('Kiểm tra', 'workflow', self.store))
        self.assertEqual(events[-1]['type'], 'error')
        self.assertNotIn('complete', [e['type'] for e in events])


if __name__ == '__main__':
    unittest.main()
