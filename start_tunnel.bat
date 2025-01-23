@echo off
echo === Iniciando Cloudflare Tunnel ===
cd /d "%~dp0"
cloudflared.exe tunnel --config="config.yml" run ac6a98a6-6158-4ce4-928b-f5ffe6480f7e 