import asyncio
import logging
from contextlib import asynccontextmanager

from src.domain.ports import ConsultadorPort, EstadoSesion
from src.domain.exceptions import PortalNoDisponibleError

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(
        self,
        consultador: ConsultadorPort,
        heartbeat_interval: int = 240,
        max_reintentos: int = 3,
    ):
        self._consultador = consultador
        self._heartbeat_interval = heartbeat_interval
        self._max_reintentos = max_reintentos
        self._lock = asyncio.Lock()
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
        logger.info("SessionManager arrancado. Heartbeat cada %ds.", self._heartbeat_interval)

    async def shutdown(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        await self._consultador.cerrar()
        logger.info("SessionManager cerrado.")

    # ------------------------------------------------------------------
    # Lock (un request a la vez)
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def sesion_activa(self):
        """Context manager: adquiere lock, cambia estado a PROCESSING, libera al salir."""
        if self._estado == EstadoSesion.ERROR:
            raise PortalNoDisponibleError(
                "Sesión en estado ERROR. El servicio no puede procesar requests."
            )
        async with self._lock:
            estado_previo = self._estado
            self._estado = EstadoSesion.PROCESSING
            try:
                yield
            finally:
                self._estado = estado_previo if estado_previo != EstadoSesion.PROCESSING else EstadoSesion.ACTIVE

    @property
    def estado(self) -> EstadoSesion:
        return self._estado

    def lock_ocupado(self) -> bool:
        return self._lock.locked()

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self._heartbeat_interval)
            if self._estado == EstadoSesion.PROCESSING:
                continue
            self._estado = EstadoSesion.HEARTBEATING
            logger.debug("Heartbeat: verificando sesión...")
            try:
                activa = await self._consultador.heartbeat()
                if activa:
                    self._estado = EstadoSesion.ACTIVE
                    logger.debug("Heartbeat OK — sesión activa.")
                else:
                    logger.warning("Heartbeat: sesión expirada. Re-login...")
                    await self._re_login()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("Heartbeat error: %s", e)
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
                logger.info("Re-login intento %d/%d...", intento, self._max_reintentos)
                await self._consultador.login()
                self._estado = EstadoSesion.ACTIVE
                logger.info("Re-login exitoso en intento %d.", intento)
                return
            except Exception as e:
                logger.error("Re-login intento %d fallido: %s", intento, e)
                if intento < self._max_reintentos:
                    await asyncio.sleep(5)

        self._estado = EstadoSesion.ERROR
        logger.critical(
            "Re-login fallido tras %d intentos. Servicio degradado.", self._max_reintentos
        )
