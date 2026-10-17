"""Campaign-owned bounded web-only install/switch; reuses qualified current reader dependency closure; no dependency or private-state mutation."""
import hashlib,json,os,pathlib,stat,subprocess,tarfile,time,urllib.request,urllib.error
R=pathlib.Path(__file__).resolve().parent
M=json.loads((R/'MANIFEST.json').read_text())
OLD=pathlib.Path('/opt/phlogiston-app/releases/3bf402e4cf4974b5319d2f2ce0ffd76476b61b28/community/apps/community-live')
NEW=pathlib.Path('/opt/phlogiston-app/web-releases')/M['source_revision']/'community-live'
NODE=pathlib.Path('/opt/phlogiston-app/releases/3bf402e4cf4974b5319d2f2ce0ffd76476b61b28/community/toolchain/node24/bin/node')
DROP=pathlib.Path('/etc/systemd/system/community-live.service.d/20-frontdoor-generation.conf')
OTHERS=['communityd.service','communitywatch-index.service','communitywatch-web.service']
SHA=lambda b:hashlib.sha256(b).hexdigest()
CONTROL_NAMES=['p0-site-state','p0-admission-state']

def save(name,value):
    p=R/(name+'.tmp');p.write_text(json.dumps(value,indent=2)+'\n');os.chmod(p,0o600);p.replace(R/name)

def command(args):
    p=subprocess.run(args,capture_output=True,timeout=40)
    if p.returncode:raise RuntimeError('command '+args[0]+' '+args[1]+' failed exit'+str(p.returncode))
    return p.stdout

def properties(unit,fields):
    return dict(line.split('=',1) for line in command(['systemctl','show',unit,'--property='+','.join(fields)]).decode().splitlines())

def other_ids():
    out={u:properties(u,['MainPID','InvocationID','NRestarts','ActiveState']) for u in OTHERS}
    assert all(v['ActiveState']=='active' and int(v['MainPID'])>0 for v in out.values())
    return out

def config_snapshot():
    out={}
    for p in sorted(pathlib.Path('/etc/atproto-community-p0').iterdir()):
        s=p.lstat();assert not stat.S_ISLNK(s.st_mode)
        if p.is_file():out[str(p)]={'sha256':SHA(p.read_bytes()),'uid':s.st_uid,'gid':s.st_gid,'mode':oct(stat.S_IMODE(s.st_mode)),'inode':s.st_ino}
    for n in CONTROL_NAMES:
        p=pathlib.Path('/etc/atproto-community-p0')/n;s=p.lstat()
        assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022 and p.read_bytes()==b'open\n'
    return out

def service_files():
    v=properties('community-live.service',['FragmentPath','DropInPaths'])
    paths=[v['FragmentPath']]+v['DropInPaths'].split()
    return {name:SHA(pathlib.Path(name).read_bytes()) for name in paths if name!=str(DROP)}

def private_paths():
    return {str(p):{'inode':p.stat().st_ino,'uid':p.stat().st_uid,'gid':p.stat().st_gid,'mode':oct(stat.S_IMODE(p.stat().st_mode))} for p in [pathlib.Path('/var/lib/community-web-p0'),pathlib.Path('/var/lib/communityd-p0'),pathlib.Path('/var/lib/communitywatch-p0')]}

def public_checks():
    out={}
    for name,url in [('health','http://127.0.0.1:3211/healthz'),('home','https://phlogiston.app/'),('metadata','https://phlogiston.app/oauth-client-metadata.json'),('css','https://phlogiston.app/static/app.css')]:
        with urllib.request.urlopen(url,timeout=15) as r:
            body=r.read(2000000);assert r.status==200;out[name]={'status':r.status,'sha256':SHA(body)}
        if name=='health':assert body==b'ok\n'
        elif name=='metadata':
            v=json.loads(body);assert v['client_id']=='https://phlogiston.app/oauth-client-metadata.json' and v['redirect_uris']==['https://phlogiston.app/oauth/callback']
            assert v['scope']==M['oauth_scope']
        elif name=='css':assert SHA(body)==M['files']['static/app.css']
        elif name=='home':
            for marker in M['home_markers']:assert marker.encode() in body,'missing canonical UX marker'
    for path in ['/', '/?preview=qualification', '/community']:
        with urllib.request.urlopen('https://phlogiston.app'+path,timeout=15) as r:
            body=r.read(2000000);assert r.status==200
        title='The Cabinet · Phlogiston' if path=='/community' else 'Phlogiston'
        for marker in ['<title>'+title+'</title>', '<meta property="og:title" content="'+title+'">', '<meta name="twitter:title" content="'+title+'">']:
            assert marker.encode() in body,'canonical social title mismatch'
        if path!='/community':
            for attribute in ['name="description"','property="og:description"','name="twitter:description"']:
                assert ('<meta '+attribute+' content="'+M['social_description']+'">').encode() in body
        assert b'property="og:image"' not in body
        out['social:'+path]={'status':200,'sha256':SHA(body),'title':title}
    with urllib.request.urlopen('https://phlogiston.app/help',timeout=15) as r:
        body=r.read(2000000);assert r.status==200
        for marker in ['private Phlogiston view', 'direct public blocks', 'Communities are configured by the operator', 'optional public content interaction', 'Disabling disconnects this account in every browser.']:
            assert marker.encode() in body
        out['help']={'status':200,'sha256':SHA(body)}
    for path in M['static_script_paths']:
        with urllib.request.urlopen('https://phlogiston.app/'+path,timeout=15) as r:
            body=r.read(2000000);assert r.status==200 and SHA(body)==M['files'][path]
            out[path]={'status':r.status,'sha256':SHA(body)}
    for path in M['anonymous_private_paths']:
        try:
            with urllib.request.urlopen('https://phlogiston.app'+path,timeout=15) as response:
                status=response.status;body=response.read(2000000)
        except urllib.error.HTTPError as response:
            status=response.code;body=response.read(2000000)
        assert status==401,'participant private route allowed anonymous read'
        out[path]={'status':status,'sha256':SHA(body)}
    for path in M['anonymous_redirect_paths']:
        try:
            urllib.request.build_opener(NoRedirect()).open('https://phlogiston.app'+path,timeout=15)
            raise AssertionError('private document did not redirect')
        except urllib.error.HTTPError as r:
            assert r.code==303 and r.headers['Location'].startswith('/signin?return=')
            out[path]={'status':r.code,'location':r.headers['Location']}
    with urllib.request.urlopen('https://phlogiston.app/signin',timeout=15) as r:
        body=r.read(2000000);assert r.status==200 and b'<h1>Sign in to Phlogiston</h1>' in body
        assert body.count(b'class="signin"')==1
        out['signin']={'status':200,'sha256':SHA(body)}
    for detail in M['discussion_paths']:
        with urllib.request.urlopen('https://phlogiston.app'+detail,timeout=15) as r:
            body=r.read(2000000);assert r.status==200
            out[detail]={'status':r.status,'sha256':SHA(body)}
    return out

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

old_drop=None
switched=False
try:
    assert os.getuid()==0
    assert len(M['source_revision'])==40 and all(c in '0123456789abcdef' for c in M['source_revision'])
    assert not NEW.parent.exists()
    assert SHA(NODE.read_bytes())==M['node_binary_sha256']
    assert command([str(NODE),'--version']).strip()==b'v24.13.0'
    archive=R/'web-source.tar.gz';assert SHA(archive.read_bytes())==M['archive_sha256']
    assert os.statvfs('/').f_bavail*os.statvfs('/').f_frsize>64424509440+M['remote_allocation_budget_bytes']
    closure_root=pathlib.Path('/opt/phlogiston-app/web-releases/25a2816811d6fe6551fa910b853d1a130c8bfa61')
    assert SHA((closure_root/'INSTALLED.json').read_bytes())==M['baseline_closure_manifest_sha256']
    closure=json.loads((closure_root/'INSTALLED.json').read_text())
    for name in ['package.json','pnpm-lock.yaml']:
        assert M['files'][name]==closure['files'][name]
    current=pathlib.Path('/opt/phlogiston-app/web-releases')/M['baseline_web_revision']/'community-live'
    assert properties('community-live.service',['WorkingDirectory'])['WorkingDirectory']==str(current)
    for name,digest in M['baseline_files'].items():assert SHA((current/name).read_bytes())==digest
    assert DROP.is_file() and SHA(DROP.read_bytes())==M['baseline_dropin_sha256']
    dependency_root=closure_root/'community-live'/'node_modules'
    assert (current/'node_modules').is_symlink() and (current/'node_modules').resolve()==dependency_root
    assert dependency_root.is_dir() and not dependency_root.is_symlink()
    for name,entry in closure['dependencies'].items():
        p=dependency_root/name
        if entry['kind']=='symlink':
            assert p.is_symlink() and os.readlink(p)==entry['target'] and p.resolve().is_relative_to(dependency_root)
        else:
            assert p.is_file() and not p.is_symlink() and SHA(p.read_bytes())==entry['sha256']
    original_other=other_ids();original_config=config_snapshot();original_paths=private_paths();original_service_files=service_files()
    save('BEFORE.json',{'other_services':original_other,'config':original_config,'private_paths':original_paths,'service_files':original_service_files,'web':properties('community-live.service',['MainPID','InvocationID','WorkingDirectory','FragmentPath','DropInPaths','User','Group','UnitFileState'])})
    effective=command(['systemctl','cat','community-live.service']);(R/'previous-effective-unit.txt').write_bytes(effective);os.chmod(R/'previous-effective-unit.txt',0o600)
    old_drop=DROP.read_bytes() if DROP.exists() else None
    if old_drop is not None:(R/'previous-dropin.conf').write_bytes(old_drop);os.chmod(R/'previous-dropin.conf',0o600)
    save('PHASE.json',{'phase':'installing-new-public-web-generation','time':time.time()})
    NEW.parent.mkdir(parents=True,mode=0o755);NEW.mkdir(mode=0o755)
    with tarfile.open(archive,'r:gz') as t:
        for member in t.getmembers():
            assert member.isfile() and member.name in M['files'] and not pathlib.PurePosixPath(member.name).is_absolute() and '..' not in pathlib.PurePosixPath(member.name).parts
            p=NEW/member.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(t.extractfile(member).read());os.chmod(p,0o644)
    for name,digest in M['files'].items():assert SHA((NEW/name).read_bytes())==digest
    (NEW/'node_modules').symlink_to(dependency_root,target_is_directory=True)
    (NEW.parent/'INSTALLED.json').write_text(json.dumps(M,indent=2)+'\n');os.chmod(NEW.parent/'INSTALLED.json',0o644)
    drop=f'[Unit]\nConditionPathExists={NEW.parent}/INSTALLED.json\n[Service]\nWorkingDirectory={NEW}\nExecStart=\nEnvironment=COMMUNITY_READER_ENABLED=true\nExecStart={NODE} {NEW}/node_modules/tsx/dist/cli.mjs src/server.ts\n'.encode()
    DROP.parent.mkdir(exist_ok=True,mode=0o755)
    assert (DROP.read_bytes() if DROP.exists() else None)==old_drop
    temp=DROP.with_name(DROP.name+'.new');temp.write_bytes(drop);os.chmod(temp,0o644);temp.replace(DROP)
    switched=True
    save('PHASE.json',{'phase':'web-unit-switched-before-restart','dropin_sha256':SHA(drop),'time':time.time()})
    command(['systemctl','daemon-reload']);command(['systemctl','restart','community-live.service'])
    deadline=time.monotonic()+120
    for attempt in range(10):
        try:checks=public_checks();break
        except Exception:
            if attempt==9 or time.monotonic()>deadline:raise
            time.sleep(1)
    assert original_other==other_ids(),'non-web service identity changed'
    assert original_config==config_snapshot(),'config or open controls changed'
    assert original_paths==private_paths(),'private state directory replaced'
    assert original_service_files==service_files(),'base unit or other drop-in changed'
    v=properties('community-live.service',['MainPID','InvocationID','WorkingDirectory','User','Group','UnitFileState','ActiveState'])
    assert v['WorkingDirectory']==str(NEW) and v['User']=='community-web-p0' and v['ActiveState']=='active' and v['UnitFileState']=='enabled'
    save('AFTER.json',{'web':v,'other_services':other_ids(),'public_checks':checks,'config_unchanged':True,'private_directories_preserved':True,'dropin_sha256':SHA(drop),'node_modules_target':str((NEW/'node_modules').resolve())})
    save('PHASE.json',{'phase':'complete-canonical-frontdoor','time':time.time()})
    save('TERMINAL.json',{'exit':0,'source_revision':M['source_revision'],'time':time.time(),'generation':str(NEW),'other_services_unchanged':True,'controls':'unchanged open','private_state':'preserved','no_record_writes':True})
except Exception as e:
    rollback='not required before switch'
    if switched:
        try:
            assert DROP.read_bytes()==drop,'dropin changed concurrently; refuse rollback'
            if old_drop is None:DROP.unlink()
            else:
                tmp=DROP.with_name(DROP.name+'.rollback');tmp.write_bytes(old_drop);os.chmod(tmp,0o644);tmp.replace(DROP)
            command(['systemctl','daemon-reload']);command(['systemctl','restart','community-live.service']);rollback='previous exact drop-in restored and only web restarted'
        except Exception as re:rollback='indeterminate '+type(re).__name__+' '+str(re)
    save('TERMINAL.json',{'exit':1,'time':time.time(),'error_type':type(e).__name__,'error':str(e),'rollback':rollback,'recovery':'Inspect exact original producer, live drop-in and web PID/generation; never duplicate producer/reset state'})
    raise
