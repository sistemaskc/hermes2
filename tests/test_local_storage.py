import re
import pytest
from pathlib import Path
from PIL import Image

from src.adapters.outbound.local_storage import LocalStorageAdapter
from src.domain.value_objects import Pestana


def png_bytes(color: str = "red") -> bytes:
    img = Image.new("RGB", (100, 100), color=color)
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorageAdapter:
    return LocalStorageAdapter(output_dir=tmp_path)


def test_guardar_captura_crea_archivo(storage: LocalStorageAdapter, tmp_path: Path):
    ruta = storage.guardar_captura("POL001", Pestana.GENERAL, png_bytes())
    assert ruta.exists()
    assert ruta.name == "POL001_general.png"
    assert ruta.parent == tmp_path


def test_listar_capturas_respeta_orden(storage: LocalStorageAdapter):
    storage.guardar_captura("POL001", Pestana.AGENTES, png_bytes())
    storage.guardar_captura("POL001", Pestana.GENERAL, png_bytes())
    storage.guardar_captura("POL001", Pestana.COBERTURAS, png_bytes())

    rutas = storage.listar_capturas("POL001")
    nombres = [r.stem.split("_", 1)[1] for r in rutas]

    assert nombres == ["general", "coberturas", "agentes"]


def test_listar_capturas_omite_pestanas_no_guardadas(storage: LocalStorageAdapter):
    storage.guardar_captura("POL001", Pestana.GENERAL, png_bytes())

    rutas = storage.listar_capturas("POL001")
    assert len(rutas) == 1
    assert rutas[0].name == "POL001_general.png"


def test_generar_pdf_crea_archivo(storage: LocalStorageAdapter, tmp_path: Path):
    storage.guardar_captura("POL001", Pestana.GENERAL, png_bytes("red"))
    storage.guardar_captura("POL001", Pestana.COBERTURAS, png_bytes("blue"))

    ruta_pdf = storage.generar_pdf("POL001")

    assert ruta_pdf.exists()
    assert re.match(r"POL001_\d+\.pdf", ruta_pdf.name)
    assert ruta_pdf.stat().st_size > 0


def test_generar_pdf_elimina_pngs(storage: LocalStorageAdapter, tmp_path: Path):
    storage.guardar_captura("POL001", Pestana.GENERAL, png_bytes())
    storage.generar_pdf("POL001")

    assert list(tmp_path.glob("POL001_*.png")) == []


def test_generar_pdf_sin_capturas_lanza_error(storage: LocalStorageAdapter):
    with pytest.raises(FileNotFoundError):
        storage.generar_pdf("POL_INEXISTENTE")
