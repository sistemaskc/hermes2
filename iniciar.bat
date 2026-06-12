@echo off
title Hermes KC
cd /d "%~dp0"

echo ============================================================
echo  Hermes KC
echo  %DATE% %TIME%
echo ============================================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv no encontrado en PATH.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] Archivo .env no encontrado.
    pause
    exit /b 1
)

findstr /i "tu_usuario" .env >nul 2>&1
if not errorlevel 1 (
    echo [ERROR] METLIFE_USUARIO sigue siendo "tu_usuario". Configurar .env.
    pause
    exit /b 1
)

findstr /i "tu_password" .env >nul 2>&1
if not errorlevel 1 (
    echo [ERROR] METLIFE_PASSWORD sigue siendo "tu_password". Configurar .env.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [INFO] Entorno virtual no encontrado. Ejecutando uv sync...
    uv sync
    if errorlevel 1 (
        echo [ERROR] uv sync fallo.
        pause
        exit /b 1
    )
    echo.
)

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /i "^PORT=" .env 2^>nul`) do set PORT=%%B
if "%PORT%"=="" set PORT=8000

netstat -ano > "%TEMP%\netstat_out.txt" 2>nul
findstr ":%PORT% " "%TEMP%\netstat_out.txt" | findstr "LISTENING" > "%TEMP%\puerto_activo.txt" 2>nul
for /f "tokens=5" %%a in (%TEMP%\puerto_activo.txt) do taskkill /PID %%a /F >nul 2>&1
del "%TEMP%\netstat_out.txt" >nul 2>&1
del "%TEMP%\puerto_activo.txt" >nul 2>&1

echo [INFO] Iniciando servidor en http://localhost:%PORT%
echo.

uv run python main.py

echo.
echo [INFO] Servidor detenido.
pause
