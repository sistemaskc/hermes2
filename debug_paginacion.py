"""
Diagnostico de paginacion en el portal MetLife.
Uso: uv run python debug_paginacion.py <POLIZA> [pestana1,pestana2,...]
Ejemplo: uv run python debug_paginacion.py HMZ317
Ejemplo: uv run python debug_paginacion.py HMZ317 coberturas,beneficiarios
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

from src.adapters.outbound.pages.login_page import LoginPage
from src.adapters.outbound.pages.policy_page import PolicyPage
from src.adapters.outbound.pages.results_page import ResultsPage
from src.adapters.outbound.pages.search_page import SearchPage
from src.config import settings
from src.domain.value_objects import Pestana, TipoIdentificador

SELECTORES_PRUEBA = [
    ".pagination",
    ".pagination li",
    ".pagination .page-item",
    ".pagination .page-item.disabled",
    ".pagination .page-item:last-child",
    ".pagination .page-item:last-child:not(.disabled)",
    ".pagination .page-item:last-child:not(.disabled) .page-link",
    ".page-link",
    '[aria-label="Next"]',
    '[aria-label="Siguiente"]',
    '[aria-label="next"]',
    'button[aria-label*="next"]',
    'a[aria-label*="next"]',
    ".pager",
    ".paginator",
    'li.next',
    'li.next:not(.disabled)',
    'li.next a',
]

TODAS_PESTANAS = [
    Pestana.GENERAL,
    Pestana.COBERTURAS,
    Pestana.BENEFICIARIOS,
    Pestana.SERVICIOS,
    Pestana.AGENTES,
]


async def main(poliza: str, pestanas: list[Pestana]):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()

        print(f"\nLogin como {settings.metlife_usuario}...")
        login = LoginPage(page, settings.metlife_usuario, settings.metlife_password)
        await login.hacer_login()
        await login.click_ingresar_consultador()
        await login.click_ingresar()

        print(f"Buscando poliza {poliza}...")
        search = SearchPage(page)
        await search.ingresar_identificador(poliza, TipoIdentificador.POLIZA)
        await search.click_buscar()
        await search.confirmar_dialogo()

        results = ResultsPage(page)
        await results.click_poliza(poliza)

        policy = PolicyPage(page)

        for pestana in pestanas:
            print(f"\n{'='*60}")
            print(f"[{pestana.value.upper()}] Navegando...")
            await policy.navegar_pestana(pestana)

            print(f"[{pestana.value.upper()}] Buscando elementos de paginacion...")
            encontrados = []
            for sel in SELECTORES_PRUEBA:
                try:
                    els = await page.query_selector_all(sel)
                    if els:
                        textos = []
                        for el in els[:3]:
                            t = (await el.inner_text()).strip().replace("\n", " ")
                            t = t.encode("ascii", errors="replace").decode("ascii")
                            cls = await el.get_attribute("class") or ""
                            textos.append(f'"{t[:30]}" class="{cls[:40]}"')
                        print(f"  ENCONTRADO: {sel:<60} -> {len(els)} elemento(s)")
                        for t in textos:
                            print(f"             {t}")
                        encontrados.append(sel)
                except Exception as e:
                    print(f"  ERROR con {sel}: {e}")

            if not encontrados:
                print(f"  Sin elementos de paginacion en [{pestana.value}]")

            # Verificar logica JS nueva
            tiene = await policy.tiene_siguiente_pagina()
            print(f"  tiene_siguiente_pagina() = {tiene}")

            # Guardar HTML del contenido
            html_file = Path(f"debug_{pestana.value}.html")
            try:
                contenido = page.locator("#root > div.container").first
                html = await contenido.inner_html()
                html_file.write_text(html, encoding="utf-8")
                print(f"  HTML guardado: {html_file}")
            except Exception as e:
                print(f"  Error guardando HTML: {e}")

            await asyncio.sleep(3)

        print("\n\nBrowser abierto. Presiona Enter para cerrar...")
        input()
        await browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: uv run python debug_paginacion.py <POLIZA> [pestana1,pestana2,...]")
        sys.exit(1)

    poliza_arg = sys.argv[1].strip().upper()

    if len(sys.argv) >= 3:
        nombres = [p.strip().lower() for p in sys.argv[2].split(",")]
        pestanas_arg = [p for p in TODAS_PESTANAS if p.value in nombres]
    else:
        pestanas_arg = TODAS_PESTANAS

    asyncio.run(main(poliza_arg, pestanas_arg))
