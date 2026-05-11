from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from src.adapters.inbound.schemas import (
    ConsultaRequestSchema,
    ConsultaResponseSchema,
    CapturaSchema,
    PolizaSchema,
)
from src.application.use_cases import ConsultarPolizaUseCase
from src.config import settings
from src.domain.entities import ConsultaRequest
from src.domain.exceptions import PolizaNoEncontradaError, PortalNoDisponibleError
from src.infrastructure.logger import logger

router = APIRouter()


def get_use_case(request: Request) -> ConsultarPolizaUseCase:
    return request.app.state.use_case


@router.get("/health")
async def health(request: Request):
    session = request.app.state.session_manager
    return {"estado": session.estado.value}


@router.get("/archivo")
async def descargar_archivo(path: str):
    output_dir = settings.output_dir.resolve()
    archivo = Path(path)
    if not archivo.is_absolute():
        archivo = Path.cwd() / archivo
    archivo = archivo.resolve()

    if not str(archivo).startswith(str(output_dir)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruta no permitida.")
    if not archivo.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")

    is_pdf = archivo.suffix == ".pdf"
    media_type = "application/pdf" if is_pdf else "image/png"
    disposition = f'inline; filename="{archivo.name}"' if is_pdf else f'attachment; filename="{archivo.name}"'
    return FileResponse(
        path=str(archivo),
        media_type=media_type,
        headers={
            "Content-Disposition": disposition,
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
    except PortalNoDisponibleError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PolizaNoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("API", f"Error inesperado en consulta {body.identificador}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return ConsultaResponseSchema(
        polizas=[
            PolizaSchema(
                numero=p.numero,
                capturas=[
                    CapturaSchema(pestana=c.pestana, ruta_archivo=str(c.ruta_archivo))
                    for c in p.capturas
                ],
                ruta_pdf=str(p.ruta_pdf),
            )
            for p in polizas
        ]
    )
