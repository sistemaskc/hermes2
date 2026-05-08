@echo off
title RPA Consultador MetLife
cd /d "%~dp0"

echo ============================================================
echo  RPA Consultador MetLife
echo  %DATE% %TIME%
echo ============================================================
echo.

:: Verificar uv disponible
where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv no encontrado en PATH.
    echo         Instalar: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

:: Verificar .env existe
if not exist ".env" (
    echo [ERROR] Archivo .env no encontrado.
    echo         Copiar .env.example a .env y configurar credenciales.
    pause
    exit /b 1
)

:: Verificar credenciales no son valores por defecto
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

:: Verificar dependencias sincronizadas
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

echo [OK] Verificaciones completadas.
echo [INFO] Iniciando servidor...
echo [INFO] API disponible en http://localhost:8000
echo [INFO] Docs en http://localhost:8000/docs
echo [INFO] Ctrl+C para detener.
echo.

uv run python main.py

echo.
echo [INFO] Servidor detenido.
pause
