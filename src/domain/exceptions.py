class SesionExpiradaError(Exception):
    pass


class PortalNoDisponibleError(Exception):
    pass


class PolizaNoEncontradaError(Exception):
    def __init__(self, identificador: str):
        super().__init__(f"No se encontraron pólizas para: {identificador}")


class CapturaFallidaError(Exception):
    def __init__(self, numero: str, pestana: str, detalle: str = ""):
        super().__init__(f"Error capturando {pestana} en póliza {numero}. {detalle}")
