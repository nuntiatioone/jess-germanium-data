"""Seal/check a portable release and create a deterministic ZIP (standard library)."""
import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'SHA256SUMS'
FOLDERS=('data','docs','patches','results','sources','src','tests')
TOP=('.gitattributes','README.md','RIGHTS.md','LICENSE-CODE','requirements.lock.txt','requirements-demo.lock.txt')


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def paths():
    items=[ROOT/n for n in TOP]
    for folder in FOLDERS:
        items.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return sorted(items,key=lambda p:p.relative_to(ROOT).as_posix())


def seal():
    MANIFEST.write_text(''.join(f'{digest(p)}  {p.relative_to(ROOT).as_posix()}\n' for p in paths()),encoding='utf-8')


def verify():
    files=[]
    for line in MANIFEST.read_text(encoding='utf-8').splitlines():
        expected,name=line.split('  ',1)
        p=(ROOT/name).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file() or digest(p)!=expected:
            raise ValueError('Release integrity failure: '+name)
        files.append(p)
    print(f'Verified {len(files)} release files against SHA256SUMS')
    return files


def package():
    files=verify()+[MANIFEST]
    out=ROOT/'dist/jess-germanium-data-0.1.1.zip'
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(files):
            entry=zipfile.ZipInfo('jess-germanium-data-0.1.1/'+p.relative_to(ROOT).as_posix(),date_time=(2026,9,20,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            entry.external_attr=0o100644<<16
            z.writestr(entry,p.read_bytes(),compresslevel=9)
    print(f'{out.name}: {out.stat().st_size} bytes; SHA256 {digest(out)}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['seal','check','package'])
    args=parser.parse_args()
    if args.command=='seal':seal()
    elif args.command=='check':verify()
    else:package()
