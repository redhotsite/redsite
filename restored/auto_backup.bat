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
echo [1/4] Copiando banco de dados...
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
echo [2/4] Compactando arquivos...
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
echo [3/4] Limpando backups antigos...
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

:: 4. Verificação final
echo.
echo [4/4] Verificando backup...
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