@echo off
cd /d "%~dp0"

echo === GET /health ===
curl -s http://localhost:8000/health
echo.
echo.

echo === POST /consultar (poliza) ===
curl -s -X POST http://localhost:8000/consultar ^
  -H "Content-Type: application/json" ^
  -d "{\"identificador\": \"%POLIZA_PRUEBA%\", \"tipo\": \"POLIZA\", \"pestanas\": [\"todo\"]}"
echo.

pause
