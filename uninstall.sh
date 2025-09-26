#!/bin/bash
# Desinstalador do aplicativo Gerenciador de Notas Fiscais (nível usuário)

APP_NAME="Gerenciador de Notas Fiscais"
APP_DIR_NAME="gerenciador-de-notas-fiscais"
INSTALL_DIR="$HOME/.local/share/$APP_DIR_NAME"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_DIR="$HOME/.local/share/applications"

echo ">> Desinstalando $APP_NAME..."

# Remove arquivos de atalho
rm -f "$BIN_DIR/gerenciador-de-notas-fiscais"
rm -f "$DESKTOP_DIR/gerenciador-de-notas-fiscais.desktop"
rm -f "$ICON_DIR/gerenciador-de-notas-fiscais.png"

# Remove diretório de instalação
if [ -d "$INSTALL_DIR" ]; then
    echo "Removendo arquivos do aplicativo..."
    rm -rf "$INSTALL_DIR"
fi

# Atualiza bancos de dados
echo "Atualizando bancos de dados de aplicativos..."
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi

echo ">> Desinstalação concluída com sucesso!"
