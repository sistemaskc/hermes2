"""
Prueba ConsultarPolizaUseCase completo.
    uv run python scripts/test_use_case.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging
from dotenv import load_dotenv
import os

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from src.adapters.outbound.playwright_consultador import PlaywrightConsultadorAdapter
from src.adapters.outbound.local_storage import LocalStorageAdapter
from src.application.session_manager import SessionManager
from src.application.use_cases import ConsultarPolizaUseCase
from src.domain.entities import ConsultaRequest
from src.domain.value_objects import TipoIdentificador, Pestana


async def main():
    poliza = os.getenv("POLIZA_PRUEBA", "")
    if not poliza:
        print("ERROR: POLIZA_PRUEBA requerida en .env")
        return

    adapter = PlaywrightConsultadorAdapter(
        usuario=os.getenv("METLIFE_USUARIO", ""),
        password=os.getenv("METLIFE_PASSWORD", ""),
        headless=False,
    )
    storage = LocalStorageAdapter(output_dir=Path("output"))
    manager = SessionManager(consultador=adapter, heartbeat_interval=240, max_reintentos=3)
    use_case = ConsultarPolizaUseCase(
        session_manager=manager,
        consultador=adapter,
        storage=storage,
    )

    print("Startup...")
    await manager.startup()

    try:
        request = ConsultaRequest(
            identificador=poliza,
            tipo=TipoIdentificador.POLIZA,
            pestanas=[Pestana.TODO],
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
