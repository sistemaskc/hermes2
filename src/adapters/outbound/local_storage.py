import io
from pathlib import Path

import img2pdf
from PIL import Image

from src.domain.ports import StoragePort
from src.domain.value_objects import Pestana, PESTANAS_ORDENADAS


class LocalStorageAdapter(StoragePort):
    def __init__(self, output_dir: Path):
        self._base = output_dir

    def guardar_captura(
        self,
        identificador: str,
        numero_poliza: str,
        pestana: Pestana,
        datos: bytes,
    ) -> Path:
        directorio = self._base / identificador
        directorio.mkdir(parents=True, exist_ok=True)
        ruta = directorio / f"{numero_poliza}_{pestana.value}.png"

        img = Image.open(io.BytesIO(datos)).convert("L")
        img.save(ruta, format="PNG")

        return ruta

    def listar_capturas(self, identificador: str, numero_poliza: str) -> list[Path]:
        directorio = self._base / identificador
        rutas = []
        for pestana in PESTANAS_ORDENADAS:
            ruta = directorio / f"{numero_poliza}_{pestana.value}.png"
            if ruta.exists():
                rutas.append(ruta)
        return rutas

    def generar_pdf(self, identificador: str, numero_poliza: str) -> Path:
        capturas = self.listar_capturas(identificador, numero_poliza)
        if not capturas:
            raise FileNotFoundError(
                f"Sin capturas para {numero_poliza} en {identificador}"
            )

        ruta_pdf = self._base / identificador / f"{numero_poliza}.pdf"
        with open(ruta_pdf, "wb") as f:
            f.write(img2pdf.convert([str(p) for p in capturas]))

        return ruta_pdf
