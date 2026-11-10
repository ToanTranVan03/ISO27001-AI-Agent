"""Build controlled raw configuration/log fixtures. No production host modifications."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parent/'raw'

def build():
 for profile in ('conforming','mixed','nonconforming','incomplete'):
  first=profile!='nonconforming';second=profile=='conforming'
  for number in (1,2,3,5,7,8,9,10,12,13,15,16,17,19,20,22,24,32):
   root=ROOT/profile/f'A.8.{number}';root.mkdir(parents=True,exist_ok=True)
   def put(name,value):
    (root/name).write_text(value,encoding='utf-8')
   put('capture.json',json.dumps({'observed_at':'2026-11-10T00:00:00+00:00','asset_id':f'LAB-SYSTEM-{number:02}','source_kind':'controlled-raw-config-and-log-fixture'}))
   if number==1:
    put('edr.status','Active: active (running)\n' if first else 'Active: inactive (dead)\n')
    put('lsblk.json',json.dumps({'blockdevices':[{'name':'root','type':'crypt' if second else 'part','mountpoint':'/'}]}))
   elif number==2:
    put('sudoers','labadmin ALL=(ALL:ALL) ALL\n' if first else 'ALL ALL=(ALL:ALL) NOPASSWD: ALL\n')
    put('access-review.csv','account,decision,reviewed_at\nlabadmin,'+('approved,2026-11-01' if second else 'pending,2025-01-01')+'\n')
   elif number==3:
    put('acl.csv','subject,resource,permission\n'+('finance,/finance,read' if first else 'everyone,/finance,write')+'\n')
    put('access-review.csv','account,decision,reviewed_at\nfinance,'+('approved,2026-11-01' if second else 'pending,2025-01-01')+'\n')
   elif number==5:
    put('sshd_config','AuthenticationMethods '+('publickey,keyboard-interactive' if first else 'password')+'\n')
    put('legacy-auth.conf','PasswordAuthentication '+('no' if second else 'yes')+'\nPermitRootLogin no\n')
   elif number==7:
    put('clamd.status','Active: active (running)\n' if first else 'Active: failed\n')
    put('freshclam.log','database_updated_at='+('2026-11-09T00:00:00+00:00' if second else '2025-01-01T00:00:00+00:00')+'\n')
   elif number==8:
    put('scanner.log','scan_completed_at='+('2026-11-09T00:00:00+00:00' if first else '2025-01-01T00:00:00+00:00')+'\n')
    put('vulnerabilities.csv','cve,severity,state\nLAB-CVE-001,critical,'+('fixed' if second else 'open')+'\n')
   elif number==9:
    put('baseline.conf','approval='+('CAB-001' if first else 'NONE')+'\nssh_port=22\n')
    put('drift.diff','' if second else '-PermitRootLogin no\n+PermitRootLogin yes\n')
   elif number==10:
    put('retention.conf','retention_days='+('30' if first else '3650')+'\n')
    put('deletion.log','ticket=DEL-01 action=remove verification='+('absent' if second else 'still_present')+'\n')
   elif number==12:
    put('dlp.conf','mode='+('block' if first else 'monitor')+'\n')
    put('dlp.log','probe=PII-001 decision='+('blocked' if second else 'allowed')+'\n')
   elif number==13:
    put('backup.dat','enterprise-backup-v2\n')
    digest=hashlib.sha256((root/'backup.dat').read_bytes()).hexdigest()
    put('backup.sha256',digest if first else '0'*64)
    put('restored.dat','enterprise-backup-v2\n' if second else 'corrupted-restore\n')
   elif number==15:
    put('auditd.conf','write_logs = '+('yes' if first else 'no')+'\n')
    put('audit.log','type=USER_LOGIN acct=labadmin res=success\n')
    put('audit.sha256',hashlib.sha256((root/'audit.log').read_bytes()).hexdigest() if second else '0'*64)
   elif number==16:
    put('alerts.conf','failed_login_threshold='+('5' if first else '0')+'\n')
    put('alert-delivery.log','event=FAILED_LOGIN recipient=soc delivery='+('received' if second else 'failed')+'\n')
   elif number==17:
    put('chrony.conf','server '+('time.lab.internal iburst' if first else 'untrusted.example.invalid iburst')+'\n')
    put('tracking.txt','Last offset : '+('0.001' if second else '8.5')+' seconds\n')
   elif number==19:
    put('installer-permissions.csv','subject,install_permission\n'+('admin,allow\nuser,deny' if first else 'admin,allow\nuser,allow')+'\n')
    put('packages.tsv','package\tversion\tapproval\nnginx\t1.24\t'+('CAB-010' if second else 'NONE')+'\n')
   elif number==20:
    put('nftables.conf','table inet filter { chain input { type filter hook input priority 0; policy '+('drop' if first else 'accept')+'; } }\n')
    put('firewall-review.csv','rule,ticket,decision\ninput-01,CAB-001,'+('approved' if second else 'pending')+'\n')
   elif number==22:
    put('zones.csv','zone,cidr\nprod,10.10.0.0/24\ndev,'+('10.20.0.0/24' if first else '10.10.0.0/24')+'\n')
    put('connectivity.log','source=dev target=prod:5432 result='+('DENY' if second else 'ALLOW')+'\n')
   elif number==24:
    put('nginx.conf','ssl_protocols '+('TLSv1.2 TLSv1.3' if first else 'TLSv1 TLSv1.1')+';\n')
    put('key-rotation.csv','key_id,rotated_at\nlab-key,'+('2026-11-01' if second else '2025-01-01')+'\n')
   elif number==32:
    put('changes.csv','ticket,approval\nCHG-001,'+('CAB-010' if first else 'NONE')+'\n')
    put('rollback.log','ticket=CHG-001 restore='+('verified' if second else 'failed')+'\n')
   if profile=='incomplete':
    # Deliberately remove the second criterion's raw artifact, not an expected-result flag.
    last={1:'lsblk.json',2:'access-review.csv',3:'access-review.csv',5:'legacy-auth.conf',7:'freshclam.log',8:'vulnerabilities.csv',9:'drift.diff',10:'deletion.log',12:'dlp.log',13:'restored.dat',15:'audit.sha256',16:'alert-delivery.log',17:'tracking.txt',19:'packages.tsv',20:'firewall-review.csv',22:'connectivity.log',24:'key-rotation.csv',32:'rollback.log'}[number]
    (root/last).unlink(missing_ok=True)

 # Additional stress profiles: stale capture and independently conflicting digest.
 for profile in ('stale','conflicting'):
  for source in (ROOT/'conforming').iterdir():
   dest=ROOT/profile/source.name;dest.mkdir(parents=True,exist_ok=True)
   for path in source.iterdir():shutil.copyfile(path,dest/path.name)
   meta=json.loads((dest/'capture.json').read_text(encoding='utf-8'))
   if profile=='stale':meta['observed_at']='2025-01-01T00:00:00+00:00'
   (dest/'capture.json').write_text(json.dumps(meta),encoding='utf-8')
   if profile=='conflicting':(dest/'secondary-capture.sha256').write_text('0'*64,encoding='utf-8')
 for path in ROOT.glob('*/*/capture.json'):
  meta=json.loads(path.read_text(encoding='utf-8'));meta['assessment_as_of']='2026-11-10T00:00:00+00:00'
  path.write_text(json.dumps(meta),encoding='utf-8')

if __name__=='__main__':build()
