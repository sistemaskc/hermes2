# RPA Consultador MetLife

RPA que mantiene sesión activa en el portal MetLife (`https://providaweb.metlife.mx/`), recibe peticiones HTTP, ejecuta búsquedas por RFC o número de póliza, captura screenshots por pestaña y devuelve rutas de archivos generados.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Chromium (se instala vía Playwright)

## Setup

```bash
# 1. Clonar repo
git clone <repo-url>
cd RPA_Consultador

# 2. Instalar dependencias
uv sync

# 3. Instalar browser
uv run playwright install chromium

# 4. Configurar credenciales
cp .env.example .env
# Editar .env con usuario y password de MetLife
```

### Variables de entorno (`.env`)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `METLIFE_USUARIO` | Usuario del portal MetLife | — |
| `METLIFE_PASSWORD` | Password del portal MetLife | — |
| `HEADLESS` | `false` = browser visible (requerido si hay OTP). `true` = headless | `false` |
| `OTP_TIMEOUT_SEGUNDOS` | Tiempo de espera para completar OTP manualmente | `900` |
| `OUTPUT_DIR` | Directorio donde se guardan screenshots y PDFs | `./output` |
| `HOST` | Host donde escucha el servidor | `0.0.0.0` |
| `PORT` | Puerto del servidor | `8000` |
| `HEARTBEAT_INTERVAL_SECONDS` | Intervalo de heartbeat para mantener sesión viva | `240` |
| `MAX_REINTENTOS_LOGIN` | Intentos de re-login automático ante sesión expirada | `3` |
| `LOG_LEVEL` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

## Arranque

```bash
uv run python main.py
```

O usando el script incluido:

```bash
iniciar.bat
```

Al arrancar, el servicio ejecuta login en el portal MetLife. Si el portal requiere OTP, completarlo manualmente en el browser abierto. El servidor queda listo cuando el log muestra `SessionManager arrancado`.

## Uso

Ver [API_CONTRACT.md](API_CONTRACT.md) para el contrato completo.

```bash
# Verificar estado
curl http://localhost:8000/health

# Consultar por RFC, todas las pestañas (tipo se infiere por longitud ≥10)
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"identificador": "XXXXXXXXXXXXX", "pestanas": ["todo"], "numero_telefono": "5512345678"}' \
  --max-time 300

# Consultar por póliza, todas las pestañas (tipo se infiere por longitud 6)
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"identificador": "XXXXXX", "pestanas": ["todo"], "numero_telefono": "5512345678"}' \
  --max-time 300

# Consultar por póliza, pestañas específicas
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"identificador": "XXXXXX", "pestanas": ["general", "beneficiarios"], "numero_telefono": "5512345678"}' \
  --max-time 300
```

**Pestañas disponibles (`pestanas`):**

| Valor | Descripción |
|-------|-------------|
| `"general"` | Información general |
| `"coberturas"` | Coberturas |
| `"beneficiarios"` | Beneficiarios |
| `"servicios"` | Servicios |
| `"agentes"` | Agentes |
| `"todo"` | Expande a las 5 anteriores en orden |

```bash
# Preview PDF en iframe (default: inline)
GET http://localhost:8000/archivo?path=output\RLF150\RLF150_5512345678.pdf

# Forzar descarga
GET http://localhost:8000/archivo?path=output\RLF150\RLF150_5512345678.pdf&disposition=attachment
```

```html
<!-- Embeber PDF en frontend -->
<iframe src="http://localhost:8000/archivo?path=output\RLF150\RLF150_5512345678.pdf" />
```

El cliente HTTP debe configurar **timeout mínimo de 300s** para `/consultar`. Un RFC con múltiples pólizas puede tardar más.

## Archivos generados

```
output/
└── {identificador}/
    ├── {num_poliza}_general.png
    ├── {num_poliza}_coberturas.png
    ├── ...
    └── {num_poliza}_{telefono}.pdf
```

Las imágenes se guardan en escala de grises. Se genera un PDF por póliza con todas las pestañas capturadas en orden.

## Deploy en Azure VM

```bash
# Instalar uv en la VM
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clonar e instalar
git clone <repo-url>
cd RPA_Consultador
uv sync
uv run playwright install chromium --with-deps

# Configurar .env
cp .env.example .env
# Editar con credenciales y HEADLESS=false para el primer login con OTP

# Arrancar (primera vez: browser visible para OTP)
uv run python main.py
```

> **Nota:** Si el portal requiere OTP en cada sesión, mantener `HEADLESS=false` y acceso de escritorio remoto para completarlo manualmente al arrancar.

## Tests

```bash
uv run pytest
uv run pytest tests/test_local_storage.py -v
```

## Arquitectura

Hexagonal (Ports & Adapters). Ver [PLAN.md](PLAN.md) para detalle.

```
src/
├── domain/          ← entidades, value objects, ports (ABC), excepciones
├── application/     ← use cases, session manager
└── adapters/
    ├── inbound/     ← FastAPI router + schemas Pydantic
    └── outbound/    ← PlaywrightConsultadorAdapter, LocalStorageAdapter
                        pages/ → LoginPage, SearchPage, ResultsPage, PolicyPage
```

| Documento | Contenido |
|-----------|-----------|
| [API_CONTRACT.md](API_CONTRACT.md) | Contrato HTTP completo con ejemplos |
| [Proceso.md](Proceso.md) | Flujo oficial del proceso con XPaths |
| [PLAN.md](PLAN.md) | Arquitectura detallada |
| [Diagrama_Proceso.md](Diagrama_Proceso.md) | Flowchart del proceso |
| [Diagrama_Secuencia.md](Diagrama_Secuencia.md) | Diagrama de secuencia |
