from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.adapters.inbound.schemas import (
    ConsultaRequestSchema,
    ConsultaResponseSchema,
    CapturaSchema,
    PolizaSchema,
)
from src.application.use_cases import ConsultarPolizaUseCase
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
