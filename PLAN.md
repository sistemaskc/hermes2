# Plan de Implementación — RPA Consultador MetLife

## Contexto

RPA que mantiene sesión activa en el portal MetLife (`https://providaweb.metlife.mx/`), recibe peticiones HTTP, ejecuta búsquedas por RFC o número de póliza, captura screenshots por pestaña y devuelve rutas de archivos generados.

---

## Decisiones de arquitectura

| Decisión | Valor |
|----------|-------|
| Patrón | Arquitectura Hexagonal + SOLID |
| Lenguaje | Python 3.12+ |
| Gestor de paquetes | uv |
| Browser automation | Playwright (async) |
| HTTP server | FastAPI + uvicorn |
| Credenciales | `.env` vía `pydantic-settings` |
| Concurrencia | 1 request a la vez (`asyncio.Lock`) |
| Respuesta API | Síncrona — cliente espera resultado completo |
| Storage | Filesystem local (Azure VM) |
| RFC múltiples | Archivos separados por número de póliza |
| PDF | Una PDF por póliza, generada en v1 tras screenshots |
| Sesión | Login único al startup + heartbeat cada 4 min |
| Deploy | Azure VM — uvicorn directo o detrás de nginx |

---

## Estructura de carpetas

```
rpa_consultador/
├── pyproject.toml
├── uv.lock
├── .env                          ← credenciales (no commitear)
├── .env.example
├── .gitignore
├── main.py                       ← entrypoint: wiring DI + arranque
│
├── src/
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities.py           ← ConsultaRequest, Poliza, Captura
│   │   ├── value_objects.py      ← RFC, NumeroPoliza, Pestana (Enum)
│   │   ├── ports.py              ← ConsultadorPort, StoragePort (ABC)
│   │   └── exceptions.py         ← SesionExpiradaError, PortalNoDisponibleError
│   │
│   ├── application/
│   │   ├── __init__.py
│   │   ├── use_cases.py          ← ConsultarPolizaUseCase
│   │   └── session_manager.py    ← SessionManager (lifecycle + heartbeat)
│   │
│   └── adapters/
│       ├── inbound/
│       │   ├── __init__.py
│       │   └── api.py            ← FastAPI router, Pydantic schemas
│       └── outbound/
│           ├── __init__.py
│           ├── playwright_consultador.py  ← implementa ConsultadorPort
│           │   ├── pages/
│           │   │   ├── login_page.py
│           │   │   ├── search_page.py
│           │   │   ├── results_page.py
│           │   │   └── policy_page.py
│           └── local_storage.py           ← implementa StoragePort
│
└── output/                       ← generado en runtime
    └── {RFC_o_poliza}/
        └── {num_poliza}_{pestana}.png
```

---

## Dominio

### Entidades (`domain/entities.py`)

```
ConsultaRequest
    identificador: str          ← RFC o número de póliza
    tipo: TipoIdentificador     ← Enum: RFC | POLIZA
    pestanas: list[Pestana]     ← pestañas a capturar

Poliza
    numero: NumeroPoliza
    capturas: list[Captura]
    ruta_pdf: Path | None        ← None hasta que generar_pdf() se ejecute

Captura
    pestana: Pestana
    ruta_archivo: Path
```

### Value Objects (`domain/value_objects.py`)

```
TipoIdentificador (Enum)
    RFC
    POLIZA

Pestana (Enum)
    GENERAL
    COBERTURAS
    BENEFICIARIOS
    SERVICIOS
    AGENTES
    TODO                        ← expande a todas las anteriores

NumeroPoliza                    ← str validado, inmutable
RFC                             ← str validado formato RFC MX, inmutable
```

### Puertos (`domain/ports.py`)

```
ConsultadorPort (ABC)
    login() → None
    ir_a_busqueda() → None
    buscar(identificador, tipo) → None
    confirmar_dialogo() → None
    obtener_polizas_resultado() → list[str]   ← lista de números de póliza
    abrir_poliza(numero) → None
    navegar_pestana(pestana: Pestana) → None
    capturar_screenshot() → bytes
    heartbeat() → bool                         ← True = sesión viva
    estado_sesion() → EstadoSesion

StoragePort (ABC)
    guardar_captura(identificador, numero_poliza, pestana, datos: bytes) → Path
    listar_capturas(identificador, numero_poliza) → list[Path]
    generar_pdf(identificador, numero_poliza) → Path   ← consolida capturas de esa póliza
```

### Excepciones (`domain/exceptions.py`)

```
SesionExpiradaError
PortalNoDisponibleError
PolizaNoEncontradaError
CapturaFallidaError
```

---

## Aplicación

### SessionManager (`application/session_manager.py`)

Responsabilidad única: ciclo de vida de la sesión del browser.

```
Estados
    INITIALIZING
    ACTIVE
    PROCESSING        ← durante request, heartbeat pausado
    HEARTBEATING
    ERROR
    REINITIALIZING

Comportamiento
    startup()
        → inicializa Playwright
        → llama ConsultadorPort.login()
        → inicia tarea background heartbeat (asyncio.create_task)

    heartbeat_loop()
        → cada 4 minutos (240s < timeout portal 300s)
        → si estado == PROCESSING: esperar
        → llamar ConsultadorPort.heartbeat()
        → si devuelve False: trigger re_login()

    re_login()
        → estado = REINITIALIZING
        → hasta 3 intentos con backoff 5s
        → ConsultadorPort.login()
        → estado = ACTIVE
        → si 3 intentos fallan: estado = ERROR, alerta log

    acquire_lock()        ← asyncio.Lock, un request a la vez
    release_lock()
    shutdown()            ← cierra browser limpiamente
```

### ConsultarPolizaUseCase (`application/use_cases.py`)

```
execute(request: ConsultaRequest) → list[Poliza]

    1. session_manager.acquire_lock()
    2. session_manager.estado = PROCESSING
    3. consultador.ir_a_busqueda()
    4. click "ingresar consultador"
    5. click "ingresar"
    6. consultador.buscar(request.identificador, request.tipo)
    7. consultador.confirmar_dialogo()
    8. numeros_poliza = consultador.obtener_polizas_resultado()
    9. por cada numero en numeros_poliza:
           consultador.abrir_poliza(numero)
           pestanas = expandir_todo(request.pestanas)
           por cada pestana:
               consultador.navegar_pestana(pestana)
               bytes = consultador.capturar_screenshot()
               ruta = storage.guardar_captura(request.identificador, numero, pestana, bytes)
               capturas.append(Captura(pestana, ruta))
           ruta_pdf = storage.generar_pdf(request.identificador, numero)
           polizas.append(Poliza(numero, capturas, ruta_pdf))
           consultador.ir_a_busqueda()   ← URL: consultadorBusqueda/false
   10. session_manager.estado = ACTIVE
   11. session_manager.release_lock()
   12. return polizas
```

---

## Adapters

### Inbound — API (`adapters/inbound/api.py`)

```
POST /consultar
    Body:
        identificador: str          ← RFC o número de póliza
        tipo: "RFC" | "POLIZA"
        pestanas: list[str]         ← ["general", "coberturas", ...] | ["todo"]

    Response 200:
        polizas: [
            {
                numero: str,
                capturas: [
                    { pestana: str, ruta: str }
                ]
            }
        ]

    Response 409:  ← request en proceso (lock ocupado)
        { error: "Consulta en proceso, reintentar" }

    Response 503:  ← sesión en ERROR
        { error: "Sesión no disponible" }

GET /health
    Response:
        { estado_sesion: str, version: str }
```

### Outbound — Playwright (`adapters/outbound/playwright_consultador.py`)

Organizado por Page Object Model. Cada page encapsula sus XPaths.

```
LoginPage
    URL_BASE = "https://providaweb.metlife.mx/"
    XPATH_BTN_CONSULTADOR = '//*[@id="root"]/div[3]/div/div/div[1]/div/div[2]/a'
    XPATH_BTN_INGRESAR    = '//*[@id="root"]/div[3]/div/div/div/div/div[2]/a'
    métodos: ir_a_login(), click_consultador(), click_ingresar()

SearchPage
    URL = "https://providaweb.metlife.mx/consultadorBusqueda/false"
    XPATH_INPUT_POLIZA = '//input[@name="poliza"]'           ← validado
    XPATH_INPUT_RFC    = '//input[@name="rfc"]'              ← validado
    XPATH_BTN_BUSCAR   = '//button[normalize-space()="BUSCAR"]'  ← validado
    XPATH_BTN_OK       = '/html/body/div[2]/div/div[3]/button[1]'  ← pendiente validar
    métodos: ingresar_poliza(num), ingresar_rfc(rfc), buscar(), confirmar()

ResultsPage
    XPATH_FILAS_TABLA = '//*[@id="root"]/div[3]/div/div[2]/div[2]/table/tbody/tr'
    XPATH_LINK_POLIZA = 'td[1]/a'                ← relativo a cada fila
    métodos: obtener_numeros_poliza() → list[str], click_poliza(numero)

PolicyPage
    XPATHS_PESTANAS = {
        Pestana.GENERAL:       'text=INFORMACIÓN GENERAL',   ← validado
        Pestana.COBERTURAS:    'text=COBERTURAS',            ← validado
        Pestana.BENEFICIARIOS: 'text=BENEFICIARIOS',         ← validado
        Pestana.SERVICIOS:     'text=SERVICIOS',             ← validado
        Pestana.AGENTES:       'text=AGENTES',               ← validado
    }
    # Tabs son botones al fondo de página, no <a> en tabla como indicaban XPaths originales
    métodos: navegar_pestana(pestana), capturar_screenshot() → bytes
```

### Outbound — Storage (`adapters/outbound/local_storage.py`)

```
Estructura de archivos:
    output/
        {identificador}/              ← RFC o número de póliza buscado
            {num_poliza}_general.png
            {num_poliza}_coberturas.png
            {num_poliza}_beneficiarios.png
            ...

Métodos:
    guardar_captura(identificador, num_poliza, pestana, datos) → Path
    listar_capturas(identificador, num_poliza) → list[Path]
    generar_pdf(identificador, num_poliza) → Path   ← Pillow: save PNG list as PDF

Estructura de archivos:
    output/
        {identificador}/
            {num_poliza}_general.png
            {num_poliza}_coberturas.png
            ...
            {num_poliza}.pdf              ← generado tras capturar todas las pestañas
```

---

## Configuración (`pydantic-settings`)

```
Settings (.env)
    METLIFE_USUARIO: str
    METLIFE_PASSWORD: str
    HEARTBEAT_INTERVAL_SECONDS: int = 240
    MAX_REINTENTOS_LOGIN: int = 3
    OUTPUT_DIR: Path = ./output
    HOST: str = 0.0.0.0
    PORT: int = 8000
    LOG_LEVEL: str = INFO
```

---

## Paquetes (`pyproject.toml`)

```toml
[project]
name = "rpa-consultador"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "playwright",
    "pydantic",
    "pydantic-settings",
    "pillow",
]

[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "httpx",
]
```

---

## Fases de implementación

### Fase 1 — Scaffolding
- [ ] `uv init rpa_consultador`
- [ ] Crear estructura de carpetas
- [ ] `pyproject.toml` con dependencias
- [ ] `.env.example`
- [ ] `.gitignore`
- [ ] `playwright install chromium`

### Fase 2 — Dominio
- [ ] `value_objects.py` — Pestana, TipoIdentificador, RFC, NumeroPoliza
- [ ] `entities.py` — ConsultaRequest, Poliza, Captura
- [ ] `ports.py` — ConsultadorPort, StoragePort (ABC)
- [ ] `exceptions.py`

### Fase 3 — Adapter Storage
- [ ] `local_storage.py` — implementa StoragePort
- [ ] `guardar_captura()` — escribe PNG a disco
- [ ] `listar_capturas()` — retorna paths ordenados por pestaña
- [ ] `generar_pdf()` — consolida PNGs de póliza en PDF usando Pillow
- [ ] Tests unitarios de storage y generación PDF

### Fase 4 — Adapter Playwright (Page Objects)
- [ ] `login_page.py`
- [ ] `search_page.py`
- [ ] `results_page.py`
- [ ] `policy_page.py`
- [ ] `playwright_consultador.py` — ensambla pages, implementa ConsultadorPort
- [ ] Validar XPaths manualmente contra portal antes de codificar

### Fase 5 — Session Manager
- [ ] `session_manager.py` — startup, heartbeat loop, re-login, lock
- [ ] Validar comportamiento heartbeat contra timeout real del portal (5 min)

### Fase 6 — Use Case
- [ ] `use_cases.py` — ConsultarPolizaUseCase
- [ ] Tests de integración con mock de ConsultadorPort

### Fase 7 — Adapter API
- [ ] `api.py` — FastAPI router, schemas Pydantic
- [ ] `main.py` — DI wiring, lifespan startup/shutdown
- [ ] Tests de endpoints con httpx

### Fase 8 — Deploy Azure VM
- [ ] Instalar uv + Python 3.12 en VM
- [ ] `playwright install chromium --with-deps`
- [ ] Configurar servicio systemd o tarea Windows para arranque automático
- [ ] Configurar nginx como reverse proxy (opcional)
- [ ] Firewall: abrir puerto del servicio solo a IPs autorizadas

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| XPaths frágiles (portal actualiza DOM) | Centralizar todos en page objects, fácil actualización |
| Timeout sesión < 5 min real | Heartbeat a 240s; validar contra portal en Fase 5 |
| RFC devuelve N pólizas, tabla paginada | Verificar si hay paginación; iterar o cargar todo antes de procesar |
| Screenshot incompleto (lazy loading) | Scroll to bottom + wait networkidle antes de capturar |
| Respuesta lenta cliente (30-120s+) | Documentar timeout mínimo recomendado: 300s |
| URL injection no funciona (nota en proceso.md) | Confirmado: navegar solo por clicks, nunca por URL directa a póliza |
| Segundo request mientras procesa | Devolver 409, cliente reintenta; no hacer cola para evitar complejidad |

---

## Notas de implementación

- **No usar URL directa a póliza**: el portal no responde a inyección de URL (`consultadorInformacionGeneral/{id}/false`). Navegar siempre por clicks.
- **Playwright async**: usar `async_playwright` — FastAPI es async, evitar mezclar sync/async.
- **Heartbeat pausado durante PROCESSING**: evitar interferencia con la navegación activa.
- **PDF en v1**: `StoragePort.generar_pdf()` usa Pillow (`Image.save(..., save_all=True)`). No requiere paquete adicional. Se genera por póliza tras capturar todas sus pestañas.
