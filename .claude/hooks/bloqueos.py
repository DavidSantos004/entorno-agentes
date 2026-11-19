#!/usr/bin/env python3
"""Bloqueos del harness para los comandos de shell del agente.

Corre antes de cada comando Bash (hook PreToolUse en .claude/settings.json). Si el
comando cae en un bloqueo, sale con 2 y el motivo en stderr: el harness no lo
ejecuta y le devuelve el motivo al agente. Existe para poder trabajar con varios
agentes, y sin pedir permiso por cada comando, sin depender de que cada agente
recuerde las reglas:

- push a una rama protegida (o desde ella), y cualquier merge de PR;
- escrituras a la base de producción: todo comando que la nombre tiene que ir con
  default_transaction_read_only=on y no puede volver a abrir la escritura.

Pruebas: python3 .claude/hooks/test_bloqueos.py
"""
import json
import os
import re
import shlex
import subprocess
import sys

# Adaptar estas tres constantes al repo.
RAMAS_PROTEGIDAS = {'integracion', 'produccion'}
RAMA_DE_TRABAJO = 'desarrollo'
BASE_DE_PRODUCCION = re.compile(r'rds\.amazonaws\.com|produccion\.ejemplo\.internal', re.I)

SOLO_LECTURA = re.compile(r'default_transaction_read_only\s*=\s*on', re.I)
REABRE_ESCRITURA = re.compile(
    r'read\s+write|default_transaction_read_only\s*(=|to)\s*(off|false|0)|transaction_read_only\s*(=|to)\s*(off|false|0)', re.I)
SEPARADORES = re.compile(r'&&|\|\||;|\||\n')


def segmentos(comando):
    """Los comandos sueltos de una línea compuesta, ya partidos en palabras."""
    for crudo in SEPARADORES.split(comando):
        try:
            palabras = shlex.split(crudo, posix=True)
        except ValueError:
            palabras = crudo.split()
        # Asignaciones de entorno delante (PGOPTIONS=... psql) no cuentan como el programa.
        while palabras and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', palabras[0]):
            palabras = palabras[1:]
        if palabras:
            yield palabras


def subcomando_git(palabras):
    """('push', [argumentos], ruta de -C) si es un git, o None."""
    if not palabras or os.path.basename(palabras[0]) != 'git':
        return None
    i, ruta = 1, None
    while i < len(palabras) and palabras[i].startswith('-'):
        if palabras[i] in ('-C', '-c') and i + 1 < len(palabras):
            if palabras[i] == '-C':
                ruta = palabras[i + 1]
            i += 2
        else:
            i += 1
    if i >= len(palabras):
        return None
    return palabras[i], palabras[i + 1:], ruta


def rama_actual(ruta):
    try:
        return subprocess.run(['git', '-C', ruta or '.', 'branch', '--show-current'],
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ''


def es_rama_protegida(ref):
    destino = ref.lstrip('+').split(':')[-1]
    destino = re.sub(r'^refs/heads/', '', destino)
    return destino in RAMAS_PROTEGIDAS


def motivo_push(args, ruta, cwd):
    protegidas = ' y '.join(sorted(RAMAS_PROTEGIDAS))
    if any(a in ('--all', '--mirror') for a in args):
        return f'git push --all/--mirror sube también {protegidas}.'
    refs = [a for a in args if not a.startswith('-')]
    refspecs = refs[1:]  # git push <remoto> <refspec...>
    for r in refspecs:
        if es_rama_protegida(r):
            return f'git push a {r}: {protegidas} solo las mueve el líder del proyecto; tu PR va a {RAMA_DE_TRABAJO}.'
    if not refspecs:
        rama = rama_actual(ruta or cwd)
        if rama in RAMAS_PROTEGIDAS:
            return f'git push desde la rama {rama}: {protegidas} solo las mueve el líder del proyecto; tu PR va a {RAMA_DE_TRABAJO}.'
    return None


def motivo_merge_pr(palabras):
    if palabras[0] == 'gh' and len(palabras) >= 3 and palabras[1] == 'pr' and palabras[2] == 'merge':
        return 'gh pr merge: los PR los une el líder del proyecto.'
    if palabras[0] == 'gh' and len(palabras) >= 2 and palabras[1] == 'api' and any(re.search(r'/pulls/\d+/merge\b', p) for p in palabras):
        return 'Unir un PR por la API de GitHub: los PR los une el líder del proyecto.'
    return None


def motivo(comando, cwd='.'):
    if BASE_DE_PRODUCCION.search(comando):
        if not SOLO_LECTURA.search(comando):
            return 'Comando contra la base de producción sin PGOPTIONS default_transaction_read_only=on: producción es solo lectura.'
        if REABRE_ESCRITURA.search(comando):
            return 'El comando vuelve a abrir la escritura en la base de producción: producción es solo lectura.'
    for palabras in segmentos(comando):
        m = motivo_merge_pr(palabras)
        if m:
            return m
        g = subcomando_git(palabras)
        if g and g[0] == 'push':
            m = motivo_push(g[1], g[2], cwd)
            if m:
                return m
    return None


def main():
    try:
        entrada = json.load(sys.stdin)
    except Exception:
        return 0
    if entrada.get('tool_name') != 'Bash':
        return 0
    comando = (entrada.get('tool_input') or {}).get('command') or ''
    m = motivo(comando, entrada.get('cwd') or '.')
    if m:
        print(f'BLOQUEADO por .claude/hooks/bloqueos.py: {m}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
