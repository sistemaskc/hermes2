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
    return LocalStorageAdapter(output_dir=tmp_path / "output", tmp_dir=tmp_path / "tmp")


def test_guardar_captura_crea_archivo(storage: LocalStorageAdapter, tmp_path: Path):
    ruta = storage.guardar_captura("POL001", Pestana.GENERAL, 1, png_bytes())
    assert ruta.exists()
    assert ruta.name == "POL001_general_p1.png"


def test_guardar_captura_varias_paginas(storage: LocalStorageAdapter, tmp_path: Path):
    r1 = storage.guardar_captura("POL001", Pestana.GENERAL, 1, png_bytes())
    r2 = storage.guardar_captura("POL001", Pestana.GENERAL, 2, png_bytes("blue"))
    assert r1.name == "POL001_general_p1.png"
    assert r2.name == "POL001_general_p2.png"


def test_listar_capturas_respeta_orden_pestana_y_pagina(storage: LocalStorageAdapter):
    storage.guardar_captura("POL001", Pestana.COBERTURAS, 1, png_bytes())
    storage.guardar_captura("POL001", Pestana.GENERAL, 2, png_bytes())
    storage.guardar_captura("POL001", Pestana.GENERAL, 1, png_bytes())

    rutas = storage.listar_capturas("POL001")
    nombres = [r.name for r in rutas]

    assert nombres == ["POL001_general_p1.png", "POL001_general_p2.png", "POL001_coberturas_p1.png"]


def test_listar_capturas_omite_pestanas_no_guardadas(storage: LocalStorageAdapter):
    storage.guardar_captura("POL001", Pestana.GENERAL, 1, png_bytes())
    rutas = storage.listar_capturas("POL001")
    assert len(rutas) == 1


def test_generar_pdf_crea_archivo_en_output(storage: LocalStorageAdapter, tmp_path: Path):
    storage.guardar_captura("POL001", Pestana.GENERAL, 1, png_bytes("red"))
    storage.guardar_captura("POL001", Pestana.COBERTURAS, 1, png_bytes("blue"))

    ruta_pdf = storage.generar_pdf("POL001")

    assert ruta_pdf.exists()
    assert ruta_pdf.parent == tmp_path / "output"
    assert re.match(r"POL001_\d+\.pdf", ruta_pdf.name)
    assert ruta_pdf.stat().st_size > 0


def test_generar_pdf_elimina_pngs(storage: LocalStorageAdapter, tmp_path: Path):
    storage.guardar_captura("POL001", Pestana.GENERAL, 1, png_bytes())
    storage.generar_pdf("POL001")
    assert list((tmp_path / "output").glob("POL001_*.png")) == []


def test_generar_pdf_tmp_vacio_al_terminar(storage: LocalStorageAdapter, tmp_path: Path):
    storage.guardar_captura("POL001", Pestana.GENERAL, 1, png_bytes())
    storage.generar_pdf("POL001")
    assert list((tmp_path / "tmp").glob("*.pdf")) == []


def test_generar_pdf_sin_capturas_lanza_error(storage: LocalStorageAdapter):
    with pytest.raises(FileNotFoundError):
        storage.generar_pdf("POL_INEXISTENTE")
