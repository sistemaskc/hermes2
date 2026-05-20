import asyncio
from contextlib import asynccontextmanager

from src.domain.exceptions import ColaSaturadaError, PortalNoDisponibleError, SesionExpiradaError
from src.domain.ports import ConsultadorPort, EstadoSesion
from src.infrastructure.logger import logger


class SessionManager:
    def __init__(
        self,
        consultador: ConsultadorPort,
        heartbeat_interval: int = 240,
        max_reintentos: int = 3,
        max_queue_size: int = 10,
    ):
        self._consultador = consultador
        self._heartbeat_interval = heartbeat_interval
        self._max_reintentos = max_reintentos
        self._max_queue_size = max_queue_size
        self._lock = asyncio.Lock()
        self._pending = 0
        self._heartbeat_task: asyncio.Task | None = None
        self._estado = EstadoSesion.INITIALIZING

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def startup(self) -> None:
        self._estado = EstadoSesion.INITIALIZING
        await self._consultador.inicializar()
        await self._login_con_reintentos()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("SessionManager", f"Arrancado. Heartbeat cada {self._heartbeat_interval}s.")

    async def shutdown(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        await self._consultador.cerrar()
        logger.info("SessionManager", "Cerrado.")

    # ------------------------------------------------------------------
    # Lock (un request a la vez)
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def sesion_activa(self):
        """Context manager: encola request FIFO, adquiere lock, libera al salir."""
        if self._estado == EstadoSesion.ERROR:
            raise PortalNoDisponibleError(
                "Sesión en estado ERROR. El servicio no puede procesar requests."
            )
        if self._pending >= self._max_queue_size:
            raise ColaSaturadaError(self._max_queue_size)
        self._pending += 1
        try:
            async with self._lock:
                self._estado = EstadoSesion.PROCESSING
                try:
                    yield
                except SesionExpiradaError:
                    logger.warning("SessionManager", "SesionExpiradaError durante procesamiento. Re-login inmediato...")
                    await self._re_login()
                    raise
                finally:
                    self._estado = self._estado if self._estado not in (EstadoSesion.PROCESSING,) else EstadoSesion.ACTIVE
        finally:
            self._pending -= 1

    @property
    def estado(self) -> EstadoSesion:
        return self._estado

    @property
    def pending(self) -> int:
        return self._pending

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self._heartbeat_interval)
            if self._estado == EstadoSesion.PROCESSING:
                continue
            self._estado = EstadoSesion.HEARTBEATING
            logger.debug("SessionManager", "Heartbeat: verificando sesión...")
            try:
                activa = await self._consultador.heartbeat()
                if activa:
                    self._estado = EstadoSesion.ACTIVE
                    logger.debug("SessionManager", "Heartbeat OK — sesión activa.")
                else:
                    logger.warning("SessionManager", "Heartbeat: sesión expirada. Re-login...")
                    await self._re_login()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("SessionManager", f"Heartbeat error: {e}")
                await self._re_login()

    # ------------------------------------------------------------------
    # Re-login
    # ------------------------------------------------------------------

    async def _login_con_reintentos(self) -> None:
        await self._re_login()

    async def _re_login(self) -> None:
        self._estado = EstadoSesion.REINITIALIZING
        for intento in range(1, self._max_reintentos + 1):
            try:
                logger.info("SessionManager", f"Re-login intento {intento}/{self._max_reintentos}...")
                await self._consultador.login()
                self._estado = EstadoSesion.ACTIVE
                logger.info("SessionManager", f"Re-login exitoso en intento {intento}.")
                return
            except Exception as e:
                logger.error("SessionManager", f"Re-login intento {intento} fallido: {e}")
                if intento < self._max_reintentos:
                    await asyncio.sleep(5)

        self._estado = EstadoSesion.ERROR
        logger.error("SessionManager", f"Re-login fallido tras {self._max_reintentos} intentos. Servicio degradado.")
