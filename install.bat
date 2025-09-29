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

:: Verifica se pythonw existe (Python para Windows sem console)
where pythonw >nul 2>&1
if errorlevel 1 (
    echo AVISO: pythonw.exe não encontrado. Criando cópia de python.exe como pythonw.exe...
    for /f "delims=" %%I in ('where python') do (
        copy "%%~I" "%%~dpIpythonw.exe" >nul 2>&1
    )
)

:: Verifica bibliotecas necessárias
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

:: Copia arquivos do projeto
xcopy /E /I /Y "%~dp0*" "%INSTALL_DIR%" >nul

:: Cria estrutura de dados inicial
if not exist "%DATA_DIR%\notas.db" type nul > "%DATA_DIR%\notas.db"
if not exist "%DATA_DIR%\cadastros.db" type nul > "%DATA_DIR%\cadastros.db"
if not exist "%DATA_DIR%\config.json" echo {"tema": "cosmo", "window_state": {}} > "%DATA_DIR%\config.json"

:: Cria atalho no Menu Iniciar com PowerShell
set "PS_SCRIPT=%INSTALL_DIR%\create_shortcut.ps1"

> "%PS_SCRIPT%" echo $WshShell = New-Object -ComObject WScript.Shell
>> "%PS_SCRIPT%" echo $Shortcut = $WshShell.CreateShortcut("%START_MENU_DIR%\%APP_NAME%.lnk")
>> "%PS_SCRIPT%" echo $Shortcut.TargetPath = "pythonw.exe"
>> "%PS_SCRIPT%" echo $Shortcut.Arguments = '%INSTALL_DIR%\main.py'
>> "%PS_SCRIPT%" echo $Shortcut.WorkingDirectory = "%INSTALL_DIR%"
>> "%PS_SCRIPT%" echo $Shortcut.IconLocation = "%INSTALL_DIR%\icons\GNF.ico"
>> "%PS_SCRIPT%" echo $Shortcut.WindowStyle = 1
>> "%PS_SCRIPT%" echo $Shortcut.Save()

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del "%PS_SCRIPT%" >nul 2>&1

echo.
echo Instalação concluída com sucesso!
echo O aplicativo foi instalado em: %INSTALL_DIR%
echo Procure por "%APP_NAME%" no Menu Iniciar.
pause
