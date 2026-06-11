from playwright.async_api import async_playwright, Browser, Page, Playwright

from src.adapters.outbound.pages.login_page import LoginPage
from src.adapters.outbound.pages.policy_page import PolicyPage
from src.adapters.outbound.pages.results_page import ResultsPage
from src.adapters.outbound.pages.search_page import SearchPage
from src.domain.ports import ConsultadorPort, EstadoSesion
from src.domain.value_objects import Pestana, TipoIdentificador


class PlaywrightConsultadorAdapter(ConsultadorPort):
    def __init__(self, usuario: str, password: str, headless: bool = False):
        self._usuario = usuario
        self._password = password
        self._headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._estado = EstadoSesion.INITIALIZING

    async def inicializar(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._page = await self._browser.new_page()

    async def cerrar(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    # --- ConsultadorPort ---

    async def login(self) -> None:
        page = LoginPage(self._page, self._usuario, self._password)
        await page.hacer_login()
        self._estado = EstadoSesion.ACTIVE

    async def ir_a_busqueda(self) -> None:
        page = LoginPage(self._page, self._usuario, self._password)
        await page.click_ingresar_consultador()
        await page.click_ingresar()

    async def buscar(self, identificador: str, tipo: TipoIdentificador) -> None:
        page = SearchPage(self._page)
        await page.ingresar_identificador(identificador, tipo)
        await page.click_buscar()

    async def confirmar_dialogo(self) -> None:
        page = SearchPage(self._page)
        await page.confirmar_dialogo()

    async def obtener_polizas_resultado(self) -> list[str]:
        page = ResultsPage(self._page)
        return await page.obtener_numeros_poliza()

    async def abrir_poliza(self, numero: str) -> None:
        page = ResultsPage(self._page)
        await page.click_poliza(numero)

    async def navegar_pestana(self, pestana: Pestana) -> None:
        page = PolicyPage(self._page)
        await page.navegar_pestana(pestana)

    async def capturar_screenshot(self) -> bytes:
        page = PolicyPage(self._page)
        return await page.capturar_screenshot()

    async def capturar_cobranza(self) -> list[bytes]:
        page = PolicyPage(self._page)
        return await page.capturar_cobranza()

    async def tiene_siguiente_pagina(self) -> bool:
        page = PolicyPage(self._page)
        return await page.tiene_siguiente_pagina()

    async def post_captura(self, pestana: Pestana) -> None:
        page = PolicyPage(self._page)
        await page.post_captura(pestana)

    async def navegar_siguiente_pagina(self) -> None:
        page = PolicyPage(self._page)
        await page.navegar_siguiente_pagina()

    async def volver_a_consultador(self) -> None:
        page = LoginPage(self._page, self._usuario, self._password)
        await page.volver_a_consultador()

    async def heartbeat(self) -> bool:
        login_page = LoginPage(self._page, self._usuario, self._password)
        activa = await login_page.sesion_activa()
        self._estado = EstadoSesion.ACTIVE if activa else EstadoSesion.ERROR
        return activa

    def estado_sesion(self) -> EstadoSesion:
        return self._estado
