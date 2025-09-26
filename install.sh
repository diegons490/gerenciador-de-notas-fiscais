#!/bin/bash
# Instalador do aplicativo Gerenciador de Notas Fiscais (nível usuário)

APP_NAME="Gerenciador de Notas Fiscais"
APP_DIR_NAME="gerenciador_de_notas_fiscais"
INSTALL_DIR="$HOME/.local/share/$APP_DIR_NAME"
DATA_DIR="$INSTALL_DIR/data"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_DIR="$HOME/.local/share/applications"

echo ">> Verificando dependências..."

# Verifica se o FreeSimpleGUI está instalado
if ! python3 -c "import FreeSimpleGUI" &>/dev/null; then
    echo "Erro: FreeSimpleGUI não encontrado!"
    echo "Instale usando: pip install FreeSimpleGUI - sistemas Arch pode ser pipx... -"
    exit 1
fi

echo ">> Instalando $APP_NAME..."

# Cria pastas necessárias
mkdir -p "$INSTALL_DIR" "$DATA_DIR" "$BIN_DIR" "$ICON_DIR" "$DESKTOP_DIR"

# Copia aplicação (excluindo a pasta data se existir no source)
rsync -a --exclude=data "$(dirname "$0")/" "$INSTALL_DIR/"

# Cria pasta data e copia arquivos existentes se houver
if [ -d "$(dirname "$0")/data" ]; then
    cp -r "$(dirname "$0")/data/"* "$DATA_DIR/"
else
    # Cria arquivos padrão se não existirem
    touch "$DATA_DIR/notas.db"
    echo '{"tema": "SystemDefault"}' >"$DATA_DIR/config.json"
fi

# Copia ícone
cp "$INSTALL_DIR/icons/NF.png" "$ICON_DIR/gerenciador_de_notas_fiscais.png"

# Cria script lançador
cat >"$BIN_DIR/gerenciador_de_notas_fiscais" <<EOF
#!/bin/bash
export GERENCIADOR_NOTAS_DATA_DIR="$DATA_DIR"
exec python3 "$INSTALL_DIR/main.py" "\$@"
EOF
chmod +x "$BIN_DIR/gerenciador_de_notas_fiscais"

# Cria atalho .desktop
cat >"$DESKTOP_DIR/gerenciador_de_notas_fiscais.desktop" <<EOF
[Desktop Entry]
Name=$APP_NAME
Comment=Armazena informações e valores das notas fiscais para consultas e cálculos posteriores
Exec=$BIN_DIR/gerenciador_de_notas_fiscais
Icon=gerenciador_de_notas_fiscais
Type=Application
Terminal=false
Categories=Office;Finance;
EOF

echo ">> Instalação concluída!"
echo "Execute 'gerenciador_de_notas_fiscais' no terminal ou procure no menu de aplicativos."
