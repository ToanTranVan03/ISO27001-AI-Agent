import unittest
import json
import tempfile
from unittest.mock import patch
from urllib.error import URLError

from fastapi.testclient import TestClient

from backend.main import app
from agent_core.simulation import ModelUnavailable, explain_with_ollama, run_simulation
from agent_core.autonomous import AgentStore, agent_events
from agent_core.live import LiveMonitor


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_business_event_automatically_produces_rule_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = LiveMonitor(directory, mode='workflow')
            with patch('backend.main.get_live_monitor', return_value=monitor):
                initial = self.client.get('/api/live').json()
                self.assertEqual(initial['revision'], 0)
                self.assertTrue(all(c['status'] == 'Compliant' for c in initial['controls']))
                response = self.client.post('/api/live/events', json={'person_id': 'HF-025', 'action': 'terminate'})
                self.assertEqual(response.status_code, 200)
                state = self.client.get('/api/live').json()
                self.assertTrue(next(c for c in state['controls'] if c['control_id'] == 'A.6.5')['findings'])
                self.assertEqual(self.client.post('/api/live/events', json={'person_id': 'HF-025', 'action': 'invalid'}).status_code, 400)
                self.assertEqual(self.client.post('/api/live/events', json={}).status_code, 422)

    def test_agent_stream_history_and_input_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AgentStore(directory)
            with patch('backend.main.agent_events', side_effect=lambda goal, mode: agent_events(goal, mode, store)), patch('backend.main.AgentStore', return_value=store):
                response = self.client.post('/api/agent/run', json={'goal': 'Kiểm tra HiveFive', 'mode': 'workflow'})
                self.assertIn('application/x-ndjson', response.headers['content-type'])
                events = [json.loads(line) for line in response.text.splitlines()]
                self.assertEqual(events[0]['type'], 'start')
                self.assertEqual(events[-1]['type'], 'complete')
                self.assertEqual(self.client.get('/api/agent/latest').json()['run_id'], events[-1]['report']['run_id'])
                self.assertEqual(len(self.client.get('/api/agent/history').json()), 1)
        for body in ({'goal': ''}, {'goal': '   '}, {'goal': 'x' * 1001}, {'goal': 'test', 'mode': 'invalid'}):
            self.assertEqual(self.client.post('/api/agent/run', json=body).status_code, 422)

    def test_live_report_exports_consistent_snapshot_and_evidence_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = LiveMonitor(directory, mode='workflow')
            monitor.change('HF-042', 'training_unverified')
            with patch('backend.main.get_live_monitor', return_value=monitor):
                response = self.client.get('/api/live/report')
            self.assertEqual(response.status_code, 200)
            self.assertIn('attachment;', response.headers['content-disposition'])
            report = response.json()
            self.assertEqual(report['revision'], 1)
            self.assertEqual(report['enterprise']['name'], 'HiveFive')
            self.assertIsNone(report['events'][0]['changes'][0]['after'])
            self.assertEqual(len(report['snapshot_hash']), 64)

    def test_catalog_and_page(self):
        response = self.client.get('/api/simulation')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['enterprise']['name'], 'HiveFive')
        self.assertEqual(len(response.json()['scenarios']), 6)
        self.assertIn('HiveFive', self.client.get('/simulation').text)
        for path in ('/static/app.js', '/static/style.css', '/static/guided.css'):
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertIn('javascript', self.client.get('/static/navigation.mjs').headers['content-type'])

    def test_all_scenarios_and_invalid_input(self):
        scenarios = self.client.get('/api/simulation').json()['scenarios']
        for scenario in scenarios:
            with self.subTest(scenario=scenario['id']):
                response = self.client.post('/api/simulation/run', json={'scenario_id': scenario['id']})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['mode'], 'rules')
        self.assertEqual(self.client.post('/api/simulation/run', json={'scenario_id': 'invalid'}).status_code, 404)
        self.assertEqual(self.client.post('/api/simulation/run', json={'scenario_id': 'baseline', 'mode': 'invalid'}).status_code, 422)
        self.assertEqual(self.client.post('/api/simulation/run', json={}).status_code, 422)

    def test_ollama_connection_failure_is_recoverable(self):
        with patch('agent_core.simulation.urlopen', side_effect=URLError('unavailable')):
            response = self.client.post('/api/simulation/run', json={'scenario_id': 'training', 'mode': 'ai'})
        self.assertEqual(response.status_code, 503)
        self.assertIn('Quy tắc', response.json()['detail'])
        self.assertEqual(self.client.post('/api/simulation/run', json={'scenario_id': 'training'}).status_code, 200)

    def test_ai_commentary_does_not_replace_rule_decisions(self):
        with patch('agent_core.simulation.explain_with_ollama', return_value='Giải thích diễn tập'):
            result = run_simulation('training', 'ai')
        self.assertEqual(result['mode'], 'ai')
        self.assertEqual(result['ai_explanation'], 'Giải thích diễn tập')
        self.assertEqual(next(c for c in result['controls'] if c['control_id'] == 'A.6.3')['status'], 'Partially Compliant')

    def test_malformed_model_response(self):
        with patch('agent_core.simulation.urlopen') as call:
            call.return_value.__enter__.return_value.read.return_value = b'{"message": {"content": ""}}'
            with self.assertRaises(ModelUnavailable):
                explain_with_ollama([])

    def test_legacy_root_still_returns_message(self):
        self.assertIn('message', self.client.get('/').json())

    def test_legacy_evaluation_contract(self):
        with patch('backend.main.agent_graph') as graph:
            graph.invoke.return_value = {'control_id': 'A.6.3', 'compliance_status': 'Partially Compliant',
                                        'confidence': .85, 'rationale': 'Test', 'audit_trail': ['PLAN', 'REPORT']}
            response = self.client.post('/api/evaluate', json={'control_id': 'A.6.3'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {'control_id', 'status', 'confidence', 'rationale', 'audit_trail'})
        self.assertEqual(self.client.post('/api/evaluate', json={'control_id': 'unknown'}).status_code, 404)


if __name__ == '__main__':
    unittest.main()
