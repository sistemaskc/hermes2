import asyncio

from playwright.async_api import Page

from src.domain.exceptions import PortalNoDisponibleError, SesionExpiradaError
from src.infrastructure.logger import logger

DOMINIO_PORTAL = "providaweb.metlife.mx"
DOMINIO_SSO = "federate.sso.metlife.com"
TEXTO_ERROR_CREDENCIALES = "No reconocemos el nombre de usuario"


class LoginPage:
    URL_BASE = f"https://{DOMINIO_PORTAL}/"
    URL_BUSQUEDA = f"https://{DOMINIO_PORTAL}/consultadorBusqueda/false"

    # Formulario de credenciales PingFederate SSO
    XPATH_INPUT_USUARIO = '//input[@id="username"]'
    XPATH_INPUT_PASSWORD = '//input[@id="password"]'
    XPATH_BTN_SUBMIT = '//button[@id="signOnButtonSpan"]'

    # Navegación por petición (dentro del portal autenticado)
    XPATH_BTN_CONSULTADOR = '//*[@id="root"]/div[3]/div/div/div[1]/div/div[2]/a'
    XPATH_BTN_INGRESAR = '//*[@id="root"]/div[3]/div/div/div/div/div[2]/a'

    OTP_TIMEOUT_SEGUNDOS = 900  # 15 minutos para que usuario ingrese OTP

    def __init__(self, page: Page, usuario: str, password: str):
        self._page = page
        self._usuario = usuario
        self._password = password

    async def hacer_login(self) -> None:
        try:
            await self._page.goto(self.URL_BASE, wait_until="networkidle")
            await self._page.wait_for_selector(self.XPATH_INPUT_USUARIO, timeout=15000)
            await self._page.fill(self.XPATH_INPUT_USUARIO, self._usuario)
            await self._page.fill(self.XPATH_INPUT_PASSWORD, self._password)
            await self._page.click(self.XPATH_BTN_SUBMIT)
            await self._page.wait_for_load_state("networkidle")
        except Exception as e:
            raise PortalNoDisponibleError(f"Error al enviar credenciales: {e}") from e

        await self._esperar_post_login()

    async def _esperar_post_login(self) -> None:
        # Esperar que la navegación post-submit se estabilice
        try:
            await self._page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        # Ya está en el portal — login sin OTP
        if DOMINIO_PORTAL in self._page.url:
            logger.info("LoginPage", "Login exitoso sin OTP")
            return

        # Detectar error de credenciales — buscar elemento de error sin leer page.content()
        try:
            error_el = await self._page.wait_for_selector(
                f'//*[contains(text(), "{TEXTO_ERROR_CREDENCIALES}")]',
                timeout=3000,
            )
            if error_el:
                raise PortalNoDisponibleError(
                    "Credenciales incorrectas. Verificar METLIFE_USUARIO y METLIFE_PASSWORD en .env"
                )
        except PortalNoDisponibleError:
            raise
        except Exception:
            pass  # No hay mensaje de error — continuar

        # Sigue en SSO — puede ser selección de método o ingreso de OTP
        logger.warning(
            "LoginPage",
            f"Posible OTP requerido. URL: {self._page.url} — "
            f"esperando hasta {self.OTP_TIMEOUT_SEGUNDOS}s para que el usuario complete el proceso",
        )

        # Auto-seleccionar correo electrónico si aparece pantalla de selección de método
        await self._seleccionar_metodo_otp()

        transcurrido = 0
        intervalo = 2
        while transcurrido < self.OTP_TIMEOUT_SEGUNDOS:
            await asyncio.sleep(intervalo)
            transcurrido += intervalo
            if DOMINIO_PORTAL in self._page.url:
                logger.info("LoginPage", f"Login completado tras OTP ({transcurrido}s)")
                return

        raise PortalNoDisponibleError(
            f"Timeout de {self.OTP_TIMEOUT_SEGUNDOS}s esperando OTP/login. "
            "El usuario no completó la autenticación a tiempo."
        )

    async def _seleccionar_metodo_otp(self) -> None:
        """Auto-click en 'Correo electrónico' si aparece pantalla de selección de método OTP."""
        try:
            boton_email = await self._page.wait_for_selector(
                '//*[contains(text(),"Correo electrónico")]/ancestor::*[@role="button" or self::button or self::a][1]',
                timeout=3000,
            )
            if boton_email:
                await boton_email.click()
                await self._page.wait_for_load_state("networkidle")
                logger.info("LoginPage", "Método OTP seleccionado: Correo electrónico. Esperando código del usuario.")
        except Exception:
            # Pantalla de selección no presente — ya está en pantalla de ingreso de código u otra
            pass

    async def click_ingresar_consultador(self) -> None:
        try:
            await self._page.wait_for_selector(self.XPATH_BTN_CONSULTADOR, timeout=10000)
            await self._page.click(self.XPATH_BTN_CONSULTADOR)
            await self._page.wait_for_load_state("networkidle")
        except Exception as e:
            raise SesionExpiradaError(f"No se encontró botón 'ingresar consultador': {e}") from e

    async def click_ingresar(self) -> None:
        try:
            await self._page.wait_for_selector(self.XPATH_BTN_INGRESAR, timeout=10000)
            await self._page.click(self.XPATH_BTN_INGRESAR)
            await self._page.wait_for_load_state("networkidle")
        except Exception as e:
            raise SesionExpiradaError(f"No se encontró botón 'ingresar': {e}") from e

    async def ir_a_busqueda(self) -> None:
        await self._page.goto(self.URL_BUSQUEDA, wait_until="networkidle")

    async def volver_a_consultador(self) -> None:
        await self._page.goto(self.URL_BUSQUEDA, wait_until="networkidle")

    async def sesion_activa(self) -> bool:
        try:
            await self._page.goto(self.URL_BUSQUEDA, wait_until="networkidle", timeout=10000)
            return DOMINIO_PORTAL in self._page.url
        except Exception:
            return False
