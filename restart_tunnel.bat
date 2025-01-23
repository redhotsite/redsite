@echo off
echo === Reiniciando Cloudflare Tunnel ===
cd /d "%~dp0"

echo [1/3] Parando tunnel atual...
taskkill /F /FI "WINDOWTITLE eq Cloudflare Tunnel" >nul 2>&1
taskkill /F /IM cloudflared.exe >nul 2>&1
timeout /t 2 /nobreak > nul

echo [2/3] Limpando configurações...
cloudflared.exe tunnel cleanup ac6a98a6-6158-4ce4-928b-f5ffe6480f7e

echo [3/3] Iniciando tunnel...
start "Cloudflare Tunnel" cmd /k "cloudflared.exe tunnel --config=config.yml run ac6a98a6-6158-4ce4-928b-f5ffe6480f7e"

echo.
echo === Tunnel Reiniciado! ===
echo Aguarde alguns segundos e tente acessar:
echo https://redhot.net.br
echo.
pause 