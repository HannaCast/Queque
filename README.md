# Queque

Sistema interno para recibir una solicitud de proyecto, convertirla en un brief y sugerir a quién asignarla según habilidad y porcentaje libre.

La aplicación corre en una máquina virtual. El análisis de cada documento tiene un tope de CPU y de RAM, y solo usa ese tope mientras procesa el archivo. El dashboard muestra, en tiempo real, cómo va cada persona: en qué proyecto está, qué porcentaje tiene ocupado y qué porcentaje le queda libre para un proyecto nuevo.

## Qué hace

1. Entra una solicitud en texto libre o en archivo (Word, PDF, Excel, PowerPoint, TXT, imagen o escaneo).
2. El sistema extrae el texto y un modelo local devuelve un brief: título, resumen, áreas, tareas, supuestos y preguntas pendientes.
3. El código sugiere personas. La IA no asigna a nadie.
4. Una persona confirma o cambia la sugerencia. Hasta esa confirmación, la ocupación no cambia.
5. El dashboard se actualiza con el proyecto y el porcentaje libre.

## Reglas de asignación

- Solo entran personas que cubren un área pedida por el brief.
- Quien está al 100 % no recibe otro proyecto.
- Entre quienes sí pueden, se propone a quien tiene más porcentaje libre.
- Si empatan, se propone a quien lleva más tiempo sin un proyecto nuevo.
- Si nadie puede, la tarea queda en espera.
- Un proyecto puede pedir varias áreas y, por lo tanto, varias personas.

Las áreas del catálogo inicial son Software, Redes, Marketing y Mecatrónica.

## Pantallas

| Pantalla | Para qué sirve |
| --- | --- |
| Cola | Proyectos recién llegados, con sugerencia lista y ya asignados |
| Nueva solicitud | Pegar la nota o subir el archivo |
| Proyecto | Brief, áreas, sugerencia, a quién se saltó, y confirmar o cambiar |
| Dashboard | Ocupación, proyecto actual y porcentaje libre de cada persona |
| Equipo | Personas, áreas y ocupación. Llegan desde la intranet |

## Cómo está armado

El flujo es un pipeline. Los pasos van en este orden: recepción, conversión a texto, análisis, validación, sugerencia, confirmación y dashboard.

La aplicación, la cola, la base y el dashboard permanecen encendidos. El modelo arranca cuando hay un documento pendiente y se apaga al terminar. Se procesa un documento a la vez.

Punto de partida de la máquina virtual, a confirmar en el equipo donde se instale:

| Pieza | CPU | RAM | Cuándo corre |
| --- | --- | --- | --- |
| Máquina virtual | 4 vCPU | 8 GB | Siempre |
| App, cola, base y dashboard | 1 vCPU | 2 GB | Siempre |
| Análisis del documento | 2 vCPU | 4 GB | Solo mientras hay un documento en proceso |
| Margen del sistema | 1 vCPU | 2 GB | Sistema operativo de la virtual |

Si el análisis se pasa de memoria, ese trabajo queda en error. El dashboard sigue respondiendo.

## Repositorio

| Ruta | Contenido |
| --- | --- |
| `frontend/` | Interfaz web de las cinco pantallas |
| `backend/` | API, worker, asignación y análisis |
| `deploy/` | Compose de Ollama con tope de CPU y RAM |
| `contrato/brief.schema.json` | Forma del brief que devuelve la IA |
| `contrato/ejemplo_farmacia.json` | Brief de ejemplo: inventario de farmacia |
| `contrato/esquema.sql` | Tablas de la base |
| `contrato/personas_ejemplo.sql` | Personas de prueba: Moody, GESA y Leo |

`trabajos` guarda la nota y el brief. `personas`, `habilidades`, `proyectos`, `tareas` y `asignaciones` guardan al equipo, la carga y la sugerencia.

## Cómo correrlo

Terminal 1 — API:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli seed
export QUEQUE_ANALIZADOR=falso
uvicorn app.main:crear_app --factory --port 8000
```

Terminal 2 — worker (procesa la cola):

```bash
cd backend
source .venv/bin/activate
export QUEQUE_ANALIZADOR=falso
python -m app.worker
```

Terminal 3 — frontend:

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`. Vite reenvía `/api` al backend en el puerto 8000.

## Primera versión

En la primera versión entran la nota pegada, el brief, el catálogo de personas, la sugerencia, la confirmación, la cola y el dashboard.

Lectura de Word antiguo, PDF escaneado, Excel y PowerPoint, y el modelo local definitivo, se agregan sobre esta misma base.
