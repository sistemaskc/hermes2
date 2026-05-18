# Diagrama de Secuencia RPA Consultador

```mermaid
sequenceDiagram
    actor ClienteAPI as Cliente API
    participant Server as API Server (FastAPI)
    participant Bot as RPA Bot (Playwright)
    participant Portal as Portal MetLife

    Note over Bot, Portal: Inicialización
    Bot->>Portal: Ingresar a https://providaweb.metlife.mx/
    Bot->>Portal: Hacer login y mantener sesión iniciada

    loop Heartbeat cada 240s (en idle)
        Bot->>Portal: Navegar a consultadorBusqueda/false
        Bot->>Portal: query_selector("#username") en DOM
        alt Sesión expirada (form SSO visible)
            Portal-->>Bot: #username presente en DOM
            Bot->>Portal: Re-login automático
            Portal-->>Bot: Login exitoso
        else Sesión activa
            Portal-->>Bot: #username ausente en DOM
            Note right of Bot: Sin acción, sesión OK
        end
    end

    loop Ciclo por Petición
        ClienteAPI->>Server: Petición HTTP (Póliza/RFC, Pestañas)
        Server->>Bot: Iniciar procesamiento de datos

        Bot->>Portal: Click en 'Ingresar Consultador'
        Bot->>Portal: Click en 'Ingresar'

        alt Búsqueda por Póliza
            Bot->>Portal: Ingresar número de póliza
        else Búsqueda por RFC
            Bot->>Portal: Ingresar RFC
        end

        Bot->>Portal: Click en 'Buscar'
        Portal-->>Bot: Muestra diálogo de confirmación
        Bot->>Portal: Click en botón Confirmar (OK)

        Portal-->>Bot: Muestra tabla de resultados
        Bot->>Portal: Click en el número de póliza

        opt Sesión expirada mid-request
            Note over Bot,Portal: SesionExpiradaError detectada
            Bot->>Portal: Re-login automático
            Portal-->>Bot: Login exitoso
            Note over Bot: Reintenta procesamiento completo
        end

        loop Por cada pestaña solicitada
            Bot->>Portal: Click en la pestaña correspondiente (xpath)
            Note right of Bot: general, coberturas, beneficiarios, etc.
            Bot->>Portal: Obtener Screenshot
            Portal-->>Bot: Imagen de los datos
            Bot->>Bot: Guardar imagen en escala de grises
        end

        Bot->>Bot: Generar PDF con img2pdf, eliminar PNGs

        Bot->>Portal: Regresar a consultadorBusqueda/false

        Bot-->>Server: Finaliza procesamiento
        Server-->>ClienteAPI: success:true + file_name del PDF
    end
```
