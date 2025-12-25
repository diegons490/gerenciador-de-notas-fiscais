#!/bin/bash
# Instalador do aplicativo Gerenciador de Notas Fiscais (nível usuário)

APP_NAME="Gerenciador de Notas Fiscais"
APP_DIR_NAME="gerenciador-de-notas-fiscais"
INSTALL_DIR="$HOME/.local/share/$APP_DIR_NAME"
DATA_DIR="$INSTALL_DIR/data"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_DIR="$HOME/.local/share/applications"

echo ">> Verificando dependências..."

MISSING_DEPS=()
CRITICAL_ERROR=false

# Python
if ! command -v python3 &>/dev/null; then
    MISSING_DEPS+=("python3")
    CRITICAL_ERROR=true
fi

# pip ou pipx (não crítico, apenas informativo)
if ! command -v pip3 &>/dev/null && ! command -v pipx &>/dev/null; then
    MISSING_DEPS+=("pip3 ou pipx (para instalar dependências Python)")
fi

# ttkbootstrap (verificação só se python3 existir)
if command -v python3 &>/dev/null; then
    if ! python3 -c "import ttkbootstrap" &>/dev/null; then
        MISSING_DEPS+=("ttkbootstrap (execute: pip install ttkbootstrap)")
        CRITICAL_ERROR=true
    fi

    # pillow (python-pillow)
    if ! python3 -c "import PIL" &>/dev/null; then
        MISSING_DEPS+=("pillow (execute: pip install pillow)")
        CRITICAL_ERROR=true
    fi
fi

# Se houver erro crítico, exibir e abortar
if [ "$CRITICAL_ERROR" = true ]; then
    echo ">> ERRO: Dependências críticas ausentes!"
    echo "A instalação será interrompida. Instale as seguintes dependências primeiro:"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "   - $dep"
    done
    echo ""
    echo "Depois de instalar as dependências, execute este script novamente."
    exit 1
fi

# Se chegou aqui, todas as dependências críticas estão satisfeitas
echo ">> Todas as dependências necessárias foram encontradas."
echo ">> Iniciando instalação do $APP_NAME..."

# Cria pastas necessárias
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$ICON_DIR" "$DESKTOP_DIR"

# Copia toda a estrutura do projeto recursivamente (exceto lixo e .exe)
echo "Copiando arquivos do aplicativo..."
rsync -a --exclude="__pycache__" --exclude="*.pyc" --exclude="*.pyo" --exclude="*.exe" "$(dirname "$0")/" "$INSTALL_DIR/"

# Garante estrutura de dados
if [ ! -d "$DATA_DIR" ]; then
    echo "Criando estrutura de dados padrão..."
    mkdir -p "$DATA_DIR"
    touch "$DATA_DIR/notas.db" "$DATA_DIR/cadastros.db"
    echo '{"tema": "cosmo", "window_state": {}}' >"$DATA_DIR/config.json"
fi

# Copia ícone principal (GNF.png)
if [ -f "$INSTALL_DIR/icons/GNF.png" ]; then
    cp "$INSTALL_DIR/icons/GNF.png" "$ICON_DIR/gerenciador-de-notas-fiscais.png"
else
    echo "Aviso: Ícone GNF.png não encontrado, criando placeholder..."
    convert -size 64x64 xc:blue -pointsize 12 -fill white -annotate +10+32 "NF" \
        "$ICON_DIR/gerenciador-de-notas-fiscais.png" 2>/dev/null ||
        echo "Ícone placeholder não pôde ser criado (ImageMagick não instalado)"
fi

# Script lançador
echo "Criando script de lançamento..."
cat >"$BIN_DIR/gerenciador-de-notas-fiscais" <<EOF
#!/bin/bash
export CONTROLE_NOTAS_DATA_DIR="$DATA_DIR"
cd "$INSTALL_DIR"
exec python3 main.py "\$@"
EOF
chmod +x "$BIN_DIR/gerenciador-de-notas-fiscais"

# Atalho .desktop (usuário)
echo "Criando atalho do aplicativo..."
cat >"$DESKTOP_DIR/gerenciador-de-notas-fiscais.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=Armazena informações e valores das notas fiscais para consultas e cálculos posteriores
Exec=$BIN_DIR/gerenciador-de-notas-fiscais
Icon=gerenciador-de-notas-fiscais
Categories=Office;Finance;
Terminal=false
StartupNotify=true
EOF

# Atualiza banco de apps e ícones (nível usuário)
echo "Atualizando banco de dados de aplicativos..."
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
xdg-desktop-menu forceupdate 2>/dev/null || true

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi

echo ">> Instalação concluída com sucesso!"
echo ""
echo "Aplicativo instalado em: $INSTALL_DIR"
echo "Dados armazenados em: $DATA_DIR"
echo ""
echo "Como usar:"
echo "1. Terminal: gerenciador-de-notas-fiscais"
echo "2. Menu de aplicativos: Procure por '$APP_NAME'"
