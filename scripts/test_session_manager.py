"""
Prueba SessionManager: startup, heartbeat, lock y shutdown.
    uv run python scripts/test_session_manager.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from src.adapters.outbound.playwright_consultador import PlaywrightConsultadorAdapter
from src.application.session_manager import SessionManager
from src.config import settings
from src.domain.ports import EstadoSesion


async def main():
    adapter = PlaywrightConsultadorAdapter(
        usuario=settings.metlife_usuario,
        password=settings.metlife_password,
        headless=False,
    )
    manager = SessionManager(
        consultador=adapter,
        heartbeat_interval=30,  # 30s para probar heartbeat rápido
        max_reintentos=3,
    )

    print("Paso 1: startup (login + heartbeat task)...")
    await manager.startup()
    print(f"  Estado: {manager.estado().value}")
    assert manager.estado() == EstadoSesion.ACTIVE, "Esperaba ACTIVE tras startup"

    print("Paso 2: adquirir lock (simular request)...")
    async with manager.sesion_activa():
        print(f"  Estado durante lock: {manager.estado().value}")
        assert manager.estado() == EstadoSesion.PROCESSING
        assert manager.lock_ocupado()
        await asyncio.sleep(2)

    print(f"  Estado tras lock: {manager.estado().value}")
    assert manager.estado() == EstadoSesion.ACTIVE

    print("Paso 3: verificar que segundo intento de lock espera (no falla)...")
    async def request_simulado(n: int):
        async with manager.sesion_activa():
            print(f"  Request {n} ejecutando...")
            await asyncio.sleep(1)
            print(f"  Request {n} finalizado.")

    await asyncio.gather(request_simulado(1), request_simulado(2))
    print(f"  Ambos requests completados en serie. Estado: {manager.estado().value}")

    print("Paso 4: esperar heartbeat (30s)...")
    await asyncio.sleep(35)
    print(f"  Estado post-heartbeat: {manager.estado().value}")
    assert manager.estado() == EstadoSesion.ACTIVE, f"Esperaba ACTIVE, got {manager.estado().value}"

    print("Paso 5: shutdown...")
    await manager.shutdown()
    print("  Shutdown OK")

    print("\nSessionManager OK - todas las pruebas pasaron")


if __name__ == "__main__":
    asyncio.run(main())
