@echo off
chcp 65001 > nul
title RED HOT - Backup Automático
color 0A

:: Configurações
set "WORKSPACE=C:\Users\allef\Desktop\redsite"
set "BACKUP_DIR=C:\Users\allef\Desktop\redsite\backups"
set "DB_FILE=users.db"
set "MAX_BACKUPS=10"
set "BACKUP_INTERVAL=1800"
set "INTERVAL_MINUTES=30"
set "GITHUB_CONFIG=github_config.json"
set "CHANGELOG_FILE=changelog.txt"
set "REPO_URL=https://github.com/redhotsite/redsite.git"

:: Habilita expansão atrasada de variáveis
setlocal EnableDelayedExpansion

echo ========================================================
echo           RED HOT - Backup Automático
echo ========================================================
echo.
echo Configurações:
echo - Diretório: %WORKSPACE%
echo - Backups: %BACKUP_DIR%
echo - Intervalo: %INTERVAL_MINUTES% minutos
echo - Máximo de backups: %MAX_BACKUPS%
echo.
echo Pressione CTRL+C para encerrar
echo.
echo ========================================================

:check_7zip
if not exist "C:\Program Files\7-Zip\7z.exe" (
    color 0C
    echo ERRO: 7-Zip não encontrado!
    echo 1. Baixe o 7-Zip de https://7-zip.org/
    echo 2. Instale para todos os usuários
    echo 3. Execute este script novamente
    pause
    exit
)

:check_git
echo.
echo [1/5] Verificando Git...
git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo ERRO: Git não encontrado!
    echo Para habilitar backup no GitHub:
    echo 1. Baixe o Git de https://git-scm.com/
    echo 2. Instale e reinicie este script
    pause
    exit
)
echo ✓ Git encontrado

:: Verifica e cria diretório de backup
echo.
echo [2/5] Verificando diretório de backup...
if not exist "%BACKUP_DIR%" (
    echo Criando diretório de backup...
    mkdir "%BACKUP_DIR%"
)
echo ✓ Diretório de backup pronto

:: Realiza backup local
echo.
echo [3/5] Realizando backup local...

:: 1. Backup do banco de dados
echo - Copiando banco de dados...
set "TIMESTAMP=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_NAME=redsite_%TIMESTAMP%"
set "DB_BACKUP=%BACKUP_DIR%\db_%BACKUP_NAME%.db"
set "ZIP_BACKUP=%BACKUP_DIR%\%BACKUP_NAME%.zip"

if exist "%WORKSPACE%\%DB_FILE%" (
    copy "%WORKSPACE%\%DB_FILE%" "%DB_BACKUP%" >nul 2>&1
    if %errorlevel% equ 0 (
        echo   ✓ Banco de dados copiado
        echo   📁 Salvo em: %DB_BACKUP%
    ) else (
        echo   × Falha ao copiar banco de dados
        echo   ⚠️ Erro: Não foi possível copiar %DB_FILE%
    )
) else (
    echo   ⚠️ Banco de dados não encontrado em: %WORKSPACE%\%DB_FILE%
)

:: 2. Backup dos arquivos
echo - Compactando arquivos...
cd /d "%WORKSPACE%"

:: Lista de arquivos a serem excluídos do backup
echo # Arquivos excluídos do backup: > "%TEMP%\exclude.txt"
echo backups\ >> "%TEMP%\exclude.txt"
echo __pycache__\ >> "%TEMP%\exclude.txt"
echo *.pyc >> "%TEMP%\exclude.txt"
echo *.db >> "%TEMP%\exclude.txt"
echo *.log >> "%TEMP%\exclude.txt"
echo github_config.json >> "%TEMP%\exclude.txt"
echo .git\ >> "%TEMP%\exclude.txt"
echo .gitignore >> "%TEMP%\exclude.txt"

:: Tenta usar 7-Zip para compactar
if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" a -tzip "%ZIP_BACKUP%" * -xr@"%TEMP%\exclude.txt" >nul 2>&1
    if %errorlevel% equ 0 (
        echo   ✓ Arquivos compactados com sucesso
        echo   📁 Salvo em: %ZIP_BACKUP%
        
        :: Mostra os arquivos incluídos no backup
        echo   📋 Arquivos incluídos no backup:
        "C:\Program Files\7-Zip\7z.exe" l "%ZIP_BACKUP%" | findstr /i /v "Path = Type = Physical Size = Headers = Code Page =" | findstr /v /c:"-------------------" /c:"Scanning" /c:"Creating archive" >nul
    ) else (
        echo   × Falha ao compactar arquivos
        echo   ⚠️ Erro durante a compactação
    )
) else (
    echo   × 7-Zip não encontrado
    echo   ⚠️ Instale o 7-Zip em: C:\Program Files\7-Zip\7z.exe
)

:: Remove arquivo temporário de exclusão
del "%TEMP%\exclude.txt" >nul 2>&1

:: 3. Limpeza de backups antigos
echo - Limpando backups antigos...
set "DELETED_COUNT=0"
for /f "skip=%MAX_BACKUPS% delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\db_redsite_*.db" 2^>nul') do (
    echo   🗑️ Removendo backup antigo: %%F
    del "%BACKUP_DIR%\%%F" >nul 2>&1
    set /a "DELETED_COUNT+=1"
)
for /f "skip=%MAX_BACKUPS% delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\redsite_*.zip" 2^>nul') do (
    echo   🗑️ Removendo backup antigo: %%F
    del "%BACKUP_DIR%\%%F" >nul 2>&1
    set /a "DELETED_COUNT+=1"
)
if !DELETED_COUNT! gtr 0 (
    echo   ✓ !DELETED_COUNT! backups antigos removidos
) else (
    echo   ✓ Nenhum backup antigo para remover
)

:: Mostra estatísticas do backup local
echo.
echo Estatísticas do backup local:
for /f %%A in ('dir /b /a-d "%BACKUP_DIR%\db_redsite_*.db" 2^>nul ^| find /c /v ""') do (
    echo - 💾 Backups do banco: %%A
    echo   📁 Último: %DB_BACKUP%
)
for /f %%A in ('dir /b /a-d "%BACKUP_DIR%\redsite_*.zip" 2^>nul ^| find /c /v ""') do (
    echo - 📦 Backups dos arquivos: %%A
    echo   📁 Último: %ZIP_BACKUP%
)
echo ✓ Backup local concluído

echo.
echo [4/5] Configurando autenticação do GitHub...
if exist "%GITHUB_CONFIG%" (
    echo ✓ Configuração do GitHub encontrada
    
    :: Carrega configurações do GitHub
    for /f "tokens=* usebackq" %%a in ("%GITHUB_CONFIG%") do set "config=%%a"
    for /f "tokens=2 delims=:, " %%a in ('echo !config! ^| findstr "repo_url"') do (
        set "repo_url=%%~a"
        set "repo_url=!repo_url:"=!"
    )
    for /f "tokens=2 delims=:, " %%a in ('echo !config! ^| findstr "username"') do (
        set "username=%%~a"
        set "username=!username:"=!"
    )
    for /f "tokens=2 delims=:, " %%a in ('echo !config! ^| findstr "token"') do (
        set "token=%%~a"
        set "token=!token:"=!"
    )
) else (
    echo.
    echo Configuração do GitHub necessária.
    echo.
    set /p repo_url="Digite a URL do repositório GitHub: "
    set /p username="Digite seu nome de usuário GitHub: "
    set /p token="Digite seu token de acesso GitHub: "
    
    echo {"repo_url": "%repo_url%", "username": "%username%", "token": "%token%"} > "%GITHUB_CONFIG%"
    echo.
    echo ✓ Configuração do GitHub salva
)

echo.
echo [5/5] Configurando Git...
:: Limpa repositório Git existente
echo Limpando repositório Git anterior...
rd /s /q .git >nul 2>&1

:: Remove configuração antiga do Git
git config --global --unset http.https://github.com/.extraheader
git remote remove origin >nul 2>&1

:: Configura autenticação do Git
git config --global user.name "redhotsite"
git config --global user.email "redhotsistemas@gmail.com"
git config --global core.autocrlf true

:: Inicializa novo repositório
echo Inicializando novo repositório Git...
git init >nul

:: Cria/atualiza .gitignore
echo # Arquivos de configuração com dados sensíveis > .gitignore
echo github_config.json >> .gitignore
echo .git-credentials >> .gitignore
echo changelog.txt >> .gitignore
echo. >> .gitignore
echo # Arquivos de backup >> .gitignore
echo *.zip >> .gitignore
echo backups/ >> .gitignore
echo. >> .gitignore
echo # Arquivos do Python >> .gitignore
echo __pycache__/ >> .gitignore
echo *.py[cod] >> .gitignore
echo *$py.class >> .gitignore
echo. >> .gitignore
echo # Banco de dados >> .gitignore
echo *.db >> .gitignore
echo *.sqlite3 >> .gitignore
echo. >> .gitignore
echo # Logs >> .gitignore
echo *.log >> .gitignore
echo. >> .gitignore
echo # Arquivos de média e uploads >> .gitignore
echo static/uploads/ >> .gitignore

:: Configura o repositório remoto
echo Configurando repositório remoto...
git remote add origin "https://%token%@github.com/redhotsite/redsite.git"

:: Cria e configura branch main
echo Configurando branch main...
git add .gitignore
git commit -m "Configuração inicial do repositório" >nul 2>&1
git branch -M main

:: Tenta sincronizar com o repositório remoto
echo Sincronizando com GitHub...
git fetch origin main >nul 2>&1
if %errorlevel% equ 0 (
    :: Se o fetch funcionou, tenta fazer merge
    echo Integrando alterações remotas...
    git reset --soft origin/main >nul 2>&1
    git add --all
    git commit -m "Sincronização com repositório remoto" >nul 2>&1
    
    :: Força o push após sincronização
    echo Forçando atualização do repositório...
    git push -f origin main >nul 2>&1
) else (
    :: Se não conseguiu fazer fetch, tenta fazer o primeiro push
    echo Primeiro push para o repositório...
    git push -f origin main >nul 2>&1
)

:: Adiciona todos os arquivos
git add --all

:: Gera changelog e faz commit
echo Gerando notas de mudanças...
echo # Backup Automático - %date% %time% > "%CHANGELOG_FILE%"
echo. >> "%CHANGELOG_FILE%"
echo ## Alterações: >> "%CHANGELOG_FILE%"
git status --porcelain | findstr /V "backups/ .gitignore changelog.txt" >> "%CHANGELOG_FILE%"

:: Faz commit e push
git commit -F "%CHANGELOG_FILE%" >nul 2>&1
echo Enviando para GitHub...
git push -f origin main

:: Remove arquivo de changelog
del "%CHANGELOG_FILE%" >nul 2>&1

echo.
echo Backup concluído!
echo Próximo backup em %INTERVAL_MINUTES% minutos...
timeout /t %BACKUP_INTERVAL% /nobreak
goto backup_loop

:check_dirs
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:backup_loop
cls
:: Obtém timestamp atual
set "TIMESTAMP=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_NAME=redsite_%TIMESTAMP%"

echo ========================================================
echo           RED HOT - Backup Automático
echo ========================================================
echo.
echo [%date% %time%] Iniciando backup...

:: 1. Backup do banco de dados
echo [1/5] Copiando banco de dados...
echo - Origem: %WORKSPACE%\%DB_FILE%
echo - Destino: %BACKUP_DIR%\db_%BACKUP_NAME%.db
copy "%WORKSPACE%\%DB_FILE%" "%BACKUP_DIR%\db_%BACKUP_NAME%.db" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Banco de dados copiado
) else (
    echo × Falha ao copiar banco de dados
    goto cleanup_old
)

:: 2. Backup dos arquivos
echo.
echo [2/5] Compactando arquivos...
echo - Destino: %BACKUP_DIR%\%BACKUP_NAME%.zip
cd /d "%WORKSPACE%"
"C:\Program Files\7-Zip\7z.exe" a -tzip "%BACKUP_DIR%\%BACKUP_NAME%.zip" * -x!backups -x!__pycache__ -x!*.pyc -x!*.db -x!*.log -x!github_config.json -x!.git -x!.gitignore >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Arquivos compactados
) else (
    echo × Falha ao compactar arquivos
    goto cleanup_old
)

:: 3. Limpeza de backups antigos
echo.
echo [3/5] Limpando backups antigos...
:: Remove backups antigos do banco de dados
for /f "skip=%MAX_BACKUPS% delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\db_redsite_*.db" 2^>nul') do (
    echo - Removendo: %%F
    del "%BACKUP_DIR%\%%F" >nul 2>&1
)
:: Remove backups antigos dos arquivos
for /f "skip=%MAX_BACKUPS% delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\redsite_*.zip" 2^>nul') do (
    echo - Removendo: %%F
    del "%BACKUP_DIR%\%%F" >nul 2>&1
)
echo ✓ Backups antigos removidos

:: 4. Backup para GitHub
echo.
echo [4/5] Enviando para GitHub...

:: Puxa alterações mais recentes
echo Sincronizando com GitHub...
git pull origin main --no-rebase >nul 2>&1

:: Gera changelog das alterações
echo Gerando notas de mudanças...
echo # Backup Automático - %date% %time% > "%CHANGELOG_FILE%"
echo. >> "%CHANGELOG_FILE%"

:: Adiciona informações do autor
echo ## Autor: >> "%CHANGELOG_FILE%"
echo - Usuário: !username! >> "%CHANGELOG_FILE%"
echo - Email: !username!@users.noreply.github.com >> "%CHANGELOG_FILE%"
echo. >> "%CHANGELOG_FILE%"

:: Lista arquivos modificados
echo ## Arquivos Alterados: >> "%CHANGELOG_FILE%"
git status --porcelain | findstr /V "backups/ .gitignore changelog.txt" >> "%TEMP%\changed_files.txt"
for /f "tokens=1,2" %%a in (%TEMP%\changed_files.txt) do (
    set "status=%%a"
    set "file=%%b"
    
    if "!status!"=="M" (
        echo - ✏️ Modificado: !file! >> "%CHANGELOG_FILE%"
    ) else if "!status!"=="A" (
        echo - ➕ Adicionado: !file! >> "%CHANGELOG_FILE%"
    ) else if "!status!"=="D" (
        echo - ❌ Removido: !file! >> "%CHANGELOG_FILE%"
    )
)
del "%TEMP%\changed_files.txt" >nul 2>&1

:: Adiciona estatísticas
echo. >> "%CHANGELOG_FILE%"
echo ## Estatísticas: >> "%CHANGELOG_FILE%"
echo - 📊 Total de backups: >> "%CHANGELOG_FILE%"
for /f %%A in ('dir /b /a-d "%BACKUP_DIR%\db_redsite_*.db" 2^>nul ^| find /c /v ""') do echo   * 💾 Banco de dados: %%A backups >> "%CHANGELOG_FILE%"
for /f %%A in ('dir /b /a-d "%BACKUP_DIR%\redsite_*.zip" 2^>nul ^| find /c /v ""') do echo   * 📦 Arquivos: %%A backups >> "%CHANGELOG_FILE%"

:: Adiciona detalhes do backup
echo. >> "%CHANGELOG_FILE%"
echo ## Detalhes do Backup: >> "%CHANGELOG_FILE%"
echo - 📅 Data: %date% >> "%CHANGELOG_FILE%"
echo - ⏰ Hora: %time% >> "%CHANGELOG_FILE%"
echo - 📁 Arquivos gerados: >> "%CHANGELOG_FILE%"
echo   * 💾 %BACKUP_DIR%\db_%BACKUP_NAME%.db >> "%CHANGELOG_FILE%"
echo   * 📦 %BACKUP_DIR%\%BACKUP_NAME%.zip >> "%CHANGELOG_FILE%"

:: Faz o commit e push
echo Enviando para GitHub...
git add --all
git commit -F "%CHANGELOG_FILE%" >nul
git push -u origin main >nul 2>&1

if %errorlevel% equ 0 (
    echo ✓ Backup enviado para o GitHub
    echo ✓ Notas de mudanças geradas
    echo ✓ Commit disponível em: !repo_url!/commits/main
) else (
    echo × Falha ao enviar para GitHub
    echo   Tentando método alternativo...
    
    :: Tenta push alternativo com token
    git push "https://!token!@github.com/!username!/!repo_url:https://github.com/=!" main >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✓ Backup enviado com sucesso usando método alternativo
    ) else (
        echo × Falha ao enviar para GitHub
        echo   Verifique suas credenciais e conexão
    )
)

:: Remove arquivo de changelog temporário
del "%CHANGELOG_FILE%" >nul 2>&1

:: 5. Verificação final
echo.
echo [5/5] Verificando backup...
if exist "%BACKUP_DIR%\db_%BACKUP_NAME%.db" if exist "%BACKUP_DIR%\%BACKUP_NAME%.zip" (
    echo ✓ Backup concluído com sucesso!
    echo.
    echo Arquivos gerados:
    echo - %BACKUP_DIR%\db_%BACKUP_NAME%.db
    echo - %BACKUP_DIR%\%BACKUP_NAME%.zip
) else (
    echo × Falha na verificação do backup
)

:cleanup_old
:: Mostra estatísticas
echo.
echo Estatísticas:
for /f %%A in ('dir /b /a-d "%BACKUP_DIR%\db_redsite_*.db" 2^>nul ^| find /c /v ""') do echo - Backups do banco: %%A
for /f %%A in ('dir /b /a-d "%BACKUP_DIR%\redsite_*.zip" 2^>nul ^| find /c /v ""') do echo - Backups dos arquivos: %%A

echo.
echo Próximo backup em %INTERVAL_MINUTES% minutos...
echo ========================================================

:: Contador regressivo
set /a "total_seconds=%BACKUP_INTERVAL%"
:countdown
cls
echo ========================================================
echo           RED HOT - Backup Automático
echo ========================================================
echo.
echo Último backup: %BACKUP_NAME%
echo - Banco: %BACKUP_DIR%\db_%BACKUP_NAME%.db
echo - Arquivos: %BACKUP_DIR%\%BACKUP_NAME%.zip
echo.
echo Próximo backup em:
set /a "minutes=%total_seconds%/60"
set /a "seconds=%total_seconds%%%60"
if %seconds% lss 10 set "seconds=0%seconds%"
echo %minutes%:%seconds%
echo.
echo Pressione CTRL+C para encerrar
echo ========================================================
timeout /t 1 /nobreak >nul
set /a "total_seconds-=1"
if %total_seconds% geq 0 goto countdown

goto backup_loop 