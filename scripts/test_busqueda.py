"""
Prueba búsqueda por RFC tras login. Ejecutar con:
    uv run python scripts/test_busqueda.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio

from src.adapters.outbound.playwright_consultador import PlaywrightConsultadorAdapter
from src.config import settings
from src.domain.value_objects import TipoIdentificador, Pestana, expandir_pestanas

OUTPUT = Path("output/debug")
OUTPUT.mkdir(parents=True, exist_ok=True)


async def main():
    if not settings.poliza_prueba:
        print("ERROR: POLIZA_PRUEBA requerida en .env")
        return

    adapter = PlaywrightConsultadorAdapter(
        usuario=settings.metlife_usuario,
        password=settings.metlife_password,
        headless=False,
    )

    print("Inicializando browser...")
    await adapter.inicializar()

    try:
        print("Paso 1: Login...")
        await adapter.login()
        print(f"  URL: {adapter._page.url}")

        print("Paso 2: Ir a búsqueda...")
        await adapter.ir_a_busqueda()
        print(f"  URL: {adapter._page.url}")

        print(f"Paso 3: Buscar póliza {settings.poliza_prueba}...")
        await adapter.buscar(settings.poliza_prueba, TipoIdentificador.POLIZA)
        await adapter._page.screenshot(path=str(OUTPUT / "03_post_buscar.png"), full_page=True)
        print(f"  URL: {adapter._page.url}")

        print("Paso 4: Confirmar diálogo...")
        await adapter.confirmar_dialogo()
        await adapter._page.screenshot(path=str(OUTPUT / "04_post_confirmar.png"), full_page=True)

        print("Paso 5: Obtener pólizas de tabla...")
        polizas = await adapter.obtener_polizas_resultado()
        print(f"  Polizas encontradas: {polizas}")
        await adapter._page.screenshot(path=str(OUTPUT / "05_resultados.png"), full_page=True)

        print(f"Paso 6: Abrir poliza {polizas[0]}...")
        await adapter.abrir_poliza(polizas[0])
        await adapter._page.screenshot(path=str(OUTPUT / "06_poliza.png"), full_page=True)
        print(f"  URL: {adapter._page.url}")

        pestanas = expandir_pestanas([Pestana.TODO])
        for pestana in pestanas:
            print(f"Paso 7: Navegar pestana {pestana.value}...")
            try:
                await adapter.navegar_pestana(pestana)
                datos = await adapter.capturar_screenshot()
                ruta = OUTPUT / f"07_{pestana.value}.png"
                ruta.write_bytes(datos)
                print(f"  Screenshot: {ruta}")
            except Exception as e:
                print(f"  ERROR en pestana {pestana.value}: {e}")
                await adapter._page.screenshot(path=str(OUTPUT / f"error_{pestana.value}.png"), full_page=True)

        print("\nFlujo completo exitoso. Revisa output/debug/")

    except Exception as e:
        await adapter._page.screenshot(path=str(OUTPUT / "error.png"), full_page=True)
        print(f"\nERROR: {e}")
        print("Screenshot: output/debug/error.png")

    finally:
        await asyncio.sleep(3)
        await adapter.cerrar()


if __name__ == "__main__":
    asyncio.run(main())
