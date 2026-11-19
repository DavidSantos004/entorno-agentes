#!/usr/bin/env bash
# Avisa cuando los archivos de instrucciones de Claude Code crecen más de lo recomendado.
# Recomendación oficial: menos de 200 líneas por archivo; el aviso de Claude Code salta a 150k caracteres.
set -u
cd "$(dirname "$0")/.."
MAX_CHARS=${MAX_CHARS:-20000}
MAX_LINEAS=${MAX_LINEAS:-200}
estado=0
revisar() {
  local f=$1 chars lineas
  [ -f "$f" ] || return 0
  chars=$(wc -c < "$f"); lineas=$(wc -l < "$f")
  if [ "$chars" -gt "$MAX_CHARS" ] || [ "$lineas" -gt "$MAX_LINEAS" ]; then
    echo "AVISO: $f tiene $chars caracteres / $lineas líneas (tope $MAX_CHARS / $MAX_LINEAS). Mover narrativa a docs/historia/ y reglas a .claude/rules/."
    estado=1
  fi
}
revisar CLAUDE.md
for r in .claude/rules/*.md; do revisar "$r"; done
[ "$estado" -eq 0 ] && echo "CLAUDE.md y .claude/rules/ dentro de los topes ($(wc -c < CLAUDE.md) caracteres en CLAUDE.md)."
exit 0
