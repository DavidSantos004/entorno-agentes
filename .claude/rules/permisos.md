---
paths:
  - "backend/src/auth/**"
  - "backend/src/**/*.controller.ts"
---
# Reglas de permisos y acceso

Historia: `docs/historia/F-001.md`.

- **Validación doble**: toda restricción por rol se valida en backend y en frontend; el mensaje del backend llega tal cual a la interfaz.
- **Todo endpoint que devuelve datos de un recurso valida el acceso a ESE recurso**, aunque la pantalla ya lo esconda.
- **La caché de acceso se invalida al compartir o quitar acceso**, no se espera a que caduque.
