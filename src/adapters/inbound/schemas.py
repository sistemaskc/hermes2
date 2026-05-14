import re

from pydantic import BaseModel, field_validator, model_validator

from src.domain.value_objects import TipoIdentificador, Pestana

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


class FileDataSchema(BaseModel):
    file_name: str


class ConsultaResponseSchema(BaseModel):
    success: bool
    successMessage: str = ""
    errorMessage: str = ""
    data: list[FileDataSchema] = []
