@echo off
REM Instalador do aplicativo Gerenciador de Notas Fiscais (Windows - nível usuário)

set APP_NAME=Gerenciador de Notas Fiscais
set APP_DIR_NAME=gerenciador_de_notas_fiscais
set INSTALL_DIR=%LOCALAPPDATA%\%APP_DIR_NAME%
set DATA_DIR=%INSTALL_DIR%\data
set ICON_FILE=%INSTALL_DIR%\icons\NF.png
set SHORTCUT_NAME=%APP_NAME%.lnk

echo [1/4] Verificando dependencias...

REM Verifica se Python está instalado
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Erro: Python nao encontrado no PATH.
    echo Instale o Python 3.10 ou superior.
    pause
    exit /b 1
)

REM Verifica se FreeSimpleGUI esta instalado
python -c "import FreeSimpleGUI" >nul 2>&1
if %errorlevel% neq 0 (
    echo Erro: FreeSimpleGUI nao encontrado!
    echo Instale usando: pip install FreeSimpleGUI
    pause
    exit /b 1
)

echo [2/4] Instalando %APP_NAME%...

REM Cria pastas
mkdir "%INSTALL_DIR%" >nul 2>&1
mkdir "%DATA_DIR%" >nul 2>&1

REM Copia todos arquivos do projeto para INSTALL_DIR
xcopy "%~dp0*" "%INSTALL_DIR%\" /E /I /Y >nul

REM Cria arquivos padrão se não existirem
if not exist "%DATA_DIR%\notas.db" (
    type nul > "%DATA_DIR%\notas.db"
)
if not exist "%DATA_DIR%\config.json" (
    echo {"tema": "SystemDefault"} > "%DATA_DIR%\config.json"
)

echo [3/4] Criando atalho no Menu Iniciar...

REM Cria um script lançador .bat dentro da pasta de instalação
(
echo @echo off
echo set GERENCIADOR_NOTAS_DATA_DIR=%DATA_DIR%
echo python "%INSTALL_DIR%\main.py" %%*
) > "%INSTALL_DIR%\start_app.bat"

REM Usa PowerShell para criar um atalho .lnk no Menu Iniciar
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
powershell -command ^
    "$s=(New-Object -COM WScript.Shell).CreateShortcut('%START_MENU%\%SHORTCUT_NAME%');" ^
    "$s.TargetPath='%INSTALL_DIR%\start_app.bat';" ^
    "$s.IconLocation='%ICON_FILE%';" ^
    "$s.Save()"

echo [4/4] Instalacao concluida!
echo Voce pode iniciar o aplicativo pelo Menu Iniciar como "%APP_NAME%" ou executar:
echo "%INSTALL_DIR%\start_app.bat"
pause
