"""Create an upload archive without credentials, dependencies or Git metadata."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'exports'
ALLOW_DIRS={'public','api','backend','scripts','tests','docs','evidence','.github'}
ALLOW_FILES={'README.md','START_HERE.md','THIRD_PARTY_NOTICES.md','requirements.txt','vercel.json','package.json','package-lock.json','.env.example','.gitignore','.vercelignore','.python-version'}
DENY_PARTS={'node_modules','__pycache__','.venv','.git','.vercel','exports'}

def included(path):
    rel=path.relative_to(ROOT)
    if set(rel.parts)&DENY_PARTS:return False
    if path.name.startswith('.env') and path.name!='.env.example':return False
    if path.suffix in {'.pyc','.zip','.log'}:return False
    return rel.parts[0] in ALLOW_DIRS or len(rel.parts)==1 and rel.name in ALLOW_FILES

def main():
    OUTPUT.mkdir(exist_ok=True)
    paths=sorted(p for p in ROOT.rglob('*') if p.is_file() and included(p))
    for p in paths:
        if not p.resolve().is_relative_to(ROOT.resolve()):raise RuntimeError('External symlink excluded')
    archive=OUTPUT/'pocket-deck-coach-assignment.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for p in paths:z.write(p,p.relative_to(ROOT).as_posix())
    with ZipFile(archive) as z:
        assert z.testzip() is None
        names=set(z.namelist())
        assert {'README.md','public/index.html','api/recommend.py','backend/catalog.json','docs/SERVICE_PLAN.md','vercel.json','.env.example'}<=names
        assert not any('.env.local' in n or 'node_modules/' in n or '__pycache__/' in n or n.startswith('.git/') for n in names)
    manifest={'archive':archive.name,'fileCount':len(paths),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':[str(p.relative_to(ROOT)).replace('\\','/') for p in paths]}
    (OUTPUT/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Upload ZIP ready: {len(paths)} files, {archive.stat().st_size:,} bytes; no environment secrets or dependencies.')
if __name__=='__main__':main()
