"""Inspecciona XPaths del formulario de búsqueda tras login."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

from src.adapters.outbound.playwright_consultador import PlaywrightConsultadorAdapter

OUTPUT = Path("output/debug")
OUTPUT.mkdir(parents=True, exist_ok=True)


async def main():
    adapter = PlaywrightConsultadorAdapter(
        usuario=os.getenv("METLIFE_USUARIO", ""),
        password=os.getenv("METLIFE_PASSWORD", ""),
        headless=False,
    )
    await adapter.inicializar()

    try:
        print("Login...")
        await adapter.login()
        print(f"  URL: {adapter._page.url}")

        print("Navegando a búsqueda...")
        await adapter.ir_a_busqueda()
        print(f"  URL: {adapter._page.url}")

        # Dump inputs del formulario
        inputs = await adapter._page.query_selector_all("input")
        print(f"\nInputs en formulario de búsqueda: {len(inputs)}")
        for i, inp in enumerate(inputs):
            attrs = await adapter._page.evaluate("""el => {
                const result = {};
                for (const attr of el.attributes) result[attr.name] = attr.value;
                result['_xpath'] = '';
                return result;
            }""", inp)
            placeholder = attrs.get("placeholder", "")
            name = attrs.get("name", "")
            tipo = attrs.get("type", "text")
            print(f"  [{i}] type={tipo} placeholder='{placeholder}' name='{name}'")

        # Dump botones
        buttons = await adapter._page.query_selector_all("button")
        print(f"\nButtons: {len(buttons)}")
        for i, btn in enumerate(buttons):
            texto = (await btn.inner_text()).strip()
            print(f"  [{i}] '{texto}'")

        await adapter._page.screenshot(path=str(OUTPUT / "search_form.png"), full_page=True)
        print("\nScreenshot: output/debug/search_form.png")

    finally:
        await asyncio.sleep(2)
        await adapter.cerrar()


if __name__ == "__main__":
    asyncio.run(main())
