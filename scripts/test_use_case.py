"""
Prueba ConsultarPolizaUseCase completo.
    uv run python scripts/test_use_case.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from src.adapters.outbound.playwright_consultador import PlaywrightConsultadorAdapter
from src.adapters.outbound.local_storage import LocalStorageAdapter
from src.application.session_manager import SessionManager
from src.application.use_cases import ConsultarPolizaUseCase
from src.config import settings
from src.domain.entities import ConsultaRequest
from src.domain.value_objects import TipoIdentificador, Pestana


async def main():
    if not settings.poliza_prueba:
        print("ERROR: POLIZA_PRUEBA requerida en .env")
        return
    if not settings.telefono_prueba:
        print("ERROR: TELEFONO_PRUEBA requerida en .env")
        return

    adapter = PlaywrightConsultadorAdapter(
        usuario=settings.metlife_usuario,
        password=settings.metlife_password,
        headless=False,
    )
    storage = LocalStorageAdapter(output_dir=settings.output_dir)
    manager = SessionManager(
        consultador=adapter,
        heartbeat_interval=settings.heartbeat_interval,
        max_reintentos=settings.max_reintentos,
    )
    use_case = ConsultarPolizaUseCase(
        session_manager=manager,
        consultador=adapter,
        storage=storage,
    )

    print("Startup...")
    await manager.startup()

    try:
        request = ConsultaRequest(
            identificador=settings.poliza_prueba,
            tipo=TipoIdentificador.POLIZA,
            pestanas=[Pestana.TODO],
            numero_telefono=settings.telefono_prueba,
        )

        print(f"Ejecutando consulta: {poliza} - todas las pestanas...")
        resultado = await use_case.execute(request)

        print(f"\nResultado: {len(resultado)} poliza(s)")
        for p in resultado:
            print(f"  Poliza: {p.numero}")
            print(f"  PDF: {p.ruta_pdf}")
            for c in p.capturas:
                print(f"    {c.pestana.value}: {c.ruta_archivo}")

    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
