---
name: verificar
description: Procedimiento obligatorio antes de decir "verificado": typecheck honesto, pruebas, navegador y base de datos.
---
# Verificar un cambio

1. **Typecheck honesto y pruebas**, en primer plano y con tiempo máximo:
   ```bash
   cd frontend && rm -rf node_modules/.tmp && npx tsc --noEmit && timeout 600 npx vitest run
   cd backend && npx tsc --noEmit && timeout 600 npx jest
   ```
2. **Probar en el navegador** con las herramientas de Chrome DevTools (MCP), como lo haría una persona: clics, no llamadas a la API. Consola con 0 errores. Mirar la pantalla del OTRO lado (segundo usuario, segunda pestaña).
3. **Probar con los tipos incómodos** del dominio (archivo, firma, fórmula, lo que en este repo suela romperse).
4. **Comprobar en la base** que lo que dice la pantalla es lo que quedó guardado, con SQL que compare antes y después.
5. **No dejar datos de prueba absurdos** (emojis, nombres de 50 caracteres): rompen pantallas que en producción se ven bien.
6. **Al medir en desarrollo**, recordar que React duplica efectos: contar endpoints distintos, no peticiones.
