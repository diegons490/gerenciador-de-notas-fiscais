@echo off
REM Desinstalador do aplicativo Controle de Notas Fiscais (Windows - nível usuário)

set APP_NAME=Controle de Notas Fiscais
set APP_DIR_NAME=controle_de_notas_fiscais
set INSTALL_DIR=%LOCALAPPDATA%\%APP_DIR_NAME%
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
set SHORTCUT_NAME=%APP_NAME%.lnk

echo >> Desinstalando %APP_NAME%...

REM Remove pasta de instalação
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo - Pasta de instalacao removida.
) else (
    echo - Pasta de instalacao nao encontrada.
)

REM Remove atalho do Menu Iniciar
if exist "%START_MENU%\%SHORTCUT_NAME%" (
    del "%START_MENU%\%SHORTCUT_NAME%"
    echo - Atalho do Menu Iniciar removido.
) else (
    echo - Atalho do Menu Iniciar nao encontrado.
)

echo >> Desinstalacao concluida!
pause
