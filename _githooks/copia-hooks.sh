#!/bin/bash

# Diretório do script
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

# Diretório do Git Hooks
HOOKS_DIR="$SCRIPT_DIR/../.git/hooks"

# Verifica se o diretório .git/hooks existe
if [ ! -d "$HOOKS_DIR" ]; then
    echo "Erro: O diretório .git/hooks não foi encontrado. Execute este script na raiz do repositório."
    exit 1
fi

# Copia todos os arquivos, exceto os scripts de cópia, para o diretório .git/hooks
find "$SCRIPT_DIR" -maxdepth 1 -type f ! -name 'copia-hooks.sh' ! -name 'copia-hooks.ps1' -exec cp {} "$HOOKS_DIR" \;

# Torna os arquivos copiados executáveis
chmod +x "$HOOKS_DIR"/*

echo "Hooks copiados para .git/hooks com sucesso!"
