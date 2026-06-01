from playwright.async_api import Page

from src.domain.exceptions import PortalNoDisponibleError
from src.domain.value_objects import TipoIdentificador


class SearchPage:
    XPATH_INPUT_POLIZA = '//input[@name="poliza"]'
    XPATH_INPUT_RFC = '//input[@name="rfc"]'
    XPATH_BTN_BUSCAR = 'text=BUSCAR'
    XPATH_BTN_OK = '//button[normalize-space()="OK"]'

    def __init__(self, page: Page):
        self._page = page

    async def ingresar_identificador(
        self, identificador: str, tipo: TipoIdentificador
    ) -> None:
        try:
            if tipo == TipoIdentificador.POLIZA:
                await self._page.wait_for_selector(self.XPATH_INPUT_POLIZA, timeout=10000)
                await self._page.focus(self.XPATH_INPUT_POLIZA)
                await self._page.type(self.XPATH_INPUT_POLIZA, identificador, delay=50)
            else:
                await self._page.wait_for_selector(self.XPATH_INPUT_RFC, timeout=10000)
                await self._page.focus(self.XPATH_INPUT_RFC)
                await self._page.type(self.XPATH_INPUT_RFC, identificador, delay=50)
        except Exception as e:
            raise PortalNoDisponibleError(f"No se encontró campo de búsqueda: {e}") from e

    async def click_buscar(self) -> None:
        try:
            await self._page.wait_for_selector(self.XPATH_BTN_BUSCAR, timeout=10000)
            await self._page.click(self.XPATH_BTN_BUSCAR)
            await self._page.wait_for_load_state("networkidle", timeout=90000)
        except Exception as e:
            raise PortalNoDisponibleError(f"Error al hacer click en buscar: {e}") from e

    async def confirmar_dialogo(self) -> None:
        try:
            dialogo = await self._page.wait_for_selector(
                self.XPATH_BTN_OK, timeout=5000
            )
            if dialogo:
                await self._page.click(self.XPATH_BTN_OK)
                await self._page.wait_for_load_state("networkidle")
        except Exception:
            # Diálogo no aparece en todos los casos — no es error
            pass
