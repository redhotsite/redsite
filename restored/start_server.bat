@echo off
chcp 65001 > nul
title RED HOT - Servidor

setlocal EnableDelayedExpansion

:: Define cores para mensagens
set "GREEN=[32m"
set "RED=[31m"
set "YELLOW=[33m"
set "RESET=[0m"

:: Configurações
set "PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
set "FLASK_PORT=5000"

echo.
echo %GREEN%========================================================%RESET%
echo %GREEN%               RED HOT - Inicializando...%RESET%
echo %GREEN%========================================================%RESET%
echo.

:: Verifica se o Python existe no caminho especificado
if not exist "%PYTHON_CMD%" (
    echo %RED%Python não encontrado em: %PYTHON_CMD%%RESET%
    echo.
    echo Para instalar o Python:
    echo 1. Acesse: https://www.python.org/downloads/
    echo 2. Baixe a versão mais recente
    echo 3. Durante a instalação, marque "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: Obtém a versão do Python
for /f "tokens=*" %%v in ('"%PYTHON_CMD%" --version 2^>^&1') do set "PYTHON_VERSION=%%v"
echo %GREEN%✓ %PYTHON_VERSION% encontrado%RESET%

:: Verifica dependências do Python
echo.
echo Verificando dependências...
"%PYTHON_CMD%" -c "import flask" 2>nul
if %ERRORLEVEL% neq 0 (
    echo %YELLOW%Instalando dependências...%RESET%
    "%PYTHON_CMD%" -m pip install -r requirements.txt
    if !ERRORLEVEL! neq 0 (
        echo %RED%Erro ao instalar dependências!%RESET%
        pause
        exit /b 1
    )
)
echo %GREEN%✓ Dependências OK%RESET%

:: Verifica ngrok
set "NGROK_CMD="
if exist "ngrok.exe" (
    set "NGROK_CMD=ngrok.exe"
    echo %GREEN%✓ ngrok encontrado%RESET%
) else (
    echo %YELLOW%! ngrok não encontrado. Acesso externo não estará disponível%RESET%
    echo Para instalar ngrok:
    echo 1. Acesse: https://ngrok.com/download
    echo 2. Baixe e extraia ngrok.exe para esta pasta
)

echo.
echo %GREEN%========================================================%RESET%
echo %GREEN%            Iniciando Servidor...%RESET%
echo %GREEN%========================================================%RESET%
echo.

:: Verifica se a porta já está em uso
netstat -ano | find ":%FLASK_PORT%" >nul
if %ERRORLEVEL% equ 0 (
    echo %RED%Erro: Porta %FLASK_PORT% já está em uso!%RESET%
    echo Verifique se o servidor já está rodando.
    pause
    exit /b 1
)

:: Inicia o servidor Flask em uma nova janela
echo [1/3] Iniciando servidor Flask...
start "Flask Server" cmd /k "title Flask Server && cd /d %~dp0 && "%PYTHON_CMD%" app.py"
timeout /t 2 /nobreak >nul

:: Verifica se iniciou corretamente
timeout /t 3 /nobreak >nul
netstat -ano | find ":%FLASK_PORT%" >nul
if %ERRORLEVEL% neq 0 (
    echo %RED%Erro: Falha ao iniciar o servidor!%RESET%
    pause
    exit /b 1
)
echo %GREEN%✓ Servidor Flask iniciado%RESET%

:: Se o ngrok estiver disponível, inicia ele também
if defined NGROK_CMD (
    echo.
    echo [2/3] Iniciando túnel ngrok...
    start "Ngrok Tunnel" cmd /k "title Ngrok Tunnel && cd /d %~dp0 && %NGROK_CMD% http %FLASK_PORT%"
    timeout /t 3 /nobreak >nul
    
    echo.
    echo [3/3] Abrindo dashboard ngrok...
    start http://localhost:4040
    timeout /t 2 /nobreak >nul
    
    echo %GREEN%✓ Túnel ngrok iniciado%RESET%
    echo.
    echo Acesse:
    echo Local: %GREEN%http://localhost:%FLASK_PORT%%RESET%
    echo Externo: %GREEN%http://localhost:4040%RESET% (Dashboard ngrok)
) else (
    echo.
    echo Acesse: %GREEN%http://localhost:%FLASK_PORT%%RESET%
)

echo.
echo %GREEN%========================================================%RESET%
echo %GREEN%               Servidor Iniciado!%RESET%
echo %GREEN%========================================================%RESET%
echo.
echo Para parar os servidores:
echo 1. Feche esta janela
echo 2. As janelas dos servidores serão fechadas automaticamente
echo.
echo Pressione CTRL+C ou feche esta janela para encerrar...

:: Aguarda o usuário encerrar
:wait_exit
timeout /t 2 /nobreak >nul
tasklist /FI "WINDOWTITLE eq Flask Server" | find "cmd.exe" >nul
if %ERRORLEVEL% neq 0 goto server_stopped
goto wait_exit

:server_stopped
echo.
echo %GREEN%Encerrando servidores...%RESET%
taskkill /FI "WINDOWTITLE eq Flask Server" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Ngrok Tunnel" /F >nul 2>nul
echo %GREEN%✓ Servidores encerrados%RESET%
echo.
pause 