"""Validate imported candidate plans without certifying source independence."""
from hashlib import sha256
from agent_core import a8_assessment as a8
from agent_core.a8_protocol import recipe,payload_fingerprint


def validate_candidate(plan):
    import json
    if len(json.dumps(plan).encode())>10*1024*1024:raise ValueError('Plan exceeds 10 MB')
    if plan.get('protocol_version')!='sealed-observations-v1':raise ValueError('Unsupported protocol')
    if plan.get('sha256')!=a8.digest({k:v for k,v in plan.items() if k!='sha256'}):raise ValueError('Plan hash mismatch')
    if plan.get('recipe')!=recipe():raise ValueError('Model/implementation changed; prepare a fresh plan')
    if plan.get('dataset_usage')!='external-candidate-pending-independent-review' or plan.get('independent_validation') is not False:
        raise ValueError('Use an external candidate plan; never self-certify independence')
    if plan.get('overlap_scan')!='cosmetic-text-v2':raise ValueError('Overlap scan changed; prepare a fresh candidate plan')
    if plan.get('known_fixture_overlap_controls'):raise ValueError('Known fixture overlap: use regression workflow instead')
    snap=plan['snapshot'];controls=a8.catalog('files')
    if not isinstance(snap,dict):raise ValueError('Snapshot must be an object')
    evidence=snap.get('evidence')
    if not isinstance(evidence,list) or any(not isinstance(e,dict) for e in evidence):
        raise ValueError('Evidence must be a list of objects')
    if snap.get('sha256')!=a8.digest({k:v for k,v in snap.items() if k!='sha256'}):raise ValueError('Snapshot hash mismatch')
    if snap.get('transport')!='files' or snap.get('catalog')!=controls:raise ValueError('Candidate rubric/source mismatch')
    if snap.get('profile') not in a8.PROFILES:raise ValueError('Unsupported profile')
    if len(snap.get('evidence',[]))!=len(controls):raise ValueError('Need all 18 controls')
    for c,e in zip(controls,snap['evidence']):
        if not isinstance(e.get('facts'),dict):raise ValueError('Facts must be an object')
        if e.get('control_id')!=c['control_id'] or set(e.get('facts',{}))!=set(c['checks']):raise ValueError('Control or facts mismatch')
        a8.rules(e)  # Reject invalid types, not unknown values.
        if e.get('source_kind')!='external-lab-candidate-unverified':raise ValueError('Candidate source marking missing')
        artifacts=e.get('artifacts',[])
        if not isinstance(artifacts,list) or any(not isinstance(a,dict) or
                any(not isinstance(a.get(key),str) for key in ('artifact','content','sha256')) for a in artifacts):
            raise ValueError('Artifacts need string name, content and sha256')
        if len({a['artifact'] for a in artifacts})!=len(artifacts):raise ValueError('Duplicate artifact names')
        if not any(a['artifact']!='capture.json' for a in artifacts):raise ValueError('Missing original source artifacts')
        for a in artifacts:
            if sha256(a['content'].encode()).hexdigest()!=a['sha256']:raise ValueError('Artifact hash mismatch')
    # Reparse source bytes with trusted collector code. A caller cannot submit
    # forged facts or append irrelevant files just to bypass fixture overlap.
    import importlib.util,re,tempfile
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('_candidate_verifier',a8.ROOT/'evidence_collectors/a8_raw.py')
    collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
    with tempfile.TemporaryDirectory(prefix='a8-candidate-check-') as directory:
        collector.ROOT=Path(directory)
        for c,e in zip(controls,snap['evidence']):
            target=collector.ROOT/snap['profile']/c['control_id'];target.mkdir(parents=True)
            for a in e['artifacts']:
                if not re.fullmatch(r'[a-z0-9_.-]+',a['artifact']) or a['artifact'] in ('.','..'):
                    raise ValueError('Invalid artifact name')
                if a['artifact'].split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:
                    raise ValueError('Reserved artifact name')
                (target/a['artifact']).write_bytes(a['content'].encode())
            parsed=collector.collect_raw(snap['profile'],c)
            if parsed['facts']!=e['facts'] or parsed['source_sha256']!=e.get('source_sha256'):
                raise ValueError('Parsed facts/source digest do not match original artifacts')
    known={payload_fingerprint(a8.collect(p,c)) for p in a8.PROFILES for c in controls}
    if any(payload_fingerprint(e) in known for e in snap['evidence']):raise ValueError('Source matches known fixture; declaration cannot override overlap')
    return plan
