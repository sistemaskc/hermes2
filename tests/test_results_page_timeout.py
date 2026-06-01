import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.adapters.outbound.pages.results_page import ResultsPage
from src.domain.exceptions import PolizaNoEncontradaError


async def _portal_lento(xpath, timeout):
    """Simula portal que tarda 20s en responder (más que el viejo 15s)."""
    await asyncio.sleep(20)
    return MagicMock()


def _make_mock_row(numero: str):
    link = AsyncMock()
    link.inner_text = AsyncMock(return_value=numero)
    row = AsyncMock()
    row.query_selector = AsyncMock(return_value=link)
    return row


@pytest.mark.asyncio
async def test_portal_lento_20s_no_revienta_con_timeout_90s():
    """Portal tarda 20s. Con timeout 90s debe completar exitosamente."""
    page = MagicMock()
    page.wait_for_selector = _portal_lento
    page.query_selector_all = AsyncMock(return_value=[_make_mock_row("MYT871")])

    results = ResultsPage(page)
    numeros = await results.obtener_numeros_poliza()

    assert numeros == ["MYT871"]


@pytest.mark.asyncio
async def test_timeout_real_de_playwright_se_envuelve_como_poliza_no_encontrada():
    """Cuando playwright lanza timeout, ResultsPage lo convierte en PolizaNoEncontradaError."""
    async def playwright_timeout(xpath, timeout):
        raise Exception(f"Page.wait_for_selector: Timeout {timeout}ms exceeded.")

    page = MagicMock()
    page.wait_for_selector = playwright_timeout

    results = ResultsPage(page)

    with pytest.raises(PolizaNoEncontradaError, match="Tabla de resultados no encontrada"):
        await results.obtener_numeros_poliza()
