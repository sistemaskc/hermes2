from enum import Enum


class TipoIdentificador(str, Enum):
    RFC = "RFC"
    POLIZA = "POLIZA"


class Pestana(str, Enum):
    GENERAL = "general"
    COBERTURAS = "coberturas"
    BENEFICIARIOS = "beneficiarios"
    SERVICIOS = "servicios"
    AGENTES = "agentes"
    SALDOS = "saldos"
    COBRANZA = "cobranza"
    TODO = "todo"


PESTANAS_ORDENADAS = [
    Pestana.GENERAL,
    Pestana.SALDOS,
    Pestana.COBRANZA,
    Pestana.COBERTURAS,
    Pestana.BENEFICIARIOS,
    Pestana.SERVICIOS,
    Pestana.AGENTES,
]


def expandir_pestanas(pestanas: list[Pestana]) -> list[Pestana]:
    if Pestana.TODO in pestanas:
        return PESTANAS_ORDENADAS
    return pestanas
