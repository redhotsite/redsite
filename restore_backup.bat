@echo off
chcp 65001 > nul
title RED HOT - Restauração de Backup
color 0A
setlocal EnableDelayedExpansion

:: Configurações
set "WORKSPACE=C:\Users\allef\Desktop\redsite"
set "BACKUP_DIR=C:\Users\allef\Desktop\redsite\backups"
set "DB_FILE=users.db"
set "RESTORE_DIR=%WORKSPACE%\restored"

echo ========================================================
echo           RED HOT - Restauração de Backup
echo ========================================================
echo.

:: Verifica 7-Zip
if not exist "C:\Program Files\7-Zip\7z.exe" (
    color 0C
    echo ERRO: 7-Zip não encontrado!
    echo 1. Baixe o 7-Zip de https://7-zip.org/
    echo 2. Instale para todos os usuários
    echo 3. Execute este script novamente
    pause
    exit
)

:: Lista backups disponíveis
echo Backups disponíveis:
echo.
set "count=0"
for /f "delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\redsite_*.zip" 2^>nul') do (
    set /a "count+=1"
    set "backup[!count!]=%%F"
    echo [!count!] %%F
)

if !count! equ 0 (
    color 0C
    echo ERRO: Nenhum backup encontrado em %BACKUP_DIR%
    pause
    exit
)

echo.
set /p "choice=Escolha o número do backup para restaurar (1-!count!): "

:: Valida escolha
if !choice! lss 1 (
    color 0C
    echo Escolha inválida!
    pause
    exit
)
if !choice! gtr !count! (
    color 0C
    echo Escolha inválida!
    pause
    exit
)

:: Obtém nome do backup escolhido
set "chosen_backup=!backup[%choice%]!"
set "chosen_db=db_redsite_!chosen_backup:redsite_=!"

echo.
echo Backup selecionado:
echo - Arquivos: !chosen_backup!
echo - Banco de dados: !chosen_db!
echo.
set /p "confirm=Tem certeza que deseja restaurar este backup? (S/N): "
if /i not "!confirm!"=="S" (
    echo Operação cancelada.
    pause
    exit
)

echo.
echo [1/5] Preparando restauração...
:: Cria diretório de restauração
if exist "%RESTORE_DIR%" (
    echo Limpando diretório de restauração anterior...
    rd /s /q "%RESTORE_DIR%" >nul
)
mkdir "%RESTORE_DIR%" >nul
echo ✓ Diretório de restauração criado

echo.
echo [2/5] Extraindo arquivos...
cd /d "%BACKUP_DIR%"
echo Extraindo: !chosen_backup!
"C:\Program Files\7-Zip\7z.exe" x "!chosen_backup!" -o"%RESTORE_DIR%" -y >nul
if !errorlevel! equ 0 (
    echo ✓ Arquivos extraídos com sucesso
) else (
    color 0C
    echo × Falha ao extrair arquivos!
    echo Arquivo: !chosen_backup!
    echo Diretório: %BACKUP_DIR%
    dir "%BACKUP_DIR%\!chosen_backup!" 2>nul
    pause
    exit
)

echo.
echo [3/5] Restaurando banco de dados...
echo Copiando: !chosen_db!
if not exist "%BACKUP_DIR%\!chosen_db!" (
    color 0C
    echo × Falha ao restaurar banco de dados!
    echo Arquivo não encontrado: !chosen_db!
    echo.
    echo Arquivos disponíveis no diretório:
    dir "%BACKUP_DIR%\db_*.db" /b 2>nul
    echo.
    echo Tentando localizar arquivo mais recente...
    for /f "delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\db_*.db" 2^>nul') do (
        echo Encontrado: %%F
        set "chosen_db=%%F"
        goto :found_db
    )
    pause
    exit
)
:found_db
copy "%BACKUP_DIR%\!chosen_db!" "%RESTORE_DIR%\%DB_FILE%" >nul
if !errorlevel! equ 0 (
    echo ✓ Banco de dados restaurado
) else (
    color 0C
    echo × Falha ao restaurar banco de dados!
    echo Arquivo: !chosen_db!
    echo Diretório: %BACKUP_DIR%
    dir "%BACKUP_DIR%\!chosen_db!" 2>nul
    pause
    exit
)

echo.
echo [4/5] Verificando restauração...
if exist "%RESTORE_DIR%\app.py" if exist "%RESTORE_DIR%\%DB_FILE%" (
    echo ✓ Verificação concluída
) else (
    color 0C
    echo × Falha na verificação!
    echo Arquivos no diretório de restauração:
    dir "%RESTORE_DIR%" 2>nul
    pause
    exit
)

echo.
echo [5/5] Finalizando...
echo.
echo ========================================================
echo              Restauração Concluída!
echo ========================================================
echo.
echo Os arquivos foram restaurados em:
echo %RESTORE_DIR%
echo.
echo Para usar a versão restaurada:
echo 1. Pare o servidor Flask se estiver rodando
echo 2. Copie os arquivos de %RESTORE_DIR% para %WORKSPACE%
echo    (ou use o diretório restaurado diretamente)
echo.
echo Pressione qualquer tecla para sair...
pause >nul 