from playwright.async_api import Page

from src.domain.exceptions import PolizaFueraMercadoError, PolizaNoEncontradaError


class ResultsPage:
    XPATH_FILAS_TABLA = '//*[@id="root"]/div[3]/div/div[2]/div[2]/table/tbody/tr'

    def __init__(self, page: Page):
        self._page = page

    async def obtener_numeros_poliza(self) -> list[str]:
        try:
            await self._page.wait_for_selector(self.XPATH_FILAS_TABLA, timeout=15000)
        except Exception:
            try:
                el = self._page.locator("#root > div.container").first
                box = await el.bounding_box()
                if box and box["width"] >= 100 and box["height"] >= 100:
                    screenshot = await el.screenshot()
                else:
                    screenshot = await self._page.screenshot(full_page=True)
            except Exception:
                screenshot = await self._page.screenshot(full_page=True)
            raise PolizaFueraMercadoError(screenshot)

        filas = await self._page.query_selector_all(self.XPATH_FILAS_TABLA)
        if not filas:
            raise PolizaNoEncontradaError("Sin resultados en tabla")

        numeros = []
        for fila in filas:
            link = await fila.query_selector("td:nth-child(1) a")
            if link:
                texto = await link.inner_text()
                if texto.strip():
                    numeros.append(texto.strip())

        if not numeros:
            raise PolizaNoEncontradaError("No se extrajeron números de póliza de la tabla")

        return numeros

    async def click_poliza(self, numero: str) -> None:
        # Nunca usar URL directa — navegar solo por click
        filas = await self._page.query_selector_all(self.XPATH_FILAS_TABLA)
        for fila in filas:
            link = await fila.query_selector("td:nth-child(1) a")
            if link:
                texto = await link.inner_text()
                if texto.strip() == numero:
                    await link.click()
                    await self._page.wait_for_load_state("networkidle")
                    return

        raise PolizaNoEncontradaError(f"Póliza {numero} no encontrada en resultados")
