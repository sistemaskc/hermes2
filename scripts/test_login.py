"""
Script de prueba de login. Ejecutar con:
    uv run python scripts/test_login.py

Abre el browser en modo visible para validar XPaths.
Guarda screenshot en output/debug/ en cada paso.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio

from src.adapters.outbound.playwright_consultador import PlaywrightConsultadorAdapter
from src.config import settings

OUTPUT = Path("output/debug")
OUTPUT.mkdir(parents=True, exist_ok=True)


async def main():
    if not settings.metlife_usuario or not settings.metlife_password:
        print("ERROR: METLIFE_USUARIO y METLIFE_PASSWORD requeridos en .env")
        return

    adapter = PlaywrightConsultadorAdapter(
        usuario=settings.metlife_usuario,
        password=settings.metlife_password,
        headless=False,  # visible para depuración
    )

    print("Inicializando browser...")
    await adapter.inicializar()

    try:
        print("Paso 1: Login...")
        await adapter.login()
        await adapter._page.screenshot(path=str(OUTPUT / "01_post_login.png"), full_page=True)
        print(f"  URL actual: {adapter._page.url}")
        print(f"  Screenshot: output/debug/01_post_login.png")

        print("Paso 2: Click ingresar consultador + ingresar...")
        await adapter.ir_a_busqueda()
        await adapter._page.screenshot(path=str(OUTPUT / "02_busqueda.png"), full_page=True)
        print(f"  URL actual: {adapter._page.url}")
        print(f"  Screenshot: output/debug/02_busqueda.png")

        print("\nLogin exitoso. Revisa screenshots en output/debug/")

    except Exception as e:
        await adapter._page.screenshot(path=str(OUTPUT / "error.png"), full_page=True)
        print(f"\nERROR: {e}")
        print("Screenshot guardado en output/debug/error.png")

    finally:
        await asyncio.sleep(3)
        await adapter.cerrar()


if __name__ == "__main__":
    asyncio.run(main())
