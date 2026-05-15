import io
import re
import shutil
import time
from pathlib import Path

import img2pdf
from PIL import Image

from src.domain.ports import StoragePort
from src.domain.value_objects import Pestana, PESTANAS_ORDENADAS


class LocalStorageAdapter(StoragePort):
    def __init__(self, output_dir: Path, tmp_dir: Path):
        self._base = output_dir
        self._tmp = tmp_dir
        self._base.mkdir(parents=True, exist_ok=True)
        self._tmp.mkdir(parents=True, exist_ok=True)

    def guardar_captura(self, numero_poliza: str, pestana: Pestana, pagina: int, datos: bytes) -> Path:
        ruta = self._tmp / f"{numero_poliza}_{pestana.value}_p{pagina}.png"

        img = Image.open(io.BytesIO(datos))
        if img.height > 150:
            img = img.crop((0, 0, img.width, img.height - 150))
        img = img.convert("L")
        img.save(ruta, format="PNG")

        return ruta

    def listar_capturas(self, numero_poliza: str) -> list[Path]:
        rutas = []
        for pestana in PESTANAS_ORDENADAS:
            paginas = list(self._tmp.glob(f"{numero_poliza}_{pestana.value}_p*.png"))
            paginas.sort(key=lambda p: self._numero_pagina(p))
            rutas.extend(paginas)
        return rutas

    def generar_pdf(self, numero_poliza: str) -> Path:
        capturas = self.listar_capturas(numero_poliza)
        if not capturas:
            raise FileNotFoundError(f"Sin capturas para {numero_poliza}")

        timestamp = int(time.time())
        nombre = f"{numero_poliza}_{timestamp}.pdf"

        ruta_tmp = self._tmp / nombre
        with open(ruta_tmp, "wb") as f:
            f.write(img2pdf.convert([str(p) for p in capturas]))

        ruta_final = self._base / nombre
        shutil.move(str(ruta_tmp), str(ruta_final))

        self.limpiar_capturas(numero_poliza)
        return ruta_final

    def limpiar_capturas(self, numero_poliza: str) -> None:
        for png in self._tmp.glob(f"{numero_poliza}_*.png"):
            png.unlink(missing_ok=True)

    @staticmethod
    def _numero_pagina(ruta: Path) -> int:
        m = re.search(r"_p(\d+)\.png$", ruta.name)
        return int(m.group(1)) if m else 0
