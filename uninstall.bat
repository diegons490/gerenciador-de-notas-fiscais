@echo off
setlocal

set "APP_NAME=Gerenciador de Notas Fiscais"
set "APP_DIR_NAME=gerenciador-de-notas-fiscais"
set "INSTALL_DIR=%USERPROFILE%\AppData\Local\%APP_DIR_NAME%"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

echo Desinstalando %APP_NAME%...

:: Remove atalho
del "%START_MENU_DIR%\%APP_NAME%.lnk" >nul 2>&1

:: Remove diretório
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo Aplicativo removido com sucesso!
) else (
    echo Aplicativo não estava instalado.
)

echo.
pause
