@echo off
setlocal

set "APP_NAME=Gerenciador de Notas Fiscais"
set "APP_DIR_NAME=gerenciador-de-notas-fiscais"
set "INSTALL_DIR=%USERPROFILE%\AppData\Local\%APP_DIR_NAME%"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "SHORTCUT=%START_MENU_DIR%\%APP_NAME%.lnk"

echo Desinstalando %APP_NAME%...

:: Remove atalho do Menu Iniciar
if exist "%SHORTCUT%" (
    del "%SHORTCUT%" >nul 2>&1
    echo Atalho removido: %SHORTCUT%
) else (
    echo Nenhum atalho encontrado em %SHORTCUT%
)

:: Remove diretório de instalação
if exist "%INSTALL_DIR%" (
    echo Removendo arquivos em %INSTALL_DIR%...
    rmdir /S /Q "%INSTALL_DIR%"
    echo Diretório de instalação removido.
) else (
    echo Nenhum diretório de instalação encontrado em %INSTALL_DIR%
)

echo.
echo %APP_NAME% foi desinstalado com sucesso!
pause
