from pathlib import Path

from pydantic import BaseModel

from src.domain.value_objects import Pestana, TipoIdentificador


class ConsultaRequestSchema(BaseModel):
    identificador: str
    tipo: TipoIdentificador = TipoIdentificador.POLIZA
    pestanas: list[Pestana] = [Pestana.TODO]


class CapturaSchema(BaseModel):
    pestana: Pestana
    ruta_archivo: str


class PolizaSchema(BaseModel):
    numero: str
    capturas: list[CapturaSchema]
    ruta_pdf: str


class ConsultaResponseSchema(BaseModel):
    polizas: list[PolizaSchema]


class ErrorSchema(BaseModel):
    detalle: str
