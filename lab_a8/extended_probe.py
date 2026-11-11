"""Container-only active self-tests, not production security products.

Fixed paths and cases only. No host access, external network, arbitrary commands,
designer labels or prepared pass/fail fields. Returns operation transcripts.
"""
import base64
import csv
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone

ROOT=Path('/lab/live-extended')
PROFILES=('conforming','mixed','nonconforming','incomplete')
IDS=('A.8.1','A.8.2','A.8.5','A.8.7','A.8.8','A.8.9','A.8.12','A.8.16','A.8.17','A.8.20','A.8.22','A.8.24','A.8.32')


def sha(data):return hashlib.sha256(data).hexdigest()
def stamp():return datetime.now(timezone.utc).isoformat()
def write_json(path,data):path.write_text(json.dumps(data),encoding='utf-8')
def load(path):return json.loads(path.read_text(encoding='utf-8'))


def command(args,**kwargs):
    return subprocess.run(args,capture_output=True,timeout=8,**kwargs)


def setup():
    ROOT.mkdir(parents=True,exist_ok=True)
    cert=ROOT/'certificate.pem';key=ROOT/'private.pem'
    result=command(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(cert),
        '-days','7','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost,IP:127.0.0.1'])
    if result.returncode:raise RuntimeError('Lab certificate creation failed')
    for profile in PROFILES:
        root=ROOT/profile;root.mkdir(exist_ok=True)
        good=profile=='conforming';bad=profile=='nonconforming';missing=profile=='incomplete'
        # Actual file permissions and encrypted application data; not disk encryption.
        secret=root/'endpoint.txt';secret.write_bytes(b'lab-business-record\n');secret.chmod(0o644 if bad else 0o600)
        encryption_key=root/'encryption.key';encryption_key.write_text(secrets.token_hex(24));encryption_key.chmod(0o600)
        encrypted=command(['openssl','enc','-aes-256-cbc','-pbkdf2','-salt','-in',str(secret),'-out',str(root/'endpoint.enc'),'-pass','file:'+str(encryption_key)])
        if encrypted.returncode:raise RuntimeError('Lab encryption failed')
        (root/'endpoint-original.sha256').write_text(sha(secret.read_bytes()))
        (root/'endpoint-plaintext-copy.txt').unlink(missing_ok=True)
        if not good and not missing:shutil.copyfile(secret,root/'endpoint-plaintext-copy.txt')
        if missing:encryption_key.unlink()
        (root/'privileged.conf').write_text('restricted-admin-setting\n');(root/'privileged.conf').chmod(0o666 if bad else 0o600)
        (root/'privileged-review.csv').write_text('subject,decision,reviewed_at\nlabadmin,'+('approved' if good else 'rejected')+','+stamp()+'\n')
        # Password hash is for an isolated lab-only credential, never a user account.
        salt=secrets.token_bytes(16)
        write_json(root/'auth.json',dict(salt=salt.hex(),password_hash=hashlib.pbkdf2_hmac('sha256',b'lab-only-password',salt,100000).hex(),
            require_password=not bad,require_otp=good,otp_key=secrets.token_hex(20)))
        write_json(root/'scanner.json',dict(enabled=not bad))
        signatures=root/'signatures.txt';signatures.write_text('LAB_ONLY_HARMLESS_TEST_SIGNATURE\n')
        when=time.time()-(10*86400 if not good and not missing else 0);os.utime(signatures,(when,when))
        # Local synthetic advisory tied to the actually installed package inventory.
        inventory=command(['dpkg-query','-W','-f=${Package}\t${Version}\n']).stdout.decode()
        package,installed=inventory.splitlines()[0].split('\t')
        write_json(root/'advisories.json',[dict(advisory_id='LAB-ADVISORY-001-NOT-A-CVE',package=package,
            affected_version=installed if not good else installed+'-not-installed',severity='critical')])
        write_json(root/'scan-job.json',dict(enabled=not bad))
        config=root/'service.conf';config.write_text('protected-mode=on\n')
        write_json(root/'baseline.json',dict(ticket='UNAPPROVED' if bad else 'CAB-LAB-001',sha256=sha(config.read_bytes())))
        if not good and not missing:config.write_text('protected-mode=off\n')
        write_json(root/'dlp.json',dict(mode='allow' if bad else 'block',audit=good))
        write_json(root/'monitor.json',dict(enabled=not bad,delivery_enabled=good))
        write_json(root/'clock.json',dict(offset_ms=0 if good else 5000,signing_enabled=not bad))
        write_json(root/'network.json',dict(denied_sources=[] if bad else ['127.0.0.2'],approved_flow=good))
        write_json(root/'zones.json',dict(deny_employee_admin=not bad,business_available=good))
        shutil.copyfile(cert,root/'certificate.pem');shutil.copyfile(key,root/'private.pem')
        (root/'private.pem').chmod(0o600 if good else 0o644)
        write_json(root/'tls.json',dict(tls_enabled=not bad))
        release=root/'release.bin';release.write_bytes(b'lab-application-release-1\n')
        write_json(root/'change.json',dict(ticket='UNAPPROVED' if bad else 'CAB-LAB-032',sha256=sha(release.read_bytes())))
        (root/'rollback-backup.bin').write_bytes(release.read_bytes() if good else b'corrupt-rollback-image\n')
        if missing:
            for name in ['privileged-review.csv','auth.json','signatures.txt','advisories.json','baseline.json','dlp.json',
                         'monitor.json','clock.json','network.json','zones.json','private.pem','change.json','rollback-backup.bin']:
                (root/name).unlink(missing_ok=True)


def exchange(handler,payload=b'probe',source='127.0.0.1',server_context=None,client_context=None):
    """One real bounded loopback connection with a raw application transcript."""
    listener=socket.socket();listener.settimeout(3);listener.bind(('127.0.0.1',0));listener.listen(1)
    errors=[]
    def serve():
        try:
            peer,address=listener.accept();peer.settimeout(3)
            with peer:
                if server_context:
                    with server_context.wrap_socket(peer,server_side=True) as secure:
                        secure.sendall(handler(secure.recv(8192),address))
                else:peer.sendall(handler(peer.recv(8192),address))
        except (OSError,ssl.SSLError) as exc:errors.append(type(exc).__name__)
        finally:listener.close()
    thread=threading.Thread(target=serve,daemon=True);thread.start()
    try:
        with socket.socket() as client:
            client.settimeout(3);client.bind((source,0));client.connect(listener.getsockname())
            if client_context:
                with client_context.wrap_socket(client,server_hostname='localhost') as secure:
                    secure.sendall(payload);result=secure.recv(8192);protocol=secure.version()
            else:client.sendall(payload);result=client.recv(8192);protocol=None
        return dict(response=result.decode(),tls_version=protocol,source_address=source)
    finally:
        thread.join(timeout=4)
        if thread.is_alive():raise TimeoutError('Lab listener did not stop')


def observe(profile,cid):
    if profile not in PROFILES or cid not in IDS:raise ValueError('Invalid fixed probe')
    root=ROOT/profile
    if cid=='A.8.1':
        read=command(['su','-s','/bin/sh','labworker','-c','test -r '+str(root/'endpoint.txt')])
        key=root/'encryption.key';encrypted=root/'endpoint.enc'
        decrypted=command(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-in',str(encrypted),'-pass','file:'+str(key)]) if key.exists() else None
        return dict(read_rc=read.returncode,resource_mode=oct((root/'endpoint.txt').stat().st_mode&0o777),
            decrypt_rc=decrypted.returncode if decrypted else None,decrypted_sha256=sha(decrypted.stdout) if decrypted and decrypted.returncode==0 else None,
            original_sha256=(root/'endpoint-original.sha256').read_text(),ciphertext_prefix=base64.b64encode(encrypted.read_bytes()[:16]).decode(),
            plaintext_copy_exists=(root/'endpoint-plaintext-copy.txt').exists(),cipher='AES-256-CBC-PBKDF2 application file, not disk encryption')
    if cid=='A.8.2':
        attempt=command(['su','-s','/bin/sh','labworker','-c','test -w '+str(root/'privileged.conf')])
        return dict(privileged_write_rc=attempt.returncode,account=command(['id','labadmin']).stdout.decode(),
                    review_csv=(root/'privileged-review.csv').read_text())
    if cid=='A.8.5':
        conf=load(root/'auth.json');otp=hmac.new(bytes.fromhex(conf['otp_key']),str(int(time.time()//30)).encode(),'sha256').hexdigest()[:8]
        def login(raw,_address):
            data=json.loads(raw);candidate=hashlib.pbkdf2_hmac('sha256',data['password'].encode(),bytes.fromhex(conf['salt']),100000).hex()
            if conf['require_password'] and not hmac.compare_digest(candidate,conf['password_hash']):return b'401 invalid password'
            if conf['require_otp'] and data.get('otp')!=otp:return b'403 missing second factor'
            return b'200 authenticated'
        return dict(bad_password=exchange(login,json.dumps(dict(password='wrong',otp=otp)).encode()),
                    no_second_factor=exchange(login,json.dumps(dict(password='lab-only-password')).encode()),
                    authenticated=exchange(login,json.dumps(dict(password='lab-only-password',otp=otp)).encode()),
                    mechanism='PBKDF2 + lab time-based HMAC token, not production IAM/TOTP certification')
    if cid=='A.8.7':
        conf=load(root/'scanner.json');db=root/'signatures.txt';signature='LAB_ONLY_HARMLESS_TEST_SIGNATURE'
        database=db.read_text()
        with tempfile.TemporaryDirectory(dir=root) as folder:
            sample=Path(folder)/'sample.txt';sample.write_text('harmless sample '+signature)
            quarantine=Path(folder)/'quarantined.txt'
            matches=[s for s in database.splitlines() if s and s in sample.read_text()] if conf['enabled'] else []
            if matches:sample.replace(quarantine)
            return dict(scanner_configuration=conf,sample_sha256=sha(('harmless sample '+signature).encode()),
                scanner_exit_code=66 if matches else 0,quarantine_files=[p.name for p in Path(folder).glob('quarantined*')],
                signature_mtime=datetime.fromtimestamp(db.stat().st_mtime,timezone.utc).isoformat(),
                scanner='Lab signature scanner on harmless custom marker; not EDR/antivirus product')
    if cid=='A.8.8':
        conf=load(root/'scan-job.json');proc=command(['dpkg-query','-W','-f=${Package}\t${Version}\n'])
        return dict(scan_configuration=conf,inventory_rc=proc.returncode,inventory=proc.stdout.decode(),
                    advisory_catalog=load(root/'advisories.json'),advisory_scope='Synthetic lab advisory, not a real CVE feed')
    if cid=='A.8.9':
        baseline=load(root/'baseline.json');data=(root/'service.conf').read_bytes()
        return dict(baseline=baseline,current_configuration=data.decode(),current_sha256=sha(data),approval_source='Authored lab CAB record, not human sign-off')
    if cid=='A.8.12':
        conf=load(root/'dlp.json');events=[]
        def egress(raw,_address):
            decision='blocked' if conf['mode']=='block' and b'LAB-CONFIDENTIAL' in raw else 'allowed'
            if conf['audit']:events.append(dict(action=decision,payload_sha256=sha(raw),at=stamp()))
            return b'403 DLP blocked' if decision=='blocked' else b'200 delivered'
        result=exchange(egress,b'LAB-CONFIDENTIAL:test-business-record')
        return dict(policy=conf,transaction=result,audit_events=events)
    if cid=='A.8.16':
        conf=load(root/'monitor.json');events=[];delivered=[];stop=threading.Event()
        with tempfile.TemporaryDirectory(dir=root) as folder:
            watched=Path(folder)/'watched.txt';watched.write_text('original');initial=sha(watched.read_bytes())
            began=time.monotonic()
            def watch():
                while not stop.wait(0.01):
                    if sha(watched.read_bytes())!=initial:
                        event=dict(event='file_changed',latency_ms=round((time.monotonic()-began)*1000,2),at=stamp())
                        events.append(event)
                        if conf['delivery_enabled']:delivered.append(dict(receipt_sha256=sha(json.dumps(event).encode())))
                        return
            worker=threading.Thread(target=watch,daemon=True)
            if conf['enabled']:worker.start()
            watched.write_text('deliberate-active-probe-change')
            if conf['enabled']:worker.join(timeout=0.8)
            stop.set()
            if conf['enabled']:worker.join(timeout=1)
        return dict(monitor_configuration=conf,events=events,delivery_receipts=delivered)
    if cid=='A.8.17':
        conf=load(root/'clock.json');key=secrets.token_bytes(32);nonce=secrets.token_hex(16)
        def clock(raw,_address):
            body=json.dumps(dict(nonce=raw.decode(),time=time.time()+conf['offset_ms']/1000))
            signature=hmac.new(key,body.encode(),'sha256').hexdigest() if conf['signing_enabled'] else 'invalid'
            return json.dumps(dict(body=body,signature=signature)).encode()
        before=time.time();reply=exchange(clock,nonce.encode());after=time.time()
        response=json.loads(reply['response']);body=json.loads(response['body'])
        verified=hmac.compare_digest(response['signature'],hmac.new(key,response['body'].encode(),'sha256').hexdigest()) and body['nonce']==nonce
        return dict(reference_reply=response,signature_verify_rc=0 if verified else 1,
            offset_ms=round((body['time']-(before+after)/2)*1000,3),round_trip_ms=round((after-before)*1000,3),
            scope='Signed application time reference on same container clock; not NTP or OS synchronization')
    if cid=='A.8.20':
        conf=load(root/'network.json')
        def network(_raw,address):
            if address[0] in conf['denied_sources']:return b'403 source denied'
            if address[0]=='127.0.0.1' and not conf['approved_flow']:return b'503 approved flow unavailable'
            return b'200 service reachable'
        return dict(policy=conf,unapproved_source=exchange(network,source='127.0.0.2'),approved_source=exchange(network),
                    boundary='Application source ACL on actual loopback TCP, not kernel firewall')
    if cid=='A.8.22':
        conf=load(root/'zones.json')
        def zone(raw,address):
            if raw==b'admin' and address[0]=='127.0.0.2' and conf['deny_employee_admin']:return b'403 cross-zone denied'
            if raw==b'business' and not conf['business_available']:return b'503 business unavailable'
            return b'200 zone service reachable'
        return dict(policy=conf,employee_to_admin=exchange(zone,b'admin',source='127.0.0.2'),
            employee_to_business=exchange(zone,b'business',source='127.0.0.2'),
            boundary='Application zone gate on loopback; not VLAN, subnet or namespace isolation')
    if cid=='A.8.24':
        conf=load(root/'tls.json');key=root/'private.pem';cert=root/'certificate.pem'
        if not key.exists():raise FileNotFoundError('Missing TLS private key')
        server=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server.minimum_version=ssl.TLSVersion.TLSv1_2
        server.load_cert_chain(cert,key)
        client=ssl.create_default_context(cafile=str(cert));client.minimum_version=ssl.TLSVersion.TLSv1_2
        try:
            transcript=exchange(lambda *_:b'200 secure lab service',server_context=server if conf['tls_enabled'] else None,client_context=client)
            rc=0
        except ssl.SSLError as exc:transcript=dict(error=type(exc).__name__);rc=1
        keyread=command(['su','-s','/bin/sh','labworker','-c','test -r '+str(key)])
        return dict(handshake=transcript,handshake_rc=rc,key_read_rc=keyread.returncode,
                    key_mode=oct(key.stat().st_mode&0o777),certificate_sha256=sha(cert.read_bytes()))
    if cid=='A.8.32':
        change=load(root/'change.json');release=(root/'release.bin').read_bytes();backup=root/'rollback-backup.bin'
        with tempfile.TemporaryDirectory(dir=root) as folder:
            restored=Path(folder)/'restored-release.bin';shutil.copyfile(backup,restored)
            return dict(approval=change,current_release_sha256=sha(release),rollback_rc=0,
                        restored_sha256=sha(restored.read_bytes()),expected_release_sha256=sha(release),
                        approval_source='Authored lab change record, not human sign-off')
    raise ValueError('Unsupported probe')


def probe(profile,cid):
    try:observations=observe(profile,cid);errors=[]
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:
        # Missing-path exceptions contain the scenario folder. Keep that out of
        # the blind evidence pack and the model input.
        observations={};errors=[dict(error=type(exc).__name__,detail='Missing or invalid active source; no scenario paths exposed')]
    return dict(schema='a8-active-observation-v2',control_id=cid,observed_at=stamp(),asset_id=socket.gethostname(),
                observations=observations,collection_errors=errors,probe_kind='container-active-self-test',
                scope='Synthetic isolated lab resources, not production attestation')


if __name__=='__main__':
    if sys.argv[1:]==['setup']:setup()
    elif len(sys.argv)==4 and sys.argv[1]=='probe' and sys.argv[2] in PROFILES and sys.argv[3] in IDS:
        result=probe(sys.argv[2],sys.argv[3])
        for name,value in [('observed_at',result['observed_at']),('asset_id',result['asset_id']),('probe.json',json.dumps(result))]:
            print(name+'\t'+base64.b64encode(value.encode()).decode())
    else:raise SystemExit(64)
