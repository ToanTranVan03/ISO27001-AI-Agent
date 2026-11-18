from io import BytesIO
from docx import Document
import pytest
from evidence_collectors.source_quality import text_quality
from evidence_collectors.document_parser import extract_document_text
from backend.scope56 import build_scope
from agent_core.graph_builder import node_evaluate


@pytest.mark.parametrize('text',['','x','f'*100,'a b '+('z'*100)])
def test_unusable_text_is_not_evidence_of_compliance(text):
    assert not text_quality(text)['usable']
    d=Document();d.add_paragraph(text);out=BytesIO();d.save(out)
    with pytest.raises(ValueError):extract_document_text('source.docx',out.getvalue())


def test_ordinary_document_is_not_certified_by_text_check():
    result=text_quality('Employment agreement specifies confidentiality responsibilities and dated signatures.')
    assert result['usable'] and result['policy']=='text-usability-v1'


def test_bad_legacy_upload_is_retained_but_worklist_requests_replacement():
    evidence=dict(evidence_id='legacy',sha256_hash='hash',is_synthetic=False,source='bc.docx',
                  source_quality=text_quality('x'))
    s=build_scope('a',{'controls':[dict(control_id='A.6.2',evidence=[evidence])]})
    row=next(r for r in s['controls'] if r['control_id']=='A.6.2')
    assert row['evidence']==[evidence] and row['explicit_source_count']==1 and row['usable_source_count']==0
    assert any(t['stage']=='source_quality' and t['control_id']=='A.6.2' for t in s['acceptance_worklist']['tasks'])
    assert s['acceptance']['controls_with_source_quality_issues']==1


def test_no_usable_evidence_returns_unknown_without_model():
    result=node_evaluate(dict(source_mode='user_evidence_only',collected_evidences=[],audit_trail=[]))
    assert result['compliance_status']=='Insufficient Evidence' and result['confidence']==0
    assert result['audit_trail']==['EVALUATE NO USER EVIDENCE; NO MODEL CALL']
