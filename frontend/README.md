# Frontend de Queque

Interfaz web de las cinco pantallas: Cola, Nueva solicitud, Proyecto, Dashboard y Equipo.

Por ahora usa datos de ejemplo del contrato (Moody, GESA, Leo e Inventario de farmacia). Todavía no habla con un backend.

## Cómo correrlo

```bash
cd frontend
npm install
npm run dev
```

Abre la URL que imprime Vite, normalmente `http://localhost:5173`.

## Flujo de prueba

1. En **Cola** abre Inventario de farmacia.
2. Confirma la sugerencia a GESA (Moody aparece saltado por estar al 100 %).
3. Ve al **Dashboard** y revisa que la ocupación de GESA subió.
4. En **Nueva solicitud** pega una nota; si menciona farmacia o inventario, reutiliza el brief de ejemplo.
