@echo off
chcp 65001 > nul
title RED HOT - Painel de Controle
color 0A

setlocal EnableDelayedExpansion

:: Configurações
set "PYTHON_CMD=C:\Users\allef\AppData\Local\Programs\Python\Python313\python.exe"
set "WORKSPACE=C:\Users\allef\Desktop\redsite"
set "BACKUP_DIR=C:\Users\allef\Desktop\redsite\backups"
set "NGROK_PATH=C:\Users\allef\Desktop\redsite\ngrok.exe"
set "FLASK_PORT=5000"

:: Configurações do GitHub
set "GITHUB_USER=redhotsite"
set "GITHUB_EMAIL=redhotsistemas@gmail.com"
set "GITHUB_REPO=https://github.com/redhotsite/redsite"
set "CONFIG_FILE=%WORKSPACE%\github_config.json"

:: Configurações
set "PORTA_FLASK=5000"
set "PORTA_NGROK=4040"
set "TENTATIVAS_MAXIMAS=10"
set "PORTA_ALTERNATIVA=5001"

:inicio
cls
echo ========================================================
echo           RED HOT - Sistema de Gerenciamento
echo ========================================================
echo.

:: Verifica ambiente
call :check_environment
if !ERRORLEVEL! neq 0 goto :eof

:menu
cls
echo ========================================================
echo                    MENU PRINCIPAL
echo ========================================================
echo.
echo Python: %PYTHON_VERSION%
if exist "%NGROK_PATH%" (
    echo ngrok: Instalado
) else (
    color 0C
    echo ngrok: Não encontrado
    color 0A
)
echo.
echo [1] Iniciar Servidor + ngrok
echo [2] Iniciar Servidor Local
echo [3] Fazer Backup Local
echo [4] Fazer Backup GitHub
echo [5] Reiniciar Servidor
echo [6] Sair
echo.
echo ========================================================

set /p "opcao=Escolha uma opção (1-6): "

if "%opcao%"=="1" goto start_with_ngrok
if "%opcao%"=="2" goto start_local
if "%opcao%"=="3" goto backup_local
if "%opcao%"=="4" goto backup_github
if "%opcao%"=="5" goto restart_server
if "%opcao%"=="6" goto exit_script
color 0C
echo Opção inválida!
color 0A
pause
goto menu

:check_environment
echo Verificando ambiente...
echo [1/4] Verificando Python...
if not exist "%PYTHON_CMD%" (
    color 0C
    echo Erro: Python não encontrado em: %PYTHON_CMD%
    echo Instale o Python 3.13 de https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('"%PYTHON_CMD%" --version 2^>^&1') do set "PYTHON_VERSION=%%v"
echo ✓ Python encontrado: %PYTHON_VERSION%

echo [2/4] Verificando dependências...
"%PYTHON_CMD%" -c "import flask" 2>nul
if %ERRORLEVEL% neq 0 (
    color 0E
    echo Instalando dependências...
    cd /d "%WORKSPACE%"
    "%PYTHON_CMD%" -m pip install -r requirements.txt
    if !ERRORLEVEL! neq 0 (
        color 0C
        echo Erro ao instalar dependências!
        pause
        exit /b 1
    )
    color 0A
)
echo ✓ Dependências OK

echo [3/4] Verificando diretório de trabalho...
if not exist "%WORKSPACE%" (
    color 0C
    echo Erro: Diretório %WORKSPACE% não encontrado!
    pause
    exit /b 1
)
echo ✓ Diretório OK

echo [4/4] Verificando diretório de backup...
if not exist "%BACKUP_DIR%" (
    color 0E
    echo Criando diretório de backup...
    mkdir "%BACKUP_DIR%"
    color 0A
) else (
    echo ✓ Diretório de backup encontrado
)

echo.
echo Ambiente verificado com sucesso!
timeout /t 2 /nobreak >nul
exit /b 0

:find_available_port
:: Tenta portas entre 5000 e 5020
set "FLASK_PORT=5000"
:check_next_port
netstat -ano | find ":%FLASK_PORT%" >nul
if %ERRORLEVEL% equ 0 (
    set /a FLASK_PORT+=1
    if %FLASK_PORT% leq 5020 goto check_next_port
    color 0C
    echo Erro: Nenhuma porta disponível entre 5000 e 5020!
    pause
    color 0A
    exit /b 1
)
exit /b 0

:start_with_ngrok
cls
echo ========================================================
echo         Iniciando Servidor com Acesso Externo
echo ========================================================
echo.

:: 1. Mata processos existentes
echo [1/3] Limpando processos...
taskkill /F /FI "WINDOWTITLE eq Flask Server" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Ngrok Tunnel" >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
taskkill /F /IM ngrok.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo ✓ Processos limpos

:: 2. Inicia o servidor Flask
echo.
echo [2/3] Iniciando servidor Flask...
cd /d "%WORKSPACE%"
start "Flask Server" cmd /c "%PYTHON_CMD% app.py"
echo Aguardando servidor iniciar...
timeout /t 5 /nobreak >nul

:: 3. Inicia o ngrok
echo.
echo [3/3] Iniciando ngrok...
start "Ngrok Tunnel" cmd /c "cd /d %WORKSPACE% && ngrok.exe http 5000"
echo Aguardando ngrok iniciar...
timeout /t 3 /nobreak >nul

echo.
echo ========================================================
echo              Servidor Iniciado com Sucesso!
echo ========================================================
echo.
echo Acessos:
echo - Local: http://localhost:5000
echo - Dashboard ngrok: http://localhost:4040
echo.
echo Para encerrar o servidor:
echo 1. Pressione qualquer tecla
echo 2. Aguarde a confirmação de encerramento
echo.
pause >nul

echo.
echo Encerrando servidor...
taskkill /F /FI "WINDOWTITLE eq Flask Server" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Ngrok Tunnel" >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
taskkill /F /IM ngrok.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo ✓ Servidor encerrado com sucesso!
echo.
echo Pressione qualquer tecla para voltar ao menu...
pause >nul
goto menu

:start_local
cls
echo ========================================================
echo            Iniciando Servidor com Tunnel
echo ========================================================
echo.

:: Função de limpeza robusta
echo [1/5] Realizando limpeza profunda...

:: Mata todos os processos relacionados
echo - Encerrando processos Python...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 1 /nobreak > nul

echo - Encerrando processos Cloudflare...
taskkill /F /IM cloudflared.exe >nul 2>&1
timeout /t 1 /nobreak > nul

echo - Encerrando janelas de comando...
taskkill /F /FI "WINDOWTITLE eq Servidor RedHot" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Cloudflare Tunnel" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Python" >nul 2>&1
timeout /t 1 /nobreak > nul

:: Limpa o tunnel
echo [2/5] Limpando configurações do tunnel...
echo - Executando cleanup do tunnel...
cloudflared.exe tunnel cleanup ac6a98a6-6158-4ce4-928b-f5ffe6480f7e >nul 2>&1
timeout /t 1 /nobreak > nul

:: Verifica e tenta liberar a porta 8080
echo [3/5] Verificando porta 8080...
setlocal EnableDelayedExpansion
call :cleanup_port_8080
endlocal

:: Verifica ambiente
echo [4/5] Verificando ambiente...
echo - Verificando Python...
"%PYTHON_CMD%" --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo Erro: Python não encontrado em: %PYTHON_CMD%
    echo Verifique se o Python está instalado corretamente.
    pause
    color 0A
    goto menu
)

echo - Verificando Cloudflared...
cloudflared.exe version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo Erro: Cloudflared não encontrado!
    echo Verifique se o Cloudflared está instalado corretamente.
    pause
    color 0A
    goto menu
)

:: Inicia os serviços
echo [5/5] Iniciando serviços...
cd /d "%WORKSPACE%"

:: Inicia o servidor
echo - Iniciando servidor Waitress...
start "Servidor RedHot" cmd /k "cd /d %WORKSPACE% && %PYTHON_CMD% serve.py"

:: Aguarda e verifica o servidor
echo - Aguardando servidor iniciar...
timeout /t 5 /nobreak > nul

:: Tenta conectar ao servidor várias vezes
set "MAX_TRIES=10"
set "CURRENT_TRY=1"

:check_server
echo - Verificando servidor (tentativa %CURRENT_TRY% de %MAX_TRIES%)...
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8080 > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if "%STATUS%"=="200" (
    echo ✓ Servidor iniciado com sucesso!
    goto server_ready
) else (
    if %CURRENT_TRY% lss %MAX_TRIES% (
        set /a CURRENT_TRY+=1
        timeout /t 2 /nobreak > nul
        goto check_server
    ) else (
        color 0C
        echo.
        echo Erro: Servidor não respondeu após %MAX_TRIES% tentativas!
        echo.
        echo Verifique:
        echo 1. Se há erros na janela do servidor
        echo 2. Se todas as dependências estão instaladas
        echo 3. Se o arquivo serve.py existe e está correto
        echo.
        pause
        color 0A
        goto menu
    )
)

:server_ready
:: Inicia o tunnel
echo.
echo - Iniciando Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "cd /d %WORKSPACE% && cloudflared.exe tunnel --config=config.yml run ac6a98a6-6158-4ce4-928b-f5ffe6480f7e"

echo.
echo ========================================================
echo              Sistema Iniciado com Sucesso!
echo ========================================================
echo.
echo Acessos:
echo - Local: http://127.0.0.1:8080
echo - Externo: https://redhot.net.br
echo.
echo Aguarde alguns segundos para o tunnel estabelecer conexao...
timeout /t 10 /nobreak > nul

:: Verifica se o tunnel está funcionando
echo - Verificando conexão externa...
curl -s -o nul -w "%%{http_code}" https://redhot.net.br > temp_tunnel.txt
set /p TUNNEL_STATUS=<temp_tunnel.txt
del temp_tunnel.txt

if "%TUNNEL_STATUS%"=="200" (
    echo ✓ Tunnel funcionando!
) else (
    echo AVISO: Tunnel ainda não respondeu. Pode levar alguns segundos...
)

echo.
echo Para encerrar:
echo 1. Pressione qualquer tecla
echo 2. Aguarde a confirmação de encerramento
echo.
pause >nul

echo.
echo Encerrando sistema...
echo - Parando serviços...
setlocal EnableDelayedExpansion
call :cleanup_port_8080
endlocal

echo ✓ Sistema encerrado com sucesso!
echo.
echo Pressione qualquer tecla para voltar ao menu...
pause >nul
goto menu

:backup_local
cls
echo ========================================================
echo                 Criando Backup Local
echo ========================================================
echo.

:: Configurações
set "MAX_BACKUPS=5"
set "DB_FILE=users.db"
set "TIMESTAMP=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_NAME=redsite_%TIMESTAMP%"

echo [1/5] Verificando ambiente...
:: Verifica diretório de backup
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    echo ✓ Diretório de backup criado
) else (
    echo ✓ Diretório de backup encontrado
)

:: Verifica banco de dados
if not exist "%DB_FILE%" (
    color 0C
    echo ERRO: Banco de dados não encontrado!
    echo Verifique se o arquivo %DB_FILE% existe.
    pause
    color 0A
    goto menu
) else (
    echo ✓ Banco de dados encontrado
)

:: Verifica 7-Zip
if not exist "C:\Program Files\7-Zip\7z.exe" (
    color 0C
    echo ERRO: 7-Zip não encontrado!
    echo 1. Baixe o 7-Zip de https://7-zip.org/
    echo 2. Instale para todos os usuários
    echo 3. Tente novamente
    pause
    color 0A
    goto menu
) else (
    echo ✓ 7-Zip encontrado
)

echo.
echo [2/5] Preparando arquivos...
:: Cria arquivo .backupignore se não existir
if not exist ".backupignore" (
    (
        echo backups/
        echo __pycache__/
        echo *.pyc
        echo *.db
        echo *.log
        echo github_config.json
        echo .git/
        echo .gitignore
        echo .backupignore
    ) > .backupignore
    echo ✓ Arquivo .backupignore criado
) else (
    echo ✓ Arquivo .backupignore encontrado
)

echo.
echo [3/5] Criando backup do banco de dados...
copy "%DB_FILE%" "%BACKUP_DIR%\db_%BACKUP_NAME%.db" >nul
if %errorlevel% neq 0 (
    color 0C
    echo ERRO: Falha ao copiar banco de dados!
    pause
    color 0A
    goto menu
)
echo ✓ Banco de dados copiado

echo.
echo [4/5] Compactando arquivos do projeto...
cd /d "%WORKSPACE%"
"C:\Program Files\7-Zip\7z.exe" a -tzip "%BACKUP_DIR%\%BACKUP_NAME%.zip" * -x@.backupignore
if %errorlevel% neq 0 (
    color 0C
    echo ERRO: Falha ao compactar arquivos!
    pause
    color 0A
    goto menu
)
echo ✓ Arquivos compactados

echo.
echo [5/5] Gerenciando backups antigos...
:: Remove backups antigos do banco de dados
for /f "skip=%MAX_BACKUPS% delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\db_redsite_*.db" 2^>nul') do (
    del "%BACKUP_DIR%\%%F"
    echo ✓ Backup antigo removido: %%F
)

:: Remove backups antigos dos arquivos
for /f "skip=%MAX_BACKUPS% delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\redsite_*.zip" 2^>nul') do (
    del "%BACKUP_DIR%\%%F"
    echo ✓ Backup antigo removido: %%F
)

echo.
echo ========================================================
echo                 Backup Concluído!
echo ========================================================
echo.
echo Arquivos criados:
echo - %BACKUP_DIR%\db_%BACKUP_NAME%.db
echo - %BACKUP_DIR%\%BACKUP_NAME%.zip
echo.
echo Pressione qualquer tecla para voltar ao menu...
pause >nul
goto menu

:backup_github
cls
echo ========================================================
echo               Backup GitHub
echo ========================================================
echo.

echo [1/7] Verificando configuração...
if not exist "%CONFIG_FILE%" (
    echo Arquivo de configuração não encontrado.
    echo Criando novo arquivo de configuração...
    echo.
    set /p "GITHUB_TOKEN=Digite o token do GitHub: "
    echo { "token": "%GITHUB_TOKEN%" }> "%CONFIG_FILE%"
    echo Token salvo em %CONFIG_FILE%
    echo.
)

for /f "usebackq tokens=2 delims=:, " %%a in (`type "%CONFIG_FILE%" ^| findstr "token"`) do (
    set "GITHUB_TOKEN=%%~a"
    set "GITHUB_TOKEN=!GITHUB_TOKEN:"=!"
)

echo [2/7] Verificando Git...
git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo Erro: Git não encontrado!
    echo Instale o Git de https://git-scm.com/downloads
    pause
    color 0A
    goto menu
)

echo [3/7] Configurando Git...
cd /d "%WORKSPACE%"
git config --global core.autocrlf true
git config --global user.name "%GITHUB_USER%"
git config --global user.email "%GITHUB_EMAIL%"

echo [4/7] Limpando repositório Git...
if exist ".git" (
    rmdir /s /q .git
)
git init
git branch -M main
git remote remove origin 2>nul
git remote add origin "https://github.com/redhotsite/redsite.git"
git remote set-url origin "https://%GITHUB_TOKEN%@github.com/redhotsite/redsite.git"

echo [5/7] Verificando arquivos ignorados...
if not exist ".gitignore" (
    echo Criando arquivo .gitignore...
    (
        echo # Arquivos de configuração com dados sensíveis
        echo github_config.json
        echo.
        echo # Arquivos de backup
        echo *.zip
        echo backups/
        echo.
        echo # Arquivos do Python
        echo __pycache__/
        echo *.py[cod]
        echo *$py.class
        echo.
        echo # Ambiente virtual
        echo venv/
        echo env/
        echo.
        echo # Banco de dados
        echo *.db
        echo *.sqlite3
        echo.
        echo # Logs
        echo *.log
        echo.
        echo # Arquivos do sistema
        echo .DS_Store
        echo Thumbs.db
    ) > .gitignore
)

echo [6/7] Preparando commit...
git add .
git commit -m "Backup automático - %date% %time%"

echo [7/7] Enviando para GitHub...
git push -f origin main
if %ERRORLEVEL% neq 0 (
    color 0C
    echo Erro ao enviar para GitHub!
    echo Tentando método alternativo...
    git push -f "https://%GITHUB_TOKEN%@github.com/redhotsite/redsite.git" main
    if !ERRORLEVEL! neq 0 (
        echo Erro ao enviar para GitHub!
        echo Verifique se o token está correto em %CONFIG_FILE%
        pause
        color 0A
        goto menu
    )
)

echo.
echo Backup enviado com sucesso para GitHub!
echo Repositório: %GITHUB_REPO%
echo.
pause
goto menu

:restart_server
cls
echo ========================================================
echo               Reiniciando Servidor
echo ========================================================
echo.

echo [1/4] Parando servidores...
taskkill /FI "WINDOWTITLE eq Flask Server" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Ngrok Tunnel" /F >nul 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] Verificando processos...
netstat -ano | find ":%FLASK_PORT%" >nul
if %ERRORLEVEL% equ 0 (
    color 0E
    echo Forçando liberação da porta %FLASK_PORT%...
    for /f "tokens=5" %%a in ('netstat -aon ^| find ":%FLASK_PORT%"') do taskkill /F /PID %%a >nul 2>nul
    color 0A
)

echo [3/4] Fazendo backup...
call :backup_local

echo [4/4] Reiniciando servidor...
call :start_server
if !ERRORLEVEL! neq 0 goto menu

echo.
echo Servidor reiniciado com sucesso!
echo.
pause
goto menu

:exit_script
cls
echo ========================================================
echo               Encerrando Sistema
echo ========================================================
echo.

echo [1/3] Parando servidores...
taskkill /FI "WINDOWTITLE eq Flask Server" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Ngrok Tunnel" /F >nul 2>nul
echo ✓ Servidores parados

echo [2/3] Fazendo backup final...
call :backup_local
echo ✓ Backup realizado

echo [3/3] Finalizando...
echo.
echo ========================================================
echo            Sistema Encerrado com Sucesso!
echo ========================================================
timeout /t 2 /nobreak >nul

:: Cria um arquivo temporário para fechar o CMD
echo @echo off > "%temp%\close.bat"
echo timeout /t 1 /nobreak >nul >> "%temp%\close.bat"
echo taskkill /F /PID !ERRORLEVEL! >> "%temp%\close.bat"
start /b "" cmd /c "%temp%\close.bat" & del "%temp%\close.bat"
endlocal
exit /b 0

:cleanup_port_8080
echo Procurando e fechando aplicativos na porta 8080...
:: Lista todos os processos usando a porta 8080
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8080" ^| find "LISTENING"') do (
    :: Obtém informações do processo
    for /f "tokens=1* delims=," %%b in ('tasklist /fi "PID eq %%a" /fo csv /nh') do (
        set "PROC_NAME=%%~b"
        echo Encontrado: !PROC_NAME! (PID: %%a^)
        :: Tenta matar o processo
        taskkill /F /PID %%a >nul 2>&1
        if !ERRORLEVEL! equ 0 (
            echo ✓ Processo terminado com sucesso
        ) else (
            echo - Tentando método alternativo...
            powershell -Command "Stop-Process -Id %%a -Force" >nul 2>&1
        )
    )
)

:: Verifica se ainda há processos
netstat -ano | find ":8080" >nul
if !ERRORLEVEL! equ 0 (
    :: Tenta métodos mais agressivos
    echo - Executando limpeza agressiva...
    :: Reset de rede
    netsh int ip reset >nul 2>&1
    netsh winsock reset >nul 2>&1
    ipconfig /flushdns >nul 2>&1
    :: Mata processos comuns que podem usar a porta
    taskkill /F /IM nginx.exe >nul 2>&1
    taskkill /F /IM httpd.exe >nul 2>&1
    taskkill /F /IM java.exe >nul 2>&1
    taskkill /F /IM node.exe >nul 2>&1
)

:: Verificação final
netstat -ano | find ":8080" >nul
if !ERRORLEVEL! equ 0 (
    echo AVISO: Porta 8080 ainda em uso. Pode ser necessário reiniciar o computador.
) else (
    echo ✓ Porta 8080 totalmente liberada
)
exit /b