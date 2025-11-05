# backend/app/services/runner.py
import re
import uuid
import subprocess
import sys
import json
import os
import time
from pathlib import Path

from ..core.settings import settings
from ..core.paths import ensure_runtime_dirs

ensure_runtime_dirs()

def _replace_constant(content: str, name: str, new_value_code: str) -> str:
    pattern = re.compile(r'(^\s*' + re.escape(name) + r'\s*=\s*)([\s\S]*?)(\n)', re.MULTILINE)
    m = pattern.search(content)
    if not m:
        return content
    return content[:m.start(2)] + new_value_code + content[m.end(2):]

def create_job_and_run(script_key: str, injects: dict):
    orig = settings.originals_dir / script_key
    if not orig.exists():
        raise FileNotFoundError(f"Original script not found: {orig}")
    job_id = uuid.uuid4().hex[:16]
    job_dir = settings.runtime_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    copy_path = settings.copies_dir / f"{job_id}_{orig.name}"
    content = orig.read_text(encoding='utf-8')

    # injections
    if 'GOOGLE_SHEET_URL' in injects:
        val = json.dumps(injects['GOOGLE_SHEET_URL'], ensure_ascii=False)
        content = _replace_constant(content, 'GOOGLE_SHEET_URL', val)
    if 'multimedia_data' in injects:
        val = repr(injects['multimedia_data'])
        content = _replace_constant(content, 'multimedia_data', val)
    if 'uuid_list' in injects:
        val = repr(injects['uuid_list'])
        content = _replace_constant(content, 'uuid_list', val)

    # attempt to locate webdriver_manager cache and patch the temp copy
    try:
        home = Path.home()
        wdm_root = home / ".wdm" / "drivers" / "chromedriver"
        if wdm_root.exists() and any(wdm_root.iterdir()):
            versions = [p for p in wdm_root.iterdir() if p.is_dir()]
            versions_sorted = sorted(versions, key=lambda p: p.name, reverse=True)
            found_exec = None
            for ver in versions_sorted:
                candidates = [
                    ver / "chromedriver-win32" / "chromedriver.exe",
                    ver / "chromedriver-win64" / "chromedriver.exe",
                    ver / "chromedriver" / "chromedriver.exe",
                    ver / "chromedriver.exe",
                ]
                for c in candidates:
                    if c.exists():
                        found_exec = c
                        break
                if found_exec:
                    break
            if found_exec:
                path_literal = "r" + repr(str(found_exec))
                content = content.replace("ChromeDriverManager().install()", path_literal)
                content = content.replace("ChromeDriverManager().install( )", path_literal)
    except Exception:
        pass

    # write copy
    copy_path.parent.mkdir(parents=True, exist_ok=True)
    copy_path.write_text(content, encoding='utf-8')

    # run and capture
    out_path = settings.outputs_dir / f"{job_id}.log"
    with out_path.open('w', encoding='utf-8') as fout:
        fout.write(f"--- JOB {job_id} START {time.asctime()}\n")
        fout.flush()
        try:
            proc = subprocess.run([sys.executable, str(copy_path)],
                      stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT,
                      timeout=settings.script_timeout_seconds)
            fout.write(proc.stdout.decode('utf-8', errors='replace'))
            status = 'finished'
        except subprocess.TimeoutExpired:
            fout.write('\n--- TIMEOUT (killed) ---\n')
            status = 'timeout'
        except Exception as e:
            fout.write(f"\n--- ERROR: {e} ---\n")
            status = 'error'
        fout.write(f"\n--- JOB {job_id} END {time.asctime()} status={status}\n")
    return job_id, str(out_path), status