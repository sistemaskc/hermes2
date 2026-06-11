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
    async def capturar_cobranza(self) -> list[bytes]: ...

    @abstractmethod
    async def tiene_siguiente_pagina(self) -> bool: ...

    @abstractmethod
    async def post_captura(self, pestana: Pestana) -> None: ...

    @abstractmethod
    async def navegar_siguiente_pagina(self) -> None: ...

    @abstractmethod
    async def volver_a_consultador(self) -> None: ...

    @abstractmethod
    async def heartbeat(self) -> bool: ...

    @abstractmethod
    def estado_sesion(self) -> EstadoSesion: ...


class StoragePort(ABC):
    @abstractmethod
    def guardar_captura(self, numero_poliza: str, pestana: Pestana, pagina: int, datos: bytes) -> Path: ...

    @abstractmethod
    def listar_capturas(self, numero_poliza: str) -> list[Path]: ...

    @abstractmethod
    def generar_pdf(self, numero_poliza: str) -> Path: ...

    @abstractmethod
    def limpiar_capturas(self, numero_poliza: str) -> None: ...

    @abstractmethod
    def guardar_captura_pdf(self, nombre: str, datos: bytes) -> Path: ...
