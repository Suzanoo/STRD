"""Check a wheel, install offline in a clean venv, test outside the repository."""
import argparse
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import venv
import zipfile

def run(args,cwd,env):
    print('+',' '.join(map(str,args)),flush=True)
    subprocess.run(list(map(str,args)),cwd=cwd,env=env,check=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('wheel',type=Path)
    parser.add_argument('--gui',action='store_true',help='Require real installed Tk widget tests')
    args=parser.parse_args();wheel=args.wheel.resolve();root=Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(wheel) as package:
        names=package.namelist()
        if len(set(names))!=len(names):raise ValueError('Duplicate entries')
        if any(not n.startswith(('strd/','strd_verified/','strd_engine-0.4.0.dist-info/')) for n in names):raise ValueError('Unexpected wheel contents')
        meta=BytesParser().parsebytes(package.read('strd_engine-0.4.0.dist-info/METADATA'))
        if meta['Name']!='strd-engine' or meta['Version']!='0.4.0' or meta.get_all('Requires-Dist'):raise ValueError('Wrong metadata/dependencies')
        expected={p.relative_to(root/'src').as_posix():p for p in (root/'src').rglob('*') if p.is_file() and (p.suffix in ('.py', '.json') or p.name=='py.typed')}
        actual={n for n in names if n.startswith(('strd/','strd_verified/'))}
        if actual!=set(expected):raise ValueError('Wheel/source inventory mismatch')
        for name,file in expected.items():
            if package.read(name)!=file.read_bytes():raise ValueError('Wheel/source content mismatch: '+name)
    print('Wheel source/content/metadata/dependency inspection PASS',flush=True)
    print('SHA256:',hashlib.sha256(wheel.read_bytes()).hexdigest(),flush=True)
    env=dict(os.environ)
    for k in ('PYTHONPATH','PYTHONHOME','PIP_TARGET','PIP_PREFIX','PIP_USER'):env.pop(k,None)
    env['PYTHONNOUSERSITE']='1'
    with tempfile.TemporaryDirectory(prefix='strd-p2-installed-') as temp:
        temp=Path(temp);venv.EnvBuilder(with_pip=True).create(temp/'env')
        python=temp/'env'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        run([python,'-I','-m','pip','--isolated','install','--no-index','--no-deps',wheel],temp,env)
        run([python,'-I','-m','pip','check'],temp,env)
        run([python,'-I',root/'scripts/run_tests.py'],temp,env)
        probe="""import importlib.util,strd,strd_verified
from pathlib import Path
from importlib.metadata import version, distribution
assert version('strd-engine')==strd.__version__=='0.4.0'
assert all('site-packages' in Path(m.__file__).parts for m in (strd,strd_verified))
assert not any(importlib.util.find_spec(p) for p in ('numpy','pandas','scipy','matplotlib','PySide6','app','applications'))
assert any(e.name=='strd-desktop' and e.value=='strd.desktop.__main__:main' and e.group=='gui_scripts' for e in distribution('strd-engine').entry_points)
import sys
assert 'tkinter' not in sys.modules
print('Installed path/dependency isolation and desktop entry point PASS')
"""
        run([python,'-I','-c',probe],temp,env)
        for mod,count in [('strd_verified',2),('strd_verified.ms2_examples',7)]:
            p=subprocess.run([str(python),'-I','-m',mod],cwd=temp,env=env,check=True,capture_output=True,text=True,encoding='utf-8')
            data=json.loads(p.stdout)
            if len(data)!=count:raise ValueError('Wrong smoke count')
            json.dumps(data,allow_nan=False);print(mod,count,'finite JSON records PASS',flush=True)
        p=subprocess.run([str(python),'-I',str(root/'verification/ms2_reference_calculations.py')],cwd=temp,env=env,check=True,capture_output=True,text=True,encoding='utf-8')
        if len(json.loads(p.stdout))!=23:raise ValueError('Wrong worksheet count')
        print('Independent worksheet: 23 quantities PASS',flush=True)
        p=subprocess.run([str(python),'-I',str(root/'verification/a2_reference_calculations.py')],cwd=temp,env=env,check=True,capture_output=True,text=True,encoding='utf-8')
        if len(json.loads(p.stdout))!=2:raise ValueError('Wrong A2 worksheet count')
        sample=json.loads((root/'examples/a2_member.json').read_text(encoding='utf-8'))
        invalid=dict(sample, axial_kn=0)
        failed=json.loads(json.dumps(sample));failed['cases'][0]['segments'][0]['moment_knm']=10000
        incomplete=json.loads(json.dumps(sample));incomplete['cases'][0]['segments'][0]['cb']=6
        for data,status,code in [(sample,'CHECKS_PASS',0),(failed,'CHECKS_FAIL',1),(invalid,'INVALID_INPUT',2),(incomplete,'INCOMPLETE',2)]:
            p=subprocess.run([str(python),'-I','-m','strd.assessment','-'],input=json.dumps(data),cwd=temp,env=env,capture_output=True,text=True,encoding='utf-8')
            result=json.loads(p.stdout)
            if p.returncode!=code or result['status']!=status:raise ValueError('Wrong A2 CLI outcome')
            json.dumps(result,allow_nan=False)
        for malformed in ('{', '{"member_id":"B1","member_id":"B2"}'):
            p=subprocess.run([str(python),'-I','-m','strd.assessment','-'],input=malformed,cwd=temp,env=env,capture_output=True,text=True,encoding='utf-8')
            if p.returncode!=2 or json.loads(p.stdout)['status']!='INVALID_INPUT':raise ValueError('Malformed JSON accepted')
        print('A2 independent worksheet: 2 sections; CLI: 6 status/exit/JSON checks PASS',flush=True)
        if args.gui:run([python,'-I',root/'scripts/run_gui_tests.py'],temp,env)
    print('Installed distribution verification PASS',flush=True)

if __name__=='__main__':main()
