@echo off
echo === Iniciando RedHot com Cloudflare Tunnel ===
cd /d "%~dp0"

:: Define o caminho do Python
set "PYTHON_PATH=C:\Users\allef\AppData\Local\Programs\Python\Python313\python.exe"

:: Mata processos existentes
echo [1/4] Limpando processos anteriores...
taskkill /F /FI "WINDOWTITLE eq Servidor RedHot" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Cloudflare Tunnel" >nul 2>&1
taskkill /F /IM cloudflared.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak > nul

:: Limpa o tunnel
echo [2/4] Limpando tunnel...
cloudflared.exe tunnel cleanup ac6a98a6-6158-4ce4-928b-f5ffe6480f7e >nul 2>&1

:: Inicia o servidor em uma nova janela
echo [3/4] Iniciando servidor...
start "Servidor RedHot" cmd /k "%PYTHON_PATH% serve.py"

:: Aguarda o servidor iniciar
echo Aguardando servidor iniciar...
timeout /t 5 /nobreak > nul

:: Verifica se o servidor está rodando
powershell -Command "try { $response = Invoke-WebRequest -Uri http://127.0.0.1:8080 -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host 'Servidor iniciado com sucesso!' -ForegroundColor Green } } catch { Write-Host 'ERRO: Servidor nao respondeu!' -ForegroundColor Red; exit 1 }"
if %ERRORLEVEL% neq 0 (
    echo Erro ao iniciar o servidor! Verifique se a porta 8080 esta disponivel.
    pause
    exit /b 1
)

:: Inicia o tunnel
echo [4/4] Iniciando Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "cloudflared.exe tunnel --config=config.yml run ac6a98a6-6158-4ce4-928b-f5ffe6480f7e"

echo.
echo === Sistema Iniciado! ===
echo Local: http://127.0.0.1:8080
echo Externo: https://redhot.net.br
echo.
echo Aguarde alguns segundos para o tunnel estabelecer conexao...
timeout /t 10 /nobreak > nul

:: Verifica se o tunnel está funcionando
powershell -Command "try { $response = Invoke-WebRequest -Uri https://redhot.net.br -UseBasicParsing; if ($response.StatusCode -eq 200) { Write-Host 'Tunnel funcionando!' -ForegroundColor Green } } catch { Write-Host 'AVISO: Tunnel ainda nao respondeu. Pode levar alguns segundos...' -ForegroundColor Yellow }"

echo.
echo Para encerrar, feche esta janela e as outras duas que foram abertas.
pause 