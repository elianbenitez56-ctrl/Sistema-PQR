@echo off
title SISTEMA PQR - INAPEL

cd /d "%~dp0"

echo ======================================
echo      INICIANDO SISTEMA PQR...
echo ======================================

start "" cmd /k python app.py

timeout /t 3 /nobreak >nul

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" http://127.0.0.1:5000

exit