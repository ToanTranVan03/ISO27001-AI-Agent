"""Lossless packing of repeated captures, with a conservative input byte budget."""
import json

# Configured Qwen byte-level tokenizer, 16K context: leave 2K tokens for
# template overhead and the bounded 512-token answer. Never cut source text.
MAX_PROMPT_BYTES=14336


class InputBudgetExceeded(ValueError):
    pass


def pack_evidence(evidence):
    packed=[];captures={}
    for item in evidence:
        try:payload=json.loads(item.get('content',''))
        except (ValueError,TypeError):payload=None
        if not isinstance(payload,dict) or payload.get('origin')!='a8-live-capture-v1':
            packed.append(dict(item));continue
        # Keep observation time, asset, artifacts, criteria and limitations in the
        # grouping key. Only import-specific provenance may vary within a group.
        content=dict(payload)
        provenance={key:content.pop(key) for key in ('assessment_id','run_id','report_sha256','collected_at') if key in content}
        key=json.dumps(content,sort_keys=True,ensure_ascii=False)
        provenance.update(evidence_id=item['evidence_id'],source=item.get('source'),sha256_hash=item.get('sha256_hash'))
        if key not in captures:
            captures[key]=dict(evidence_id=item['evidence_id'],equivalent_evidence_ids=[],content=content,provenance=[])
            packed.append(captures[key])
        captures[key]['equivalent_evidence_ids'].append(item['evidence_id'])
        captures[key]['provenance'].append(provenance)
    return packed


def validate_budget(messages):
    size=sum(len(m['content'].encode('utf-8')) for m in messages)
    if size>MAX_PROMPT_BYTES:
        raise InputBudgetExceeded('Nguồn vượt giới hạn đầu vào model; không cắt bỏ nội dung. Chia nguồn theo phạm vi/tiêu chí trước khi đánh giá.')
    return size
