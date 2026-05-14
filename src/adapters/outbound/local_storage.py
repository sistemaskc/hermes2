import io
import time
from pathlib import Path

import img2pdf
from PIL import Image

from src.domain.ports import StoragePort
from src.domain.value_objects import Pestana, PESTANAS_ORDENADAS


class LocalStorageAdapter(StoragePort):
    def __init__(self, output_dir: Path):
        self._base = output_dir
        self._base.mkdir(parents=True, exist_ok=True)

    def guardar_captura(self, numero_poliza: str, pestana: Pestana, datos: bytes) -> Path:
        ruta = self._base / f"{numero_poliza}_{pestana.value}.png"

        img = Image.open(io.BytesIO(datos))
        if img.height > 150:
            img = img.crop((0, 0, img.width, img.height - 150))
        img = img.convert("L")
        img.save(ruta, format="PNG")

        return ruta

    def listar_capturas(self, numero_poliza: str) -> list[Path]:
        rutas = []
        for pestana in PESTANAS_ORDENADAS:
            ruta = self._base / f"{numero_poliza}_{pestana.value}.png"
            if ruta.exists():
                rutas.append(ruta)
        return rutas

    def generar_pdf(self, numero_poliza: str) -> Path:
        capturas = self.listar_capturas(numero_poliza)
        if not capturas:
            raise FileNotFoundError(f"Sin capturas para {numero_poliza}")

        timestamp = int(time.time())
        ruta_pdf = self._base / f"{numero_poliza}_{timestamp}.pdf"
        with open(ruta_pdf, "wb") as f:
            f.write(img2pdf.convert([str(p) for p in capturas]))

        self.limpiar_capturas(numero_poliza)
        return ruta_pdf

    def limpiar_capturas(self, numero_poliza: str) -> None:
        for png in self._base.glob(f"{numero_poliza}_*.png"):
            png.unlink(missing_ok=True)
