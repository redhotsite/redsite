@echo off
chcp 65001 > nul
title RED HOT - Sistema de Backup

:: Configurações
set BACKUP_DIR=backups
set MAX_BACKUPS=5
set DB_FILE=users.db
set GITHUB_CONFIG=github_config.json

:: Cria diretório de backup se não existir
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    echo ✓ Diretório de backup criado
)

:: Verifica se o banco de dados existe
if not exist "%DB_FILE%" (
    echo ERRO: Arquivo %DB_FILE% não encontrado!
    pause
    exit /b 1
)

:: Gera nome do arquivo de backup com timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%
set BACKUP_FILE=users_backup_%timestamp%.db

:: Cria o backup
echo.
echo ========================================================
echo                 Criando Backup Local
echo ========================================================
echo.
echo [1/4] Copiando banco de dados...
copy "%DB_FILE%" "%BACKUP_DIR%\%BACKUP_FILE%" >nul
if %errorlevel% neq 0 (
    echo ERRO: Falha ao criar backup!
    pause
    exit /b 1
)
echo ✓ Backup criado: %BACKUP_FILE%

echo.
echo [2/4] Removendo backups antigos...
:: Conta quantos backups existem
set count=0
for %%F in (%BACKUP_DIR%\users_backup_*.db) do set /a count+=1

:: Remove os mais antigos se exceder o limite
if %count% gtr %MAX_BACKUPS% (
    for /f "skip=%MAX_BACKUPS% delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\users_backup_*.db"') do (
        del "%BACKUP_DIR%\%%F"
        echo ✓ Backup antigo removido: %%F
    )
) else (
    echo ✓ Nenhum backup antigo para remover
)

echo.
echo [3/4] Verificando configuração do GitHub...
if exist "%GITHUB_CONFIG%" (
    echo ✓ Configuração do GitHub encontrada
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
echo [4/4] Enviando para o GitHub...
:: Verifica se o Git está instalado
git --version >nul 2>nul
if %errorlevel% neq 0 (
    echo AVISO: Git não encontrado. O backup não será enviado para o GitHub.
    echo Para habilitar backup no GitHub, instale o Git de https://git-scm.com/
    goto finish
)

:: Configura o Git se necessário
if not exist ".git" (
    echo Inicializando repositório Git...
    git init >nul
    
    :: Cria/atualiza .gitignore
    echo users.db> .gitignore
    echo __pycache__/>> .gitignore
    echo *.pyc>> .gitignore
    echo static/uploads/>> .gitignore
    echo backups/>> .gitignore
    echo *.log>> .gitignore
    echo github_config.json>> .gitignore
    
    :: Configura o repositório
    for /f "tokens=*" %%a in ('type "%GITHUB_CONFIG%"') do set config=%%a
    for /f "tokens=2 delims=:, " %%a in ('echo !config! ^| findstr "repo_url"') do set repo_url=%%a
    for /f "tokens=2 delims=:, " %%a in ('echo !config! ^| findstr "username"') do set username=%%a
    
    git remote add origin !repo_url!
    git config user.name !username!
)

:: Faz commit e push
git add .
git commit -m "Backup automático - %date% %time%" >nul
git push origin main >nul 2>nul
if %errorlevel% equ 0 (
    echo ✓ Backup enviado para o GitHub
) else (
    echo AVISO: Não foi possível enviar para o GitHub
    echo Verifique suas credenciais e conexão
)

:finish
echo.
echo ========================================================
echo                 Backup Concluído!
echo ========================================================
echo.
echo ✓ Backup local criado em: %BACKUP_DIR%\%BACKUP_FILE%
echo ✓ Logs salvos em: backup.log
echo.
pause 