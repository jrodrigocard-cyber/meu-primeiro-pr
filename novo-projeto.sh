#!/usr/bin/env bash
# Uso: ./novo-projeto.sh nome [diretorio-destino]
set -euo pipefail
nome="${1:?Uso: $0 nome [diretorio-destino]}"
destino="${2:-$HOME/projetos}/$nome"
origem="$(cd "$(dirname "$0")" && pwd)/template"
[ -e "$destino" ] && { echo "Já existe: $destino" >&2; exit 1; }
mkdir -p "$destino"
cp -r "$origem"/. "$destino"/
sed -i "s/__NOME__/$nome/g" "$destino/CLAUDE.md"
git -C "$destino" init -q
echo "Projeto criado em $destino"
