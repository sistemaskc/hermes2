import tomllib
from pathlib import Path

from pydantic_settings import BaseSettings


def _leer_version() -> str:
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with open(pyproject, "rb") as f:
        return tomllib.load(f)["project"]["version"]


VERSION = _leer_version()


class Settings(BaseSettings):
    metlife_usuario: str
    metlife_password: str
    headless: bool = True
    output_dir: Path = Path("output")
    tmp_dir: Path = Path("tmp")
    heartbeat_interval: int = 240
    max_reintentos: int = 3
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    log_dir: Path = Path("logs")
    poliza_prueba: str = ""
    telefono_prueba: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
