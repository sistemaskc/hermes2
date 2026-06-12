from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.adapters.inbound.api import router
from src.adapters.outbound.local_storage import LocalStorageAdapter
from src.adapters.outbound.playwright_consultador import PlaywrightConsultadorAdapter
from src.application.session_manager import SessionManager
from src.application.use_cases import ConsultarPolizaUseCase
from src.config import settings
from src.infrastructure.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    adapter = PlaywrightConsultadorAdapter(
        usuario=settings.metlife_usuario,
        password=settings.metlife_password,
        headless=settings.headless,
    )
    storage = LocalStorageAdapter(output_dir=settings.output_dir, tmp_dir=settings.tmp_dir)
    manager = SessionManager(
        consultador=adapter,
        heartbeat_interval=settings.heartbeat_interval,
        max_reintentos=settings.max_reintentos,
    )
    use_case = ConsultarPolizaUseCase(
        session_manager=manager,
        consultador=adapter,
        storage=storage,
    )

    app.state.session_manager = manager
    app.state.use_case = use_case

    await manager.startup()
    yield
    await manager.shutdown()
    logger.close()


class RestringirDocsMiddleware(BaseHTTPMiddleware):
    _RUTAS_DOCS = {"/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._RUTAS_DOCS:
            host = request.client.host if request.client else ""
            if host not in ("127.0.0.1", "::1"):
                return Response(status_code=404)
        return await call_next(request)


app = FastAPI(title="Hermes KC", lifespan=lifespan)

app.add_middleware(RestringirDocsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    max_age=86400,
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)
