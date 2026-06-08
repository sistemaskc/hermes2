from src.application.session_manager import SessionManager
from src.domain.entities import Captura, ConsultaRequest, Poliza
from src.domain.exceptions import PolizaFueraMercadoError, PortalNoDisponibleError, SesionExpiradaError
from src.domain.ports import ConsultadorPort, StoragePort
from src.domain.value_objects import Pestana, TipoIdentificador, expandir_pestanas
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

        try:
            async with self._session.sesion_activa():
                return await self._procesar(request)
        except SesionExpiradaError:
            # Re-login ya completado por SessionManager. Reintentar una vez.
            logger.info("ConsultarPolizaUseCase", "Reintentando request tras re-login por sesión expirada...")
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

            try:
                numeros = await self._consultador.obtener_polizas_resultado()
            except PolizaFueraMercadoError as e:
                logger.info("ConsultarPolizaUseCase", f"Póliza fuera de mercado: {request.identificador}")
                ruta_pdf = self._storage.guardar_captura_pdf(request.identificador, e.screenshot)
                return [Poliza(numero=request.identificador, capturas=[], ruta_pdf=ruta_pdf)]
            logger.info("ConsultarPolizaUseCase", f"Pólizas encontradas: {numeros}")

            polizas: list[Poliza] = []

            for numero in numeros:
                await self._consultador.volver_a_consultador()
                await self._consultador.ir_a_busqueda()
                await self._consultador.buscar(numero, TipoIdentificador.POLIZA)
                await self._consultador.confirmar_dialogo()
                poliza = await self._procesar_poliza(numero, pestanas)
                polizas.append(poliza)

            return polizas
        finally:
            await self._consultador.volver_a_consultador()

    async def _procesar_poliza(self, numero, pestanas) -> Poliza:
        logger.info("ConsultarPolizaUseCase", f"Abriendo póliza {numero}")
        await self._consultador.abrir_poliza(numero)

        capturas: list[Captura] = []

        for pestana in pestanas:
            logger.info("ConsultarPolizaUseCase", f"Capturando pestana {pestana.value} de poliza {numero}")
            try:
                await self._consultador.navegar_pestana(pestana)
                if pestana == Pestana.COBRANZA:
                    sub_capturas = await self._consultador.capturar_cobranza()
                    for i, datos in enumerate(sub_capturas, 1):
                        ruta = self._storage.guardar_captura(numero, pestana, i, datos)
                        capturas.append(Captura(pestana=pestana, ruta_archivo=ruta))
                else:
                    datos = await self._consultador.capturar_screenshot()
                    ruta = self._storage.guardar_captura(numero, pestana, 1, datos)
                    capturas.append(Captura(pestana=pestana, ruta_archivo=ruta))
                await self._consultador.post_captura(pestana)
            except Exception as e:
                logger.error("ConsultarPolizaUseCase", f"Error capturando {pestana.value} en poliza {numero}: {e}")

        ruta_pdf = self._storage.generar_pdf(numero)
        logger.info("ConsultarPolizaUseCase", f"PDF generado: {ruta_pdf}")

        return Poliza(numero=numero, capturas=capturas, ruta_pdf=ruta_pdf)
