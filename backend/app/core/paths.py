from pathlib import Path
from .settings import settings

def ensure_runtime_dirs():
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    settings.copies_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
