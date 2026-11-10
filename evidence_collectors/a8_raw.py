"""Read-only collectors for raw lab config, inventories, checksums and logs."""
import csv
import hashlib
import io
import ipaddress
import json
import re
import subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'lab_a8'/'raw'
PROFILES=('conforming','mixed','nonconforming','incomplete','stale','conflicting')


def collect_raw(profile,control,transport='files'):
 if profile not in PROFILES or transport not in ('files','docker'):raise ValueError('Invalid source')
 cid=control['control_id']
 if not re.fullmatch(r'A\.8\.\d+',cid):raise ValueError('Invalid control')
 artifacts=[];errors=[];cache={}
 def read(name):
  if name in cache:return cache[name]
  if not re.fullmatch(r'[a-z0-9_.-]+',name):raise ValueError('Invalid artifact')
  try:
   if transport=='files':
    path=(ROOT/profile/cid/name).resolve()
    if not path.is_relative_to((ROOT/profile/cid).resolve()):raise ValueError('Source escapes lab root')
    raw=path.read_bytes()
   else:
    proc=subprocess.run(['docker','exec','iso-a8-lab','cat',f'/lab/export/{profile}/{cid}/{name}'],capture_output=True,timeout=10)
    if proc.returncode:raise OSError('Container artifact unavailable')
    raw=proc.stdout
   if len(raw)>200000:raise ValueError('Oversize artifact')
   artifacts.append({'artifact':name,'sha256':hashlib.sha256(raw).hexdigest(),'content':raw.decode('utf-8')})
   cache[name]=raw.decode('utf-8')
   return cache[name]
  except (OSError,ValueError,subprocess.SubprocessError):
   cache[name]=None
   errors.append({'artifact':name,'error':'missing_unreadable_or_invalid'});return None
 def check(fn):
  try:return bool(fn())
  except (TypeError,ValueError,KeyError,IndexError,StopIteration,AttributeError,csv.Error):return None
 def rows(name,delimiter=','):
  text=read(name)
  if text is None:raise ValueError('Missing')
  values=list(csv.DictReader(io.StringIO(text),delimiter=delimiter))
  if not values:raise ValueError('Empty inventory is not evidence')
  return values
 def text(name):
  value=read(name)
  if value is None:raise ValueError('Missing')
  return value
 def recent(value,days):
  stamp=datetime.fromisoformat(value)
  if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=timezone.utc)
  delta=(observed-stamp).total_seconds()
  return 0<=delta<=days*86400
 try:
  meta=json.loads(text('capture.json'))
  observed=datetime.fromisoformat(meta['observed_at'])
  if observed.tzinfo is None or not isinstance(meta.get('asset_id'),str):raise ValueError('Invalid capture metadata')
 except (TypeError,ValueError,KeyError):
  errors.append({'artifact':'capture.json','error':'invalid_capture_metadata'})
  meta={};observed=datetime.now(timezone.utc)
 n=int(cid.split('.')[-1])
 if n==1:
  a=check(lambda:'active (running)' in text('edr.status'));b=check(lambda:any(x['mountpoint']=='/' and x['type']=='crypt' for x in json.loads(text('lsblk.json'))['blockdevices']))
 elif n==2:
  a=check(lambda:bool(re.fullmatch(r'labadmin ALL=\(ALL:ALL\) ALL\s*',text('sudoers'))));b=check(lambda:all(r['decision']=='approved' and recent(r['reviewed_at'],90) for r in rows('access-review.csv')))
 elif n==3:
  a=check(lambda:all(r['subject']!='everyone' and r['permission']=='read' for r in rows('acl.csv')));b=check(lambda:all(r['decision']=='approved' and recent(r['reviewed_at'],90) for r in rows('access-review.csv')))
 elif n==5:
  a=check(lambda:'AuthenticationMethods publickey,keyboard-interactive' in text('sshd_config'));b=check(lambda:'PasswordAuthentication no' in text('legacy-auth.conf'))
 elif n==7:
  a=check(lambda:'active (running)' in text('clamd.status'));b=check(lambda:recent(text('freshclam.log').strip().split('=',1)[1],2))
 elif n==8:
  a=check(lambda:recent(text('scanner.log').strip().split('=',1)[1],7));b=check(lambda:all(r['severity']!='critical' or r['state']=='fixed' for r in rows('vulnerabilities.csv')))
 elif n==9:
  a=check(lambda:bool(re.search(r'^approval=CAB-\d+',text('baseline.conf'),re.M)));b=check(lambda:text('drift.diff').strip()=='')
 elif n==10:
  a=check(lambda:1<=int(text('retention.conf').strip().split('=')[1])<=30);b=check(lambda:'verification=absent' in text('deletion.log'))
 elif n==12:
  a=check(lambda:'mode=block' in text('dlp.conf'));b=check(lambda:'decision=blocked' in text('dlp.log'))
 elif n==13:
  a=check(lambda:hashlib.sha256(text('backup.dat').encode()).hexdigest()==text('backup.sha256').strip());b=check(lambda:text('backup.dat')==text('restored.dat'))
 elif n==15:
  a=check(lambda:bool(re.search(r'^write_logs\s*=\s*yes\s*$',text('auditd.conf'),re.M)));b=check(lambda:hashlib.sha256(text('audit.log').encode()).hexdigest()==text('audit.sha256').strip())
 elif n==16:
  a=check(lambda:1<=int(text('alerts.conf').strip().split('=')[1])<=5);b=check(lambda:'delivery=received' in text('alert-delivery.log'))
 elif n==17:
  a=check(lambda:'server time.lab.internal iburst' in text('chrony.conf'));b=check(lambda:abs(float(re.search(r'Last offset : ([0-9.-]+)',text('tracking.txt')).group(1)))<=0.1)
 elif n==19:
  a=check(lambda:all(r['install_permission']=='deny' for r in rows('installer-permissions.csv') if r['subject']=='user') and any(r['subject']=='user' for r in rows('installer-permissions.csv')));b=check(lambda:all(re.fullmatch(r'CAB-\d+',r['approval']) for r in rows('packages.tsv','\t')))
 elif n==20:
  a=check(lambda:'policy drop;' in text('nftables.conf') and 'policy accept;' not in text('nftables.conf'));b=check(lambda:all(r['decision']=='approved' for r in rows('firewall-review.csv')))
 elif n==22:
  def disjoint():
   nets=[ipaddress.ip_network(r['cidr']) for r in rows('zones.csv')]
   return len(nets)>=2 and all(not a.overlaps(b) for i,a in enumerate(nets) for b in nets[i+1:])
  a=check(disjoint);b=check(lambda:'result=DENY' in text('connectivity.log'))
 elif n==24:
  a=check(lambda:set(re.search(r'ssl_protocols (.*?);',text('nginx.conf')).group(1).split())=={'TLSv1.2','TLSv1.3'});b=check(lambda:all(recent(r['rotated_at'],90) for r in rows('key-rotation.csv')))
 elif n==32:
  a=check(lambda:all(re.fullmatch(r'CAB-\d+',r['approval']) for r in rows('changes.csv')));b=check(lambda:'restore=verified' in text('rollback.log'))
 else:raise ValueError('Unsupported control')
 if not meta or errors and any(e['artifact']=='capture.json' for e in errors):a=b=None
 try:
  as_of=datetime.fromisoformat(meta.get('assessment_as_of',meta['observed_at']))
  if not 0<=(as_of-observed).total_seconds()<=7*86400:
   a=b=None;errors.append({'artifact':'capture.json','error':'capture_expired_or_future'})
 except (KeyError,TypeError,ValueError):
  a=b=None
 # Optional independently exported snapshot digest; if present it must match raw artifacts.
 secondary_path=ROOT/profile/cid/'secondary-capture.sha256'
 if transport=='files':secondary_exists=secondary_path.exists()
 else:
  try:
   probe=subprocess.run(['docker','exec','iso-a8-lab','test','-f',f'/lab/export/{profile}/{cid}/secondary-capture.sha256'],capture_output=True,timeout=10)
   secondary_exists=probe.returncode==0
  except (OSError,subprocess.SubprocessError):
   a=b=None;secondary_exists=False
   errors.append({'artifact':'secondary-capture.sha256','error':'container_read_failed'})
 if secondary_exists:
  expected=hashlib.sha256(json.dumps({r['artifact']:r['sha256'] for r in artifacts if r['artifact']!='capture.json'},sort_keys=True).encode()).hexdigest()
  secondary=read('secondary-capture.sha256')
  if secondary is None or secondary.strip()!=expected:
   a=b=None;errors.append({'artifact':'secondary-capture.sha256','error':'independent_capture_digest_conflict'})
 # Deduplicate sources when a check reads an artifact more than once.
 artifacts=list({r['artifact']:r for r in artifacts}.values())
 combined=hashlib.sha256(json.dumps(artifacts,sort_keys=True).encode()).hexdigest()
 return dict(evidence_id='A8RAW-'+combined[:24],source=f'raw-lab://{cid}',source_sha256=combined,
  collected_at=datetime.now(timezone.utc).isoformat(),observed_at=meta.get('observed_at'),
  is_synthetic=True,control_id=cid,asset_id=meta.get('asset_id'),facts=dict(zip(control['checks'],[a,b])),
  artifacts=artifacts,collection_errors=errors,transport=transport,
  source_kind='isolated-container-raw-lab' if transport=='docker' else 'raw-config-log-fixture',
  freshness_note='Replay at capture time, not assertion of current production state.')
