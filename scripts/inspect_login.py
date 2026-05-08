"""Inspecciona el HTML del formulario de login para obtener selectores correctos."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from playwright.async_api import async_playwright

URL = "https://providaweb.metlife.mx/"
OUTPUT = Path("output/debug")
OUTPUT.mkdir(parents=True, exist_ok=True)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Navegando a {URL}...")
        await page.goto(URL, wait_until="networkidle")
        await page.screenshot(path=str(OUTPUT / "login_form.png"), full_page=True)

        # Dump todos los inputs encontrados
        inputs = await page.query_selector_all("input")
        print(f"\nInputs encontrados: {len(inputs)}")
        for i, inp in enumerate(inputs):
            attrs = await page.evaluate("""el => {
                const result = {};
                for (const attr of el.attributes) {
                    result[attr.name] = attr.value;
                }
                return result;
            }""", inp)
            print(f"  input[{i}]: {attrs}")

        # Dump todos los buttons
        buttons = await page.query_selector_all("button")
        print(f"\nButtons encontrados: {len(buttons)}")
        for i, btn in enumerate(buttons):
            texto = await btn.inner_text()
            attrs = await page.evaluate("""el => {
                const result = {};
                for (const attr of el.attributes) {
                    result[attr.name] = attr.value;
                }
                return result;
            }""", btn)
            print(f"  button[{i}]: texto='{texto.strip()}' attrs={attrs}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
