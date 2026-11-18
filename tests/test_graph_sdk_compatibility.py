import json
from ollama._types import ChatRequest
from agent_core import graph_builder


def test_evaluation_uses_installed_sdk_json_mode_and_validates_response(monkeypatch):
    calls = []
    class Client:
        def __init__(self, **kwargs):
            assert kwargs['timeout'] == 45

        def chat(self, **kwargs):
            # Validate against the real installed SDK, rather than a permissive mock.
            ChatRequest(**kwargs)
            calls.append(kwargs)
            return {'message': {'content': json.dumps({'status': 'Compliant', 'confidence': 0.8,
                'rationale': 'Evidence inspected', 'evidence_ids': ['e1']})}}
    monkeypatch.setattr(graph_builder.ollama, 'Client', Client)
    monkeypatch.setattr(graph_builder, 'get_rubric', lambda cid: None)
    state = {'control_id': 'A.6.1', 'control_name': 'Screening', 'audit_trail': [],
             'collected_evidences': [{'evidence_id': 'e1', 'content': 'Screening completed'}]}
    result = graph_builder.node_evaluate(state)
    assert calls[0]['format'] == 'json'
    assert calls[0]['options']['num_predict']==512
    assert 'JSON schema:' in calls[0]['messages'][0]['content']
    assert result['proposed_evidence_ids'] == ['e1']


def test_truncated_json_stays_a_failed_job_and_never_saves_a_conclusion(monkeypatch):
    from backend import team_api
    from unittest.mock import MagicMock
    class Graph:
        def invoke(self,state):
            return graph_builder.ControlEvaluationOutput.model_validate_json('{')
    monkeypatch.setattr(graph_builder,'build_iso_agent_graph',lambda:Graph())
    monkeypatch.setattr(team_api.database,'get_control',lambda cid:{'control_id':cid,'name':'Test','objective':'Test criterion'})
    finish=MagicMock();monkeypatch.setattr(team_api.teamwork,'finish_job',finish)
    team_api.execute_agent_job('job','assessment','A.8.7',True)
    assert finish.call_args.args[1] is None
    assert 'JSON/schema' in finish.call_args.args[2]
