from src.application.session_manager import SessionManager
from src.domain.entities import Captura, ConsultaRequest, Poliza
from src.domain.exceptions import PortalNoDisponibleError
from src.domain.ports import ConsultadorPort, StoragePort
from src.domain.value_objects import TipoIdentificador, expandir_pestanas
from src.infrastructure.logger import logger


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
            "ConsultarPolizaUseCase",
            f"Procesando {request.tipo.value}={request.identificador} pestanas={[p.value for p in pestanas]}",
        )

        try:
            await self._consultador.ir_a_busqueda()
            await self._consultador.buscar(request.identificador, request.tipo)
            await self._consultador.confirmar_dialogo()

            numeros = await self._consultador.obtener_polizas_resultado()
            logger.info("ConsultarPolizaUseCase", f"Pólizas encontradas: {numeros}")

            polizas: list[Poliza] = []

            for numero in numeros:
                await self._consultador.volver_a_consultador()
                await self._consultador.ir_a_busqueda()
                await self._consultador.buscar(numero, TipoIdentificador.POLIZA)
                await self._consultador.confirmar_dialogo()
                poliza = await self._procesar_poliza(
                    numero, request.identificador, pestanas, request.numero_telefono
                )
                polizas.append(poliza)

            return polizas
        finally:
            await self._consultador.volver_a_consultador()

    async def _procesar_poliza(self, numero, identificador, pestanas, numero_telefono) -> Poliza:
        logger.info("ConsultarPolizaUseCase", f"Abriendo póliza {numero}")
        await self._consultador.abrir_poliza(numero)

        capturas: list[Captura] = []

        for pestana in pestanas:
            logger.info("ConsultarPolizaUseCase", f"Capturando pestaña {pestana.value} de póliza {numero}")
            try:
                await self._consultador.navegar_pestana(pestana)
                datos = await self._consultador.capturar_screenshot()
                ruta = self._storage.guardar_captura(
                    identificador, numero, pestana, datos
                )
                capturas.append(Captura(pestana=pestana, ruta_archivo=ruta))
            except Exception as e:
                logger.error("ConsultarPolizaUseCase", f"Error capturando {pestana.value} en póliza {numero}: {e}")

        ruta_pdf = self._storage.generar_pdf(identificador, numero, numero_telefono)
        logger.info("ConsultarPolizaUseCase", f"PDF generado: {ruta_pdf}")

        return Poliza(numero=numero, capturas=capturas, ruta_pdf=ruta_pdf)
