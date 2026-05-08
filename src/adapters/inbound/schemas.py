import re

from pydantic import BaseModel, field_validator, model_validator

from src.domain.value_objects import Pestana, TipoIdentificador

class ConsultaRequestSchema(BaseModel):
    identificador: str
    tipo: TipoIdentificador = TipoIdentificador.POLIZA
    pestanas: list[Pestana] = [Pestana.TODO]
    numero_telefono: str

    @field_validator("numero_telefono")
    @classmethod
    def validar_numero_telefono(cls, v: str) -> str:
        digitos = re.sub(r"\D", "", v)
        if len(digitos) != 10:
            raise ValueError(f"numero_telefono debe tener 10 dígitos, se obtuvieron {len(digitos)}")
        return digitos

    @model_validator(mode="after")
    def inferir_tipo(self) -> "ConsultaRequestSchema":
        n = len(self.identificador)
        if n == 6:
            self.tipo = TipoIdentificador.POLIZA
        elif n >= 10:
            self.tipo = TipoIdentificador.RFC
        else:
            raise ValueError(
                f"identificador con longitud {n} no es válido. "
                "Debe tener 6 caracteres (póliza) o 10+ caracteres (RFC)."
            )
        return self


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
