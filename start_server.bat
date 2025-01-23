@echo off
echo === Iniciando o Servidor RedHot ===
cd /d "%~dp0"
set "PYTHON_PATH=C:\Users\allef\AppData\Local\Programs\Python\Python313\python.exe"

echo Iniciando servidor...
"%PYTHON_PATH%" serve.py
echo === Iniciando Cloudflare Tunnel ===
start cmd /k "cloudflared.exe tunnel run redhot"
echo === Servidor iniciado! ===
echo Para acessar, aguarde alguns segundos e abra: https://redhot.net.br
pause 