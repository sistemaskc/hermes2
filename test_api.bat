@echo off
title RPA Consultador - Test API
cd /d "%~dp0"

set HOST=https://hermes2.kc-itservices.net

if not "%~1"=="" (
    set IDENTIFICADOR=%~1
) else if not "%POLIZA_PRUEBA%"=="" (
    set IDENTIFICADOR=%POLIZA_PRUEBA%
) else (
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

if not "%TELEFONO_PRUEBA%"=="" (
    set TELEFONO=%TELEFONO_PRUEBA%
) else (
    for /f "usebackq tokens=1,* delims==" %%A in (`findstr /i "TELEFONO_PRUEBA" .env 2^>nul`) do set TELEFONO=%%B
)

if "%TELEFONO%"=="" (
    set /p TELEFONO="Ingresar numero de telefono (10 digitos): "
)
if "%TELEFONO%"=="" (
    echo [ERROR] Telefono requerido. Abortando.
    pause
    exit /b 1
)

where curl >nul 2>&1
if errorlevel 1 (
    echo [ERROR] curl no encontrado en PATH.
    pause
    exit /b 1
)

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
echo  Telefono:      %TELEFONO%
echo  %DATE% %TIME%
echo ============================================================
echo.

echo === GET /health ===
curl -s %HOST%/health
echo.
echo.

echo === POST /consultar ===
echo     Identificador: %IDENTIFICADOR%
echo     Telefono: %TELEFONO%
echo     (timeout 300s -- respuesta sincrona)
echo.
curl -s --max-time 300 -X POST %HOST%/consultar ^
  -H "Content-Type: application/json" ^
  -d "{\"identificador\": \"%IDENTIFICADOR%\", \"pestanas\": [\"todo\"], \"numero_telefono\": \"%TELEFONO%\"}"
echo.
echo.

echo ============================================================
echo  Fin de pruebas. %TIME%
echo ============================================================
pause