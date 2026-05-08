from playwright.async_api import Page

from src.domain.exceptions import CapturaFallidaError
from src.domain.value_objects import Pestana


class PolicyPage:
    XPATHS_PESTANAS: dict[Pestana, str] = {
        Pestana.GENERAL:       'text=INFORMACIÓN GENERAL',
        Pestana.COBERTURAS:    'text=COBERTURAS',
        Pestana.BENEFICIARIOS: 'text=BENEFICIARIOS',
        Pestana.SERVICIOS:     'text=SERVICIOS',
        Pestana.AGENTES:       'text=AGENTES',
    }

    def __init__(self, page: Page):
        self._page = page

    SELECTOR_CONTENIDO = "#root > div.container"
    SELECTOR_TABS_FIJAS = ".fixed-bottom"

    async def navegar_pestana(self, pestana: Pestana) -> None:
        xpath = self.XPATHS_PESTANAS.get(pestana)
        if not xpath:
            raise CapturaFallidaError("?", pestana.value, f"Pestana {pestana} sin xpath definido")

        try:
            await self._page.wait_for_selector(xpath, timeout=10000)
            await self._page.click(xpath)
            await self._esperar_contenido_estable()
        except Exception as e:
            raise CapturaFallidaError("?", pestana.value, str(e)) from e

    async def _esperar_contenido_estable(self) -> None:
        await self._page.wait_for_load_state("networkidle")
        await self._page.evaluate("""() => new Promise(resolve => {
            let timer = setTimeout(resolve, 500);
            const obs = new MutationObserver(() => {
                clearTimeout(timer);
                timer = setTimeout(resolve, 500);
            });
            obs.observe(document.body, { childList: true, subtree: true, attributes: true });
            setTimeout(() => { obs.disconnect(); resolve(); }, 5000);
        })""")

    async def capturar_screenshot(self) -> bytes:
        try:
            el = self._page.locator(self.SELECTOR_CONTENIDO).first
            box = await el.bounding_box()
            if not box or box["width"] < 100 or box["height"] < 100:
                return await self._page.screenshot(full_page=True)

            await self._page.evaluate(
                "sel => { const el = document.querySelector(sel); if (el) el.style.visibility = 'hidden'; }",
                self.SELECTOR_TABS_FIJAS,
            )
            try:
                return await el.screenshot()
            finally:
                await self._page.evaluate(
                    "sel => { const el = document.querySelector(sel); if (el) el.style.visibility = ''; }",
                    self.SELECTOR_TABS_FIJAS,
                )
        except Exception as e:
            raise CapturaFallidaError("?", "screenshot", str(e)) from e
