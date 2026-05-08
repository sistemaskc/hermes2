from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

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
    storage = LocalStorageAdapter(output_dir=settings.output_dir)
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


app = FastAPI(title="RPA Consultador MetLife", lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)
