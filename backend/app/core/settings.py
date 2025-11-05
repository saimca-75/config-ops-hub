from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    runtime_dir: Path = Path(__file__).parents[2] / "runtime"
    originals_dir: Path = Path(__file__).parents[2] / "scripts" / "originals"
    copies_dir: Path = runtime_dir / "copies"
    outputs_dir: Path = runtime_dir / "outputs"
    headless: bool = False
    script_timeout_seconds: int = 300

    class Config:
        env_file = ".env"

settings = Settings()
