# Contrato de API — RPA Consultador MetLife

Base URL: `http://{host}:{port}`  
Versión: `v1`  
Content-Type: `application/json`

---

## Endpoints

### `POST /consultar`

Ejecuta búsqueda en portal MetLife y devuelve rutas de screenshots capturados.

**Notas:**
- Respuesta síncrona — cliente debe configurar timeout mínimo **300s**
- Un solo request activo a la vez (lock interno)
- RFC puede devolver múltiples pólizas — se procesan todas

#### Request Body

```json
{
  "identificador": "XXXXXXXXXXXXX",
  "tipo": "RFC",
  "pestanas": ["general", "coberturas"],
  "numero_telefono": "5512345678"
}
```

| Campo | Tipo | Requerido | Default | Descripción |
|-------|------|-----------|---------|-------------|
| `identificador` | `string` | Sí | — | RFC o número de póliza |
| `tipo` | `"RFC"` \| `"POLIZA"` | No | `"POLIZA"` | Tipo de búsqueda |
| `pestanas` | `array[string]` | No | `["todo"]` | Pestañas a capturar |
| `numero_telefono` | `string` | Sí | — | Teléfono a 10 dígitos. Se eliminan espacios, `+` y otros no-dígitos automáticamente. |

**Valores válidos de `pestanas`:**

| Valor | Descripción |
|-------|-------------|
| `"general"` | Información general |
| `"coberturas"` | Coberturas |
| `"beneficiarios"` | Beneficiarios |
| `"servicios"` | Servicios |
| `"agentes"` | Agentes |
| `"todo"` | Expande a las 5 pestañas anteriores en orden |

---

#### Response `200 OK`

```json
{
  "polizas": [
    {
      "numero": "<poliza>",
      "capturas": [
        {
          "pestana": "general",
          "ruta_archivo": "output\\<RFC>\\<poliza>_general.png"
        },
        {
          "pestana": "coberturas",
          "ruta_archivo": "output\\<RFC>\\<poliza>_coberturas.png"
        }
      ],
      "ruta_pdf": "output\\<RFC>\\<poliza>_<telefono>.pdf"
    }
  ]
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `polizas` | `array` | Lista de pólizas encontradas |
| `polizas[].numero` | `string` | Número de póliza |
| `polizas[].capturas` | `array` | Screenshots por pestaña |
| `polizas[].capturas[].pestana` | `string` | Nombre de la pestaña capturada |
| `polizas[].capturas[].ruta_archivo` | `string` | Ruta relativa al PNG (escala de grises) |
| `polizas[].ruta_pdf` | `string` | Ruta relativa al PDF generado para esa póliza |

> Las rutas son relativas al filesystem donde corre el servicio. Estructura: `output/{identificador}/{numero_poliza}_{pestana}.png`

---

#### Response `409 Conflict`

Otro request en proceso. Reintentar en unos segundos.

```json
{
  "detail": "Consulta en proceso. Reintentar en unos segundos."
}
```

---

#### Response `404 Not Found`

La póliza o RFC no arrojó resultados.

```json
{
  "detail": "No se encontraron pólizas para el identificador proporcionado."
}
```

---

#### Response `422 Unprocessable Entity`

Error de validación Pydantic en el body (formato estándar FastAPI).

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "pestanas", 0],
      "msg": "Input should be 'general', 'coberturas', 'beneficiarios', 'servicios', 'agentes' or 'todo'",
      "input": "INVALIDA"
    }
  ]
}
```

---

#### Response `500 Internal Server Error`

Error inesperado durante ejecución del RPA.

```json
{
  "detail": "mensaje de error interno"
}
```

---

### `GET /health`

Estado actual de la sesión.

#### Response `200 OK`

```json
{
  "estado": "ACTIVE"
}
```

| `estado` | Significado |
|----------|-------------|
| `INITIALIZING` | Arrancando, ejecutando login inicial |
| `ACTIVE` | Listo para recibir requests |
| `PROCESSING` | Procesando request activo |
| `HEARTBEATING` | Ejecutando heartbeat de sesión |
| `REINITIALIZING` | Re-login en curso tras sesión expirada |
| `ERROR` | Re-login falló — servicio degradado |

---

## Ejemplos de uso

### Buscar por RFC, todas las pestañas

```bash
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"identificador": "XXXXXXXXXXXXX", "tipo": "RFC", "pestanas": ["todo"], "numero_telefono": "5512345678"}' \
  --max-time 300
```

### Buscar por número de póliza, pestañas específicas

```bash
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"identificador": "XXXXXX", "tipo": "POLIZA", "pestanas": ["general", "beneficiarios"], "numero_telefono": "5512345678"}' \
  --max-time 300
```

### Verificar estado del servicio

```bash
curl http://localhost:8000/health
```

---

## Notas de integración

- **Timeout:** Configurar mínimo 300s en el cliente HTTP. RFC con múltiples pólizas puede tomar más tiempo.
- **Reintentos en 409:** Esperar mínimo 5s antes de reintentar.
- **Rutas devueltas:** Relativas al filesystem de la VM donde corre el servicio. Acceder vía red compartida o transferencia explícita.
- **Imágenes:** PNGs en escala de grises (modo L).
- **Orden de capturas:** Respeta el orden de `pestanas[]`. Con `"todo"`: general → coberturas → beneficiarios → servicios → agentes.
