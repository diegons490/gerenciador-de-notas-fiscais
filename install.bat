@echo off
setlocal enabledelayedexpansion

set "APP_NAME=Gerenciador de Notas Fiscais"
set "APP_DIR_NAME=gerenciador-de-notas-fiscais"
set "INSTALL_DIR=%USERPROFILE%\AppData\Local\%APP_DIR_NAME%"
set "DATA_DIR=%INSTALL_DIR%\data"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

echo Verificando dependências...

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python não encontrado!
    echo Instale Python em https://python.org
    pause
    exit /b 1
)

:: Verifica bibliotecas
python -c "import ttkbootstrap" >nul 2>&1
if errorlevel 1 (
    echo AVISO: ttkbootstrap não encontrado. Instalando...
    pip install ttkbootstrap
)

python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo AVISO: Pillow não encontrado. Instalando...
    pip install pillow
)

echo Instalando %APP_NAME%...

:: Cria diretórios
mkdir "%INSTALL_DIR%" >nul 2>&1
mkdir "%DATA_DIR%" >nul 2>&1

:: Copia arquivos
xcopy /E /I /Y "%~dp0*" "%INSTALL_DIR%"

:: Cria estrutura de dados
if not exist "%DATA_DIR%\notas.db" type nul > "%DATA_DIR%\notas.db"
if not exist "%DATA_DIR%\cadastros.db" type nul > "%DATA_DIR%\cadastros.db"
echo {"tema": "cosmo", "window_state": {}} > "%DATA_DIR%\config.json"

:: Cria atalho
set "SCRIPT=%INSTALL_DIR%\launcher.vbs"
echo Set WshShell = CreateObject("WScript.Shell") > "!SCRIPT!"
echo Set lnk = WshShell.CreateShortcut("%START_MENU_DIR%\%APP_NAME%.lnk") >> "!SCRIPT!"
echo lnk.TargetPath = "python" >> "!SCRIPT!"
echo lnk.Arguments = """%INSTALL_DIR%\main.py""" >> "!SCRIPT!"
echo lnk.WorkingDirectory = "%INSTALL_DIR%" >> "!SCRIPT!"
echo lnk.Save >> "!SCRIPT!"

wscript "!SCRIPT!"
del "!SCRIPT!"

echo Instalação concluída com sucesso!
echo.
echo O aplicativo foi instalado em: %INSTALL_DIR%
echo Procure por "%APP_NAME%" no Menu Iniciar.
pause
