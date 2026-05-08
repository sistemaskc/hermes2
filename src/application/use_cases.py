import logging

from src.application.session_manager import SessionManager
from src.domain.entities import Captura, ConsultaRequest, Poliza
from src.domain.exceptions import PortalNoDisponibleError
from src.domain.ports import ConsultadorPort, StoragePort
from src.domain.value_objects import expandir_pestanas

logger = logging.getLogger(__name__)


class ConsultarPolizaUseCase:
    def __init__(
        self,
        session_manager: SessionManager,
        consultador: ConsultadorPort,
        storage: StoragePort,
    ):
        self._session = session_manager
        self._consultador = consultador
        self._storage = storage

    async def execute(self, request: ConsultaRequest) -> list[Poliza]:
        if self._session.lock_ocupado():
            raise PortalNoDisponibleError(
                "Consulta en proceso. Reintentar en unos segundos."
            )

        async with self._session.sesion_activa():
            return await self._procesar(request)

    async def _procesar(self, request: ConsultaRequest) -> list[Poliza]:
        pestanas = expandir_pestanas(request.pestanas)
        logger.info(
            "Procesando %s=%s pestanas=%s",
            request.tipo.value,
            request.identificador,
            [p.value for p in pestanas],
        )

        await self._consultador.ir_a_busqueda()
        await self._consultador.buscar(request.identificador, request.tipo)
        await self._consultador.confirmar_dialogo()

        numeros = await self._consultador.obtener_polizas_resultado()
        logger.info("Polizas encontradas: %s", numeros)

        polizas: list[Poliza] = []

        for i, numero in enumerate(numeros):
            poliza = await self._procesar_poliza(
                numero, request.identificador, pestanas
            )
            polizas.append(poliza)
            if i < len(numeros) - 1:
                await self._consultador.ir_a_busqueda()
                await self._consultador.buscar(request.identificador, request.tipo)
                await self._consultador.confirmar_dialogo()

        await self._consultador.volver_a_consultador()
        return polizas

    async def _procesar_poliza(self, numero, identificador, pestanas) -> Poliza:
        logger.info("Abriendo poliza %s", numero)
        await self._consultador.abrir_poliza(numero)

        capturas: list[Captura] = []

        for pestana in pestanas:
            logger.info("Capturando pestana %s de poliza %s", pestana.value, numero)
            try:
                await self._consultador.navegar_pestana(pestana)
                datos = await self._consultador.capturar_screenshot()
                ruta = self._storage.guardar_captura(
                    identificador, numero, pestana, datos
                )
                capturas.append(Captura(pestana=pestana, ruta_archivo=ruta))
            except Exception as e:
                logger.error(
                    "Error capturando %s en poliza %s: %s", pestana.value, numero, e
                )

        ruta_pdf = self._storage.generar_pdf(identificador, numero)
        logger.info("PDF generado: %s", ruta_pdf)

        return Poliza(numero=numero, capturas=capturas, ruta_pdf=ruta_pdf)
