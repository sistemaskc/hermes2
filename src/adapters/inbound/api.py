from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from src.adapters.inbound.schemas import (
    ConsultaRequestSchema,
    ConsultaResponseSchema,
    FileDataSchema,
)
from src.application.use_cases import ConsultarPolizaUseCase
from src.config import settings
from src.domain.entities import ConsultaRequest
from src.domain.exceptions import (
    CapturaFallidaError,
    ColaSaturadaError,
    PolizaNoEncontradaError,
    PortalNoDisponibleError,
    SesionExpiradaError,
)
from src.infrastructure.logger import logger

router = APIRouter()


def get_use_case(request: Request) -> ConsultarPolizaUseCase:
    return request.app.state.use_case


@router.get("/health")
async def health(request: Request):
    session = request.app.state.session_manager
    return {"estado": session.estado.value, "pending": session.pending}


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
    except ColaSaturadaError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
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
