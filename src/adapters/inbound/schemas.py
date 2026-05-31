from pydantic import BaseModel, model_validator

from src.domain.value_objects import TipoIdentificador, Pestana

class ConsultaRequestSchema(BaseModel):
    identificador: str
    tipo: TipoIdentificador = TipoIdentificador.POLIZA
    pestanas: list[Pestana] = [Pestana.TODO]
    numero_telefono: str

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
