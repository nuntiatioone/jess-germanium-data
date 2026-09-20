"""Measure fresh acquisition, rebuild, independent checks and output reproducibility.

Run before issuing a release. Results/timings are overwritten intentionally;
verify the delivered SHA256SUMS first or run in a copy of the release.
"""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time

import recover
import check_stream
import recommended

ROOT=recover.ROOT


def fingerprint():
    return {p.name:recover.sha256(p) for p in sorted((ROOT/'data').iterdir()) if p.is_file()}


def timed(function):
    start=time.perf_counter()
    with redirect_stdout(io.StringIO()):
        result=function()
    return time.perf_counter()-start,result


def main():
    overall=time.perf_counter()
    cache=(ROOT/'.cache').resolve(); cache.mkdir(exist_ok=True)
    scratch=Path(tempfile.mkdtemp(prefix='acquisition-check-',dir=cache)).resolve()
    # Resolve and check the exact cleanup target before any recursive deletion.
    assert scratch.is_relative_to(cache) and scratch!=cache
    try:
        (scratch/'sources').mkdir()
        shutil.copyfile(ROOT/'sources/manifest.json',scratch/'sources/manifest.json')
        recover.ROOT=scratch
        acquisition_seconds,_=timed(recover.acquire)
        receipt=recover.read_json(scratch/'results/acquisition.json')
        assert len(receipt)==5 and all(not r['cached'] for r in receipt)
    finally:
        recover.ROOT=ROOT
        assert scratch.is_relative_to(cache) and scratch!=cache
        shutil.rmtree(scratch)
    initial=fingerprint()
    cold_seconds,_=timed(lambda:recover.build(False))
    recommendation_seconds,_=timed(recommended.main)
    cold=fingerprint()
    independent_seconds,passed=timed(check_stream.check)
    assert passed
    cached_seconds,_=timed(lambda:recover.build(True))
    cached=fingerprint()
    assert cold==cached,'Cached rebuild differs from cold extraction'
    # Generation from this source version must reproduce the delivered data too.
    assert initial==cold,'Rebuild changed checked-in data; review and rerun before release'
    test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,
                        capture_output=True,text=True,check=False)
    (ROOT/'results/regression-tests.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
    if test.returncode:raise RuntimeError('Focused regression tests failed')
    patch_dir=Path(tempfile.mkdtemp(prefix='patch-check-',dir=cache)).resolve()
    assert patch_dir.is_relative_to(cache) and patch_dir!=cache
    try:
        (patch_dir/'TCE').mkdir()
        shutil.copyfile(ROOT/'.cache/germanium-upstream.md',patch_dir/'TCE/germanium.md')
        patch=ROOT/'patches/equilibriumdata-germanium.patch'
        subprocess.run(['git','apply','--check',str(patch)],cwd=patch_dir,check=True,capture_output=True)
        subprocess.run(['git','apply',str(patch)],cwd=patch_dir,check=True,capture_output=True)
        assert recover.sha256(patch_dir/'TCE/germanium.md')==recover.read_json(ROOT/'results/upstream-patch.json')['patched_sha256']
    finally:
        assert patch_dir.is_relative_to(cache) and patch_dir!=cache
        shutil.rmtree(patch_dir)
    recover.write_json(ROOT/'results/reproducibility.json',{
        'resource_version':recover.VERSION,'data_sha256':cold,
        'cold_matches_initial_data':initial==cold,'cold_matches_cached_rebuild':cold==cached,
        'independent_extraction_passed':passed,'regression_tests_passed':test.returncode==0,
        'upstream_patch_applies_and_result_hash_matches':True})
    recover.write_json(ROOT/'results/reconstruction-cost.json',{
        'checked_utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
        'python':platform.python_version(),'fresh_acquisition_seconds':acquisition_seconds,
        'fresh_acquisition_receipts':receipt,'cold_PDF_rebuild_seconds':cold_seconds,
        'recommended_conversion_and_patch_seconds':recommendation_seconds,
        'independent_parser_seconds':independent_seconds,'cached_rebuild_seconds':cached_seconds,
        'whole_reproduction_command_seconds':time.perf_counter()-overall,
        'source_bytes':sum(f['size'] for f in recover.source_manifest()['files']),
        'data_bytes':sum(p.stat().st_size for p in (ROOT/'data').iterdir() if p.is_file()),
        'local_dependency_directory_bytes':sum(p.stat().st_size for p in Path(sys.prefix).rglob('*') if p.is_file()),
        'limitations':['One execution on this machine; not a hardware-independent benchmark.',
          'Initial research, installation, review and future source-change review time are excluded.',
          'Python runtime may reside outside the local dependency directory.',
          'No human time saving or monetary value was measured.']})
    print(json.dumps(recover.read_json(ROOT/'results/reconstruction-cost.json'),indent=2))


if __name__=='__main__':main()
