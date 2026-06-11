import socket
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse

from src.adapters.inbound.schemas import (
    ConsultaRequestSchema,
    ConsultaResponseSchema,
    FileDataSchema,
)
from src.application.use_cases import ConsultarPolizaUseCase
from src.config import VERSION, settings
from src.domain.entities import ConsultaRequest
from src.domain.exceptions import (
    CapturaFallidaError,
    PolizaNoEncontradaError,
    PortalNoDisponibleError,
    SesionExpiradaError,
)
from src.infrastructure.logger import logger

router = APIRouter()


def get_use_case(request: Request) -> ConsultarPolizaUseCase:
    return request.app.state.use_case


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request):
    session = request.app.state.session_manager
    estado = session.estado.value
    color = {"activa": "#22c55e", "iniciando": "#f59e0b", "error": "#ef4444"}.get(estado, "#6b7280")
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = "desconocida"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hermes KC</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }}
    .card {{ background: #1e293b; border-radius: 12px; padding: 2.5rem 3rem; max-width: 480px; width: 100%; box-shadow: 0 4px 32px #0004; }}
    h1 {{ margin: 0 0 0.25rem; font-size: 1.5rem; }}
    .sub {{ color: #94a3b8; font-size: 0.9rem; margin-bottom: 2rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: #0f172a; border-radius: 999px; padding: 0.3rem 0.9rem; font-size: 0.85rem; font-weight: 600; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: {color}; }}
    .links {{ margin-top: 2rem; display: flex; gap: 1rem; }}
    a {{ color: #38bdf8; text-decoration: none; font-size: 0.9rem; }}
    a:hover {{ text-decoration: underline; }}
    .divider {{ border: none; border-top: 1px solid #334155; margin: 1.5rem 0; }}
    .row {{ display: flex; justify-content: space-between; font-size: 0.85rem; color: #94a3b8; margin: 0.4rem 0; }}
    .row span:last-child {{ color: #e2e8f0; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Hermes KC</h1>
    <p class="sub">API de consulta automatizada de pólizas</p>
    <div class="badge"><span class="dot"></span>Sesión: {estado}</div>
    <hr class="divider">
    <div class="row"><span>Servidor</span><span>{hostname}</span></div>
    <div class="row"><span>IP</span><span>{ip}</span></div>
    <div class="row"><span>Endpoint consulta</span><span>POST /consultar</span></div>
    <div class="row"><span>Health check</span><span>GET /health</span></div>
    <div class="row"><span>Descarga archivo</span><span>GET /archivo</span></div>
    <div class="links">
      <a href="/docs">Documentación interactiva →</a>
      <a href="/health">Health check →</a>
    </div>
  </div>
</body>
</html>"""


@router.get("/health")
async def health(request: Request):
    session = request.app.state.session_manager
    return {"estado": session.estado.value, "version": VERSION}


@router.get("/archivo")
async def descargar_archivo(path: str, disposition: str = "inline"):
    output_dir = settings.output_dir.resolve()
    archivo = Path(path)
    if not archivo.is_absolute():
        archivo = Path.cwd() / archivo
    archivo = archivo.resolve()

    if not str(archivo).startswith(str(output_dir)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruta no permitida.")
    if not archivo.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")
    if disposition not in ("inline", "attachment"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="disposition debe ser 'inline' o 'attachment'.")

    media_type = "application/pdf" if archivo.suffix == ".pdf" else "image/png"
    return FileResponse(
        path=str(archivo),
        media_type=media_type,
        headers={
            "Content-Disposition": f'{disposition}; filename="{archivo.name}"',
            "X-Frame-Options": "ALLOWALL",
        },
    )


@router.post("/consultar", response_model=ConsultaResponseSchema)
async def consultar(
    body: ConsultaRequestSchema,
    use_case: ConsultarPolizaUseCase = Depends(get_use_case),
):
    try:
        dominio_request = ConsultaRequest(
            identificador=body.identificador,
            tipo=body.tipo,
            pestanas=body.pestanas,
            numero_telefono=body.numero_telefono,
        )
        polizas = await use_case.execute(dominio_request)
    except PolizaNoEncontradaError as e:
        return ConsultaResponseSchema(success=False, errorMessage=str(e))
    except (PortalNoDisponibleError, SesionExpiradaError, CapturaFallidaError) as e:
        return ConsultaResponseSchema(success=False, errorMessage=str(e))
    except Exception as e:
        logger.error("API", f"Error inesperado en consulta {body.identificador}: {e}")
        return ConsultaResponseSchema(success=False, errorMessage=str(e))

    return ConsultaResponseSchema(
        success=True,
        data=[FileDataSchema(file_name=Path(p.ruta_pdf).name) for p in polizas],
    )
