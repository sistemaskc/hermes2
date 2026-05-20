from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    metlife_usuario: str
    metlife_password: str
    headless: bool = True
    output_dir: Path = Path("output")
    tmp_dir: Path = Path("tmp")
    heartbeat_interval: int = 240
    max_reintentos: int = 3
    max_queue_size: int = 10
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    log_dir: Path = Path("logs")
    poliza_prueba: str = ""
    telefono_prueba: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
