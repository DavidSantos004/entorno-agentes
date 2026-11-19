# Entorno de trabajo con agentes de IA

Plantilla del entorno con el que desarrollo hoy: varios agentes de Claude Code trabajando en paralelo sobre un mismo repositorio, con reglas que se cargan solo cuando hacen falta, una definición escrita de qué significa "verificado" y bloqueos que pone el harness, no la memoria del agente.

Es una versión genérica de lo que uso en producción en una plataforma de gestión de trabajo con más de 400 tableros. Aquí no hay nada de ese producto: solo la estructura, los scripts y las pruebas, listos para copiar a otro repo.

## La idea en tres frases

1. **El agente propone, yo apruebo.** Cada solicitud la toma un agente en su propia copia del repo y la revisa otro antes de unir.
2. **Lo peligroso lo bloquea el harness.** Un hook corre antes de cada comando de shell y corta lo que no debe pasar, con sus propias pruebas.
3. **El contexto se carga por capas.** `CLAUDE.md` es corto y siempre presente; las reglas de cada área se cargan solo al tocar esa área; la historia de cada decisión se lee bajo demanda.

## Qué hay

| Ruta | Qué es |
|---|---|
| `CLAUDE.md` | Plantilla del archivo de contexto: convenciones, método, estructura de la documentación y topes. |
| `.claude/rules/<area>.md` | Reglas de un área con `paths:`; se cargan solo al tocar esos archivos. Hay un ejemplo. |
| `.claude/skills/verificar/SKILL.md` | Procedimiento que define qué significa "verificado": pruebas, navegador y base de datos. |
| `.claude/hooks/bloqueos.py` | Hook `PreToolUse` de Bash: bloquea push a ramas protegidas, merge de PR y escritura en la base de producción. |
| `.claude/hooks/test_bloqueos.py` | Pruebas del hook: cada bloqueo bloquea y lo de todos los días pasa. |
| `.claude/settings.json` | Conecta el hook y el aviso de topes al arrancar la sesión. |
| `scripts/revisar-claude-md.sh` | Avisa al abrir sesión si `CLAUDE.md` o una regla pasa del tope. |
| `docs/historia/` | Una nota por feature o incidente; nunca se cargan solas. |

## Cómo lo uso con varios agentes

- Cada agente trabaja en un worktree propio sacado de la rama de desarrollo (yo uso Orca, un IDE multiagente, pero sirve `git worktree`).
- Un solo agente verifica en el navegador a la vez, porque hay una sola copia de la aplicación corriendo.
- Cada espera tiene tope: si un agente lleva diez minutos sin entregar, se lee su terminal y se destraba o se relanza. Nadie espera para siempre.
- Las pruebas corren en primer plano con tiempo máximo, nunca en segundo plano esperando un aviso.
- Al cerrar un cambio, en el mismo commit: nota de historia, regla nueva si la dejó, y prueba que falla con el código anterior.

## Probar el hook

```bash
python3 .claude/hooks/test_bloqueos.py
```

## Adaptarlo

1. Cambia `RAMAS_PROTEGIDAS` y `BASE_DE_PRODUCCION` en `bloqueos.py` y en sus pruebas.
2. Escribe un `.claude/rules/<area>.md` por área real del código, con sus `paths:`.
3. Deja en `CLAUDE.md` solo lo que aplica en toda sesión. Si al quitar una línea el agente no se equivoca, esa línea sobra.

David Santos · [davidsantos-eight.vercel.app](https://davidsantos-eight.vercel.app)
