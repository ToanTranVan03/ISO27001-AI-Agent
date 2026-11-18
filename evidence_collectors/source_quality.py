"""Minimal text usability, not truth, authenticity or ISO compliance."""
from collections import Counter
import json


def evidence_quality(text):
    """Judge supplied content, never allow the provenance wrapper to pad a stub."""
    try:
        payload=json.loads(text)
        if isinstance(payload,dict) and payload.get('source_kind') in {'USER_PROVIDED_PACKAGE','USER_PROVIDED_WEB_SOURCE'}:
            text=payload.get('content','')
    except (ValueError,TypeError):pass
    return text_quality(text if isinstance(text,str) else '')


def text_quality(text):
    chars=[c.casefold() for c in (text or '') if c.isalnum()]
    issues=[]
    if len(chars)<20:issues.append('too_little_extracted_text')
    elif len(set(chars))<5 or max(Counter(chars).values())/len(chars)>0.6:issues.append('repetitive_placeholder_text')
    return dict(usable=not issues,issues=issues,alphanumeric_characters=len(chars),
        policy='text-usability-v1',note='Ngưỡng kỹ thuật của dự án; không xác nhận tính đúng, đủ tiêu chí, nguồn gốc hoặc tuân thủ ISO.')
