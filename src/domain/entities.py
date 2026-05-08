from dataclasses import dataclass, field
from pathlib import Path

from src.domain.value_objects import Pestana, TipoIdentificador


@dataclass
class Captura:
    pestana: Pestana
    ruta_archivo: Path


@dataclass
class Poliza:
    numero: str
    capturas: list[Captura] = field(default_factory=list)
    ruta_pdf: Path | None = None


@dataclass
class ConsultaRequest:
    identificador: str
    tipo: TipoIdentificador
    pestanas: list[Pestana]
    numero_telefono: str
