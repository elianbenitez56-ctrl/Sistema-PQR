@echo off
title SISTEMA PQR - INAPEL

cd /d "%~dp0"

echo ======================================
echo      INICIANDO SISTEMA PQR...
echo ======================================

set PYTHON=C:\Users\Administrador\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe

if not exist "%PYTHON%" (
    echo ERROR: No se encuentra Python.
    echo Instale Python desde python.org o ajuste la ruta en INICIAR_PQR.bat
    pause
    exit /b 1
)

start "" cmd /k "%PYTHON% app.py"

timeout /t 3 /nobreak >nul

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" http://127.0.0.1:5000

exit