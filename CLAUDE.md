# CLAUDE.md

Contexto mínimo para Claude Code. Se carga en cada sesión, así que aquí va solo lo que aplica siempre. El resto vive en capas que se cargan bajo demanda (ver **Estructura de la documentación**).

## Qué es este repo

Una frase. Stack en una línea. Enlace al repo.

## Flujo de ramas

| Rama | Uso |
|---|---|
| `desarrollo` | Aquí se programa el día a día. Cada agente saca su rama de aquí y vuelve aquí. |
| `integracion` | Lo aprobado se junta aquí antes de salir. |
| `produccion` | De aquí despliega el workflow. Solo la mueve el líder del proyecto. |

## Convenciones

1. Nada falla en silencio: una operación o reintenta o lo dice con el motivo. Un `catch {}` vacío es un bug.
2. Nada se borra sin vuelta atrás.
3. Toda regla nueva lleva una prueba que FALLA con el código anterior.
4. Lo que ya funciona en producción no se rediseña: antes de tocar algo, `git diff origin/produccion -- <archivo>`.

## Método

- Medir antes de tocar: perfil en el navegador, `EXPLAIN` y conteo de consultas en la base.
- Verificar en el navegador antes de decir "verificado": ver `/verificar`.
- Investigar cómo lo resuelven los productos de referencia antes de diseñar algo que ya existe.
- Al cerrar: nota en `docs/historia/`, regla en `.claude/rules/<area>.md`, como máximo una línea aquí.

## Varios agentes a la vez

- Cada agente en su worktree, sacado de `desarrollo` y de vuelta a `desarrollo`.
- Solo un agente verifica en el navegador a la vez; los demás se limitan a typecheck y pruebas.
- Pruebas en primer plano con tiempo máximo. Nadie espera para siempre una respuesta.
- Los bloqueos (push a ramas protegidas, merge de PR, escritura en producción) los pone el harness: `.claude/hooks/bloqueos.py`.

## Estructura de la documentación (obligatoria)

| Qué | Dónde | Cuándo se carga |
|---|---|---|
| Lo que aplica en toda sesión | `CLAUDE.md` | Siempre. Tope: 200 líneas / 20.000 caracteres |
| Reglas de un área, una frase cada una | `.claude/rules/<area>.md` con `paths:` | Solo al tocar archivos de esa área |
| Historia de cada feature o incidente | `docs/historia/F-0xx.md` | Nunca sola; con `grep` cuando hace falta el porqué |
| Procedimientos de varios pasos | `.claude/skills/<nombre>/SKILL.md` | Al invocar `/<nombre>` |

Prohibido: narrativa aquí, una regla en dos archivos, reglas vigentes solo dentro de una nota de historia. `scripts/revisar-claude-md.sh` avisa al abrir sesión si algo pasa del tope.

## Mantenimiento

Antes de añadir una línea aquí: "¿si la quito, el agente se equivoca?". Si no, va a historia o se borra.
