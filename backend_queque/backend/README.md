# Backend de Queque (Python)

Ejemplo de cómo conectar el contrato y el frontend que ya están en el repositorio con un backend en Python.
Se coloca en `backend/`, junto a `contrato/` y `frontend/`. Usa FastAPI y SQLite, sin infraestructura extra.

```
Queque/
├── contrato/            ← ya existe; el backend lo LEE, no lo copia
├── frontend/            ← ya existe
├── backend/             ← esto
│   ├── app/
│   │   ├── main.py          API (arranque)            ├── asignacion.py   reglas del README, código puro
│   │   ├── rutas.py         endpoints                 ├── extraccion.py   archivo → texto (un extractor por formato)
│   │   ├── servicios.py     el pipeline paso a paso   ├── limites.py      tope de memoria/tiempo en proceso hijo
│   │   ├── repositorio.py   SQL                       ├── analisis/       modelo local (Ollama) o analizador de prueba
│   │   ├── worker.py        procesa la cola           ├── contrato.py     lee brief.schema.json
│   │   └── ajustes_001.sql  ajustes aditivos al esquema
│   └── tests/               27 pruebas
└── deploy/ollama.compose.yml
```

## Cómo correrlo

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli seed                                   # Moody, GESA y Leo (contrato/personas_ejemplo.sql)

export QUEQUE_ANALIZADOR=falso                           # sin modelo, para desarrollar. Quita esta línea para usar Ollama
uvicorn app.main:crear_app --factory --port 8000         # terminal 1: API y dashboard
python -m app.worker                                     # terminal 2: procesa la cola, un documento a la vez

python -m pytest                                         # pruebas
```

La API y el worker son **procesos distintos** a propósito (README: "si el análisis se pasa de memoria, ese trabajo queda
en error; el dashboard sigue respondiendo"). Comparten la base SQLite en modo WAL.

## El pipeline del README, paso a paso

| Paso del README | Dónde está | Qué hace |
| --- | --- | --- |
| Recepción | `servicios.recibir_solicitud` | Guarda la nota o el archivo y crea el trabajo `pendiente` y el proyecto `nuevo`. Responde 202 al instante |
| Conversión a texto | `extraccion.py` vía `limites.ejecutar_aislado` | TXT, MD, DOCX y PDF con texto. Corre en un proceso hijo con tope de memoria y de tiempo |
| Análisis | `analisis/ollama.py` | Pide un JSON con la forma de `brief.schema.json`; `keep_alive: 0` descarga el modelo al terminar |
| Validación | `servicios._analizar_y_validar` | Valida contra el esquema del contrato, reintenta una vez, y revisa coherencia (áreas y dependencias) |
| Sugerencia | `asignacion.sugerir` | Las 6 reglas del README. La IA no asigna a nadie |
| Confirmación | `servicios.confirmar` | Re-valida el porcentaje libre y recién ahí cambia la ocupación. Acepta cambiar a quién |
| Dashboard | `GET /api/dashboard` | Personas, ocupación, proyecto actual y estado de la cola |

Un documento a la vez se garantiza en la base: `reclamar_trabajo` no toma otro mientras haya uno `procesando`.

## Endpoints ↔ lo que hoy hace `QuequeContext.tsx` con datos de ejemplo

| Frontend (mock) | Endpoint |
| --- | --- |
| `agregarSolicitud(texto, archivo)` | `POST /api/solicitudes` (multipart: `texto`, `archivo`) → `{id, trabajo_id}` |
| `proyectos` | `GET /api/proyectos`, `GET /api/proyectos/{id}` |
| `confirmarAsignacion(id)` | `POST /api/proyectos/{id}/confirmar` (cuerpo opcional `{"cambios":[{"area","persona_id"}]}`) |
| `personas` | `GET /api/personas` |
| `guardarPersona`, `crearPersona` | No hay: las personas llegan por `POST /api/intranet/sync` |
| Dashboard | `GET /api/dashboard` |
| (nuevo) | `POST /api/proyectos/{id}/resugerir`, `POST /api/proyectos/{id}/reintentar`, `GET /api/salud` |

Las respuestas siguen la forma de `frontend/src/types.ts` (se omiten los campos nulos, porque el frontend usa `?`).
Se añaden dos campos que hoy se ignoran: `requiere_revision` y `error`.

### Conectar el frontend

`frontend/vite.config.ts`:
```ts
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
```
Ejemplo de `src/api.ts` para sustituir lo que hace el contexto:
```ts
export async function crearSolicitud(texto: string, archivo?: File): Promise<number> {
  const datos = new FormData()
  datos.append('texto', texto)
  if (archivo) datos.append('archivo', archivo)          // hoy NuevaSolicitud solo guarda el NOMBRE del archivo
  const r = await fetch('/api/solicitudes', { method: 'POST', body: datos })
  if (!r.ok) throw new Error((await r.json()).detail)
  return (await r.json()).id
}
export const confirmar = (id: number) =>
  fetch(`/api/proyectos/${id}/confirmar`, { method: 'POST' }).then(r => r.json())
```
Con el backend real el análisis tarda (segundos o minutos con un modelo en CPU): en vez del `setTimeout` de 1.2 s,
navega a `/proyecto/{id}` de inmediato y consulta `GET /api/proyectos/{id}` cada 2–3 s mientras `estado === 'nuevo'`.

## Dos modos de asignación

El README del repo pide que **una persona confirme**; el documento original del proyecto decía **automática**.
`QUEQUE_CONFIRMACION_AUTOMATICA=0|1` cambia entre ambos sin tocar código. En modo automático, lo dudoso
(confianza baja, incoherencias, porcentaje 0) **no se confirma solo**: queda `sugerido` con `requiere_revision`.

## Ajustes al contrato

`contrato/esquema.sql` se usa tal cual. Encima se aplican solo ajustes **aditivos** (`app/ajustes_001.sql`):

| Ajuste | Por qué |
| --- | --- |
| `tareas.depende_de` | `brief.schema.json` lo trae, pero la tabla no tenía dónde guardarlo |
| `personas.id_externo` (único) | Para actualizar por id de la intranet sin duplicar |
| `personas.proyecto_intranet` | El frontend muestra "proyecto actual" y hoy solo se podría saber de lo que se confirme en Queque |
| índices | Cola y consultas del dashboard |

Dos límites del contrato que el ejemplo rodea y conviene corregir en `contrato/esquema.sql` cuando el equipo lo apruebe:
1. `proyectos.brief_json` es `NOT NULL`, pero el proyecto debe existir antes del análisis. Se guarda `'{}'` hasta tener el brief.
2. `proyectos.estado` no tiene `'error'` (el frontend sí). Se deriva del trabajo. Lo ideal: `brief_json` opcional y `'error'` en el CHECK.

## Recursos de la máquina virtual

- **Memoria al leer archivos:** `limites.py` usa `RLIMIT_AS` (solo Linux). Si se pasa, ese trabajo queda en `error`.
- **CPU y RAM del modelo:** Ollama es otro proceso, así que el tope se pone ahí (`deploy/ollama.compose.yml`: 2 CPU, 4 GB),
  no desde Python. Con 4 GB solo caben modelos de unos 3 000 millones de parámetros cuantizados, y en CPU responden lento:
  por eso el timeout es de 600 s y la cola absorbe la espera.
- Verifica con tu versión de Ollama que acepte `format` con un esquema JSON y `keep_alive`.

## Qué falta (y dónde se agrega)

- Word antiguo (`.doc`), PDF escaneado (OCR), Excel, PowerPoint e imágenes: una función más en `extraccion.EXTRACTORES`.
- Autenticación de usuarios. Hoy solo `/api/intranet/sync` admite un token (`QUEQUE_TOKEN_INTRANET`).
  Los documentos pueden ser confidenciales y `texto_crudo` se guarda sin cifrar.
- Agregar `backend/datos/` al `.gitignore` (ya ignora `*.sqlite3`, pero no la carpeta de archivos subidos).
- Servicios del sistema (systemd o similar) para la API y el worker.
- Medir el modelo definitivo con 20–30 documentos reales etiquetados antes de fiarse de sus áreas.
