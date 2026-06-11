# Contrato de API — RPA Consultador MetLife

Base URL: `http://{host}:{port}`  
Versión: `v1`  
Content-Type: `application/json`

---

## Endpoints

### `POST /consultar`

Ejecuta búsqueda en portal MetLife y devuelve nombres de los PDFs generados.

**Notas:**
- Respuesta síncrona — cliente debe configurar timeout mínimo **300s**
- Un solo request activo a la vez (lock interno)
- RFC puede devolver múltiples pólizas — se procesan todas, un PDF por póliza
- Errores de negocio (no encontrado, portal caído, etc.) devuelven `200` con `success: false`

#### Request Body

```json
{
  "identificador": "XXXXXXXXXXXXX",
  "pestanas": ["general", "coberturas"],
  "numero_telefono": "5512345678"
}
```

| Campo | Tipo | Requerido | Default | Descripción |
|-------|------|-----------|---------|-------------|
| `identificador` | `string` | Sí | — | RFC (≥10 chars) o número de póliza (exactamente 6 chars). El tipo se infiere automáticamente por longitud. |
| `pestanas` | `array[string]` | No | `["todo"]` | Pestañas a capturar |
| `numero_telefono` | `string` | Sí | — | Teléfono a 10 dígitos. Se eliminan espacios, `+` y otros no-dígitos automáticamente. |

> **Inferencia de tipo:** longitud 6 → POLIZA; longitud ≥10 → RFC; cualquier otra longitud devuelve `422`.

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

#### Response `200 OK` — Éxito

```json
{
  "success": true,
  "successMessage": "",
  "errorMessage": "",
  "data": [
    { "file_name": "HMZ317_5512345678.pdf" },
    { "file_name": "MTP455_5512345678.pdf" }
  ]
}
```

#### Response `200 OK` — Error de negocio

Todos los errores de ejecución (no encontrado, portal caído, sesión expirada, etc.) devuelven HTTP 200 con `success: false`.

```json
{
  "success": false,
  "successMessage": "",
  "errorMessage": "No se encontraron pólizas para: XXXXXXXXXXXXXXX",
  "data": []
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | `boolean` | `true` si la consulta fue exitosa |
| `successMessage` | `string` | Mensaje informativo en caso de éxito (normalmente vacío) |
| `errorMessage` | `string` | Descripción del error cuando `success: false` |
| `data` | `array` | Lista de PDFs generados |
| `data[].file_name` | `string` | Nombre del archivo PDF: `{poliza}_{unix_timestamp}.pdf` |

**Escenarios de error comunes:**

| Escenario | `errorMessage` típico |
|-----------|----------------------|
| RFC/póliza sin resultados | `"No se encontraron pólizas para: {identificador}"` |
| Portal no disponible | `"No se encontró campo de búsqueda"` |
| Sesión expirada | `"Botón de ingreso no encontrado"` |
| Error de captura en pestaña | `"Error capturando {pestana} en póliza {numero}. {detalle}"` |

> **Archivos PDF:** guardados en `output/{poliza}_{unix_timestamp}.pdf` directamente en el directorio raíz de output (sin subcarpetas).  
> Las imágenes PNG intermedias se eliminan automáticamente tras generar el PDF.  
> Usar `GET /archivo?path=output/{file_name}` para descargar o previsualizar.

---

#### Response `422 Unprocessable Entity`

Error de validación Pydantic en el body. Ocurre si `identificador` tiene longitud inválida (7-9 chars), `numero_telefono` no tiene 10 dígitos, o `pestanas` contiene un valor no reconocido.

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, identificador con longitud 8 no es válido. Debe tener 6 caracteres (póliza) o 10+ caracteres (RFC).",
      "input": { "identificador": "ABCD1234" }
    }
  ]
}
```

---

### `GET /archivo`

Descarga un archivo PDF generado por `/consultar`.

#### Query Params

| Parámetro | Tipo | Requerido | Default | Descripción |
|-----------|------|-----------|---------|-------------|
| `path` | `string` | Sí | — | Ruta relativa al archivo, construida como `output/{file_name}` |
| `disposition` | `"inline"` \| `"attachment"` | No | `"inline"` | `inline` = previsualización en iframe; `attachment` = forzar descarga |

#### Ejemplos

```bash
# Preview en iframe (default)
GET /archivo?path=output\HMZ317_1747123456.pdf

# Forzar descarga
GET /archivo?path=output\HMZ317_1747123456.pdf&disposition=attachment
```

#### Response `200 OK`

Streaming del archivo con los siguientes headers:

| Header | Valor |
|--------|-------|
| `Content-Type` | `application/pdf` |
| `Content-Disposition` | `inline; filename="..."` o `attachment; filename="..."` según `disposition` |
| `X-Frame-Options` | `ALLOWALL` — permite embeber en `<iframe>` desde cualquier origen |

#### Response `403 Forbidden`

La ruta apunta fuera del directorio `output/`.

#### Response `404 Not Found`

El archivo no existe en el filesystem.

#### Response `422 Unprocessable Entity`

`disposition` tiene un valor distinto de `inline` o `attachment`.

---

### `GET /health`

Estado actual de la sesión.

#### Response `200 OK`

```json
{
  "estado": "ACTIVE",
  "version": "0.1.2"
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
  -d '{"identificador": "FOPS840824XXX", "pestanas": ["todo"], "numero_telefono": "5512345678"}' \
  --max-time 300
```

Respuesta (RFC con 2 pólizas):
```json
{
  "success": true,
  "successMessage": "",
  "errorMessage": "",
  "data": [
    { "file_name": "MTP455_5512345678.pdf" },
    { "file_name": "ELW404_5512345678.pdf" }
  ]
}
```

### Buscar por número de póliza, pestañas específicas

```bash
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"identificador": "HMZ317", "pestanas": ["general", "beneficiarios"], "numero_telefono": "5512345678"}' \
  --max-time 300
```

### Previsualizar PDF en iframe

```html
<iframe src="http://localhost:8000/archivo?path=output\HMZ317_1747123456.pdf" />
```

### Descargar PDF generado

```bash
curl "http://localhost:8000/archivo?path=output\HMZ317_1747123456.pdf&disposition=attachment" --output HMZ317.pdf
```

### Verificar estado del servicio

```bash
curl http://localhost:8000/health
```

---

## Flujo de integración típico

```
1. POST /consultar  →  { success: true, data: [{ file_name }] }
2. Construir path: output/{file_name}
3. GET  /archivo?path={path}                        →  preview PDF en iframe
4. GET  /archivo?path={path}&disposition=attachment →  forzar descarga PDF
```

## Notas de integración

- **CORS:** Habilitado con `allow_origins=["*"]` para desarrollo. En producción se restringirá a dominios específicos.
- **Timeout:** Configurar mínimo 300s en el cliente HTTP. RFC con múltiples pólizas puede tomar más tiempo.
- **Errores de negocio:** Siempre verificar `success` antes de usar `data`. Un `200` no garantiza éxito.
- **Imágenes PNG:** Temporales — se eliminan automáticamente tras generar el PDF. Solo los PDFs persisten.
- **Orden de capturas:** Con `"todo"`: general → coberturas → beneficiarios → servicios → agentes.
- **Nombre de archivo PDF:** Formato `{numero_poliza}_{unix_timestamp}.pdf`. El timestamp es Unix epoch en segundos.
