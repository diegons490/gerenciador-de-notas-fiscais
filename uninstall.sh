#!/bin/bash
# Desinstalador do aplicativo Controle de Notas Fiscais (nível usuário)

APP_NAME="Controle de Notas Fiscais"
APP_DIR_NAME="controle_de_notas_fiscais"
INSTALL_DIR="$HOME/.local/share/$APP_DIR_NAME"
BIN_FILE="$HOME/.local/bin/controle_de_notas_fiscais"
ICON_FILE="$HOME/.local/share/icons/controle_de_notas_fiscais.png"
DESKTOP_FILE="$HOME/.local/share/applications/controle_de_notas_fiscais.desktop"

echo ">> Desinstalando $APP_NAME..."

rm -rf "$INSTALL_DIR"
rm -f "$BIN_FILE"
rm -f "$ICON_FILE"
rm -f "$DESKTOP_FILE"

echo ">> Desinstalação concluída!"
