from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    metlife_usuario: str
    metlife_password: str
    headless: bool = True
    output_dir: Path = Path("output")
    heartbeat_interval: int = 240
    max_reintentos: int = 3
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
