"""Preview owner-supplied decisions only; never infer applicability or approve."""
from backend.soa_readiness import build_readiness

FIELDS=('control_id','applicable','reason','treatment','treatment_owner','treatment_due','verification_plan')


def preview(scope,decisions):
    ids=[d['control_id'] for d in decisions]
    if len(set(ids))!=len(ids):raise ValueError('Gói có control trùng; chưa lưu quyết định nào.')
    controls={c['control_id']:c for c in scope['controls']}
    if set(ids)-controls.keys():raise ValueError('Gói chứa control ngoài phạm vi 56; chưa lưu quyết định nào.')
    supplied={d['control_id']:d for d in decisions}
    projected=[{**c,'applicability':supplied.get(c['control_id'],c.get('applicability'))} for c in scope['controls']]
    readiness=build_readiness(projected,bool(scope.get('rubric_approval')))
    gates={r['control_id']:r for r in readiness['controls']}
    changes=[]
    for d in decisions:
        c=controls[d['control_id']];old=c.get('applicability')
        before={k:old.get(k) for k in FIELDS} if old else None
        after={k:d.get(k) for k in FIELDS}
        changes.append(dict(control_id=d['control_id'],name=c['name'],before=before,after=after,
            action='unchanged' if before==after else 'update' if old else 'create',
            remaining_blockers=gates[d['control_id']]['blocker_labels']))
    return dict(changes=changes,changed_count=sum(c['action']!='unchanged' for c in changes),
        projected_ready_controls=readiness['ready_controls'],projected_pending_controls=readiness['pending_controls'],
        global_blockers=readiness['global_blockers'],
        note='Xem trước quyết định do người phụ trách cung cấp. Chưa lưu, không tạo bằng chứng/thẩm định và không phê duyệt SoA.')
