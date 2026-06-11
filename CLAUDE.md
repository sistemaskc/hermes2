# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"Hermes KC" — an RPA service that keeps a logged-in Playwright (Chromium) session against the MetLife portal (`https://providaweb.metlife.mx/`), exposes a FastAPI HTTP API, searches policies by RFC or policy number, screenshots each portal tab, and returns one PDF per policy. Code, identifiers, and docs are in Spanish (poliza, pestana, captura) — keep new code consistent with that.

## Commands

```bash
uv sync                                  # install deps (uv is the package manager)
uv run playwright install chromium       # one-time browser install
uv run python main.py                    # run the server (or iniciar.bat on Windows)
uv run pytest                            # run tests
uv run pytest tests/test_local_storage.py -v   # single test file
```

- Requires a `.env` (copy from `.env.example`) with `METLIFE_USUARIO` / `METLIFE_PASSWORD`. With `HEADLESS=false`, the portal's OTP must be completed manually in the visible browser at startup.
- `scripts/` contains manual integration scripts (`test_login.py`, `test_busqueda.py`, `inspect_*.py`) that drive the live portal — they are not pytest tests.
- `test_api.bat` exercises the running API with curl.

## Architecture

Hexagonal (Ports & Adapters). `main.py` does all DI wiring in the FastAPI lifespan and stores `SessionManager` and `ConsultarPolizaUseCase` on `app.state`.

- `src/domain/` — entities, value objects, `ConsultadorPort` / `StoragePort` ABCs ([ports.py](src/domain/ports.py)), domain exceptions. No framework imports here.
- `src/application/` — [use_cases.py](src/application/use_cases.py) (`ConsultarPolizaUseCase`: search → iterate policies → per tab capture screenshots with pagination → generate PDF) and [session_manager.py](src/application/session_manager.py).
- `src/adapters/inbound/` — FastAPI router + Pydantic schemas. Endpoints: `POST /consultar`, `GET /archivo`, `GET /health`, `GET /` (status page).
- `src/adapters/outbound/` — `PlaywrightConsultadorAdapter` (implements `ConsultadorPort`) composed of Page Objects in `pages/` (LoginPage, SearchPage, ResultsPage, PolicyPage); `LocalStorageAdapter` (implements `StoragePort`, PNG→PDF via Pillow/img2pdf).
- `src/infrastructure/logger.py` — custom logger used everywhere as `logger.info("Componente", "mensaje")`.

### Session lifecycle (the core invariant)

`SessionManager` owns a single browser session for the whole process:

- One request at a time via `asyncio.Lock`; a second concurrent `/consultar` is rejected immediately (`lock_ocupado()`), not queued.
- Background heartbeat every `HEARTBEAT_INTERVAL` (240s, below the portal's ~300s timeout) checks the session and re-logins automatically; it is skipped while state is `PROCESSING`.
- If `SesionExpiradaError` is raised mid-request, `sesion_activa()` re-logins and re-raises; the use case then retries the whole request exactly once. Clients never see the re-login.
- State machine: `INITIALIZING → ACTIVE ⇄ PROCESSING/HEARTBEATING/REINITIALIZING → ERROR` (exposed at `/health`).

### API conventions

The contract is [API_CONTRACT.md](API_CONTRACT.md) — keep it updated when changing endpoints. Key conventions:

- Business failures (policy not found, portal down, expired session) return HTTP **200 with `success: false`** and an `errorMessage`; only Pydantic validation returns 422.
- `identificador` type is inferred by length: exactly 6 chars → POLIZA, ≥10 → RFC, anything else → 422.
- Clients must use ≥300s timeouts; the response is synchronous.

### Tabs (pestañas) and output

- `Pestana` enum: general, saldos, agentes, coberturas, beneficiarios, servicios, cobranza, todo. `"todo"` expands via `PESTANAS_ORDENADAS` in [value_objects.py](src/domain/value_objects.py). **Capture (execution) order and PDF page order are intentionally different** (`PESTANAS_ORDENADAS` vs `PESTANAS_PDF`).
- `cobranza` is special: a fixed sub-navigation producing 4 screenshots via `capturar_cobranza()` instead of the normal screenshot/pagination loop.
- PNG intermediates go to `tmp/`, are converted to grayscale, consolidated into one PDF per policy under `output/`, then deleted. `GET /archivo` only serves paths inside `output/` (path-traversal check).

### Portal automation rules

- All XPaths/selectors live in the Page Objects under `src/adapters/outbound/pages/` — never inline them elsewhere; the portal DOM changes and they must be easy to update.
- **Never navigate to a policy by direct URL** — the portal rejects URL injection. Navigate only by clicks (search → results → policy).
- Everything is async Playwright (`async_playwright`); don't mix in sync API.

## Reference docs

- [API_CONTRACT.md](API_CONTRACT.md) — full HTTP contract with examples
- [PLAN.md](PLAN.md) — detailed architecture and design decisions
- [Proceso.md](Proceso.md) — official portal flow with XPaths
