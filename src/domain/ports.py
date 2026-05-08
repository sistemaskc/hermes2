from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from src.domain.value_objects import Pestana, TipoIdentificador


class EstadoSesion(str, Enum):
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    PROCESSING = "PROCESSING"
    HEARTBEATING = "HEARTBEATING"
    REINITIALIZING = "REINITIALIZING"
    ERROR = "ERROR"


class ConsultadorPort(ABC):
    @abstractmethod
    async def inicializar(self) -> None: ...

    @abstractmethod
    async def cerrar(self) -> None: ...

    @abstractmethod
    async def login(self) -> None: ...

    @abstractmethod
    async def ir_a_busqueda(self) -> None: ...

    @abstractmethod
    async def buscar(self, identificador: str, tipo: TipoIdentificador) -> None: ...

    @abstractmethod
    async def confirmar_dialogo(self) -> None: ...

    @abstractmethod
    async def obtener_polizas_resultado(self) -> list[str]: ...

    @abstractmethod
    async def abrir_poliza(self, numero: str) -> None: ...

    @abstractmethod
    async def navegar_pestana(self, pestana: Pestana) -> None: ...

    @abstractmethod
    async def capturar_screenshot(self) -> bytes: ...

    @abstractmethod
    async def volver_a_consultador(self) -> None: ...

    @abstractmethod
    async def heartbeat(self) -> bool: ...

    @abstractmethod
    def estado_sesion(self) -> EstadoSesion: ...


class StoragePort(ABC):
    @abstractmethod
    def guardar_captura(
        self,
        identificador: str,
        numero_poliza: str,
        pestana: Pestana,
        datos: bytes,
    ) -> Path: ...

    @abstractmethod
    def listar_capturas(self, identificador: str, numero_poliza: str) -> list[Path]: ...

    @abstractmethod
    def generar_pdf(self, identificador: str, numero_poliza: str) -> Path: ...
