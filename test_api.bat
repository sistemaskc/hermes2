@echo off
title RPA Consultador - Test API
cd /d "%~dp0"

set HOST=http://localhost:8000

:: Aceptar identificador como argumento o usar POLIZA_PRUEBA del entorno
if not "%~1"=="" (
    set IDENTIFICADOR=%~1
) else if not "%POLIZA_PRUEBA%"=="" (
    set IDENTIFICADOR=%POLIZA_PRUEBA%
) else (
    :: Intentar leer POLIZA_PRUEBA del .env
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /i "POLIZA_PRUEBA" .env 2^>nul`) do set IDENTIFICADOR=%%B
)

if "%IDENTIFICADOR%"=="" (
    echo [WARN] No se definio identificador de prueba.
    echo        Uso: test_api.bat [RFC_O_POLIZA]
    echo        O configurar POLIZA_PRUEBA en .env
    set /p IDENTIFICADOR="Ingresar RFC o numero de poliza: "
)
if "%IDENTIFICADOR%"=="" (
    echo [ERROR] Identificador requerido. Abortando.
    pause
    exit /b 1
)

:: Verificar curl disponible
where curl >nul 2>&1
if errorlevel 1 (
    echo [ERROR] curl no encontrado en PATH.
    pause
    exit /b 1
)

:: Verificar servidor levantado
echo Verificando servidor en %HOST%...
curl -s --max-time 3 %HOST%/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Servidor no responde en %HOST%.
    echo         Ejecutar iniciar.bat primero.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Identificador: %IDENTIFICADOR%
echo  %DATE% %TIME%
echo ============================================================
echo.

echo === GET /health ===
curl -s %HOST%/health
echo.
echo.

echo === GET /status ===
curl -s %HOST%/status
echo.
echo.

echo === POST /consultar ===
echo     Identificador: %IDENTIFICADOR%
echo     (timeout 300s — respuesta sincrona)
echo.
curl -s --max-time 300 -X POST %HOST%/consultar ^
  -H "Content-Type: application/json" ^
  -d "{\"identificador\": \"%IDENTIFICADOR%\", \"pestanas\": [\"todo\"]}"
echo.
echo.

echo ============================================================
echo  Fin de pruebas. %TIME%
echo ============================================================
pause
