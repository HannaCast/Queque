# Frontend de Nextword

Interfaz web de las cinco pantallas: Cola, Nueva solicitud, Proyecto, Dashboard y Equipo.

Habla con el backend por `/api`. En desarrollo, Vite reenvía esas peticiones a `http://localhost:8000`.

## Cómo correrlo

Con la API y el worker ya encendidos:

```bash
cd frontend
npm install
npm run dev
```

Abre la URL que imprime Vite, normalmente `http://localhost:5173`.

## Flujo de prueba

1. En el backend corre `python -m app.cli seed` (Moody, GESA y Leo).
2. En **Nueva solicitud** pega una nota de inventario o farmacia.
3. Abre el proyecto: mientras esté en `nuevo`, la pantalla consulta sola cada pocos segundos.
4. Confirma la sugerencia (debe proponer a Leo, no a Moody).
5. Ve al **Dashboard** y revisa la ocupación.
