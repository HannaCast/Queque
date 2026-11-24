# Análisis de la estructura de Queque

Revisión del repositorio (`develop`, 5 commits, 25 oct – 5 nov 2026).

## Qué hay
- `contrato/`: esquema JSON del brief, un brief de ejemplo, el esquema SQL y tres personas de prueba.
- `frontend/`: React 19 + Vite + TypeScript con cinco pantallas (Cola, Nueva solicitud, Proyecto, Dashboard, Equipo).
  Funciona completo con datos de ejemplo en memoria (`context/QuequeContext.tsx`); no llama a ningún backend.
- `README.md`: pipeline, reglas de asignación y recursos de la máquina virtual.
- No existe `backend/`. Eso es lo que se agrega.

## Lo nuevo frente a lo que se había hablado
| Antes | Ahora (repo) | Efecto |
| --- | --- | --- |
| Asignación automática | Una persona confirma o cambia la sugerencia | **Contradicción por resolver**. El ejemplo soporta ambas con una variable |
| Modelo externo posible | Modelo **local** (`modelos/` y `.ollama/` en el .gitignore) | Resuelve la duda de enviar documentos confidenciales a un tercero |
| Carga en horas | Carga en **porcentaje** (ocupado / libre) | Reglas más simples; `horas_estimadas` ya no decide nada |
| Equipo desde un sistema existente | Llega "desde la intranet" | Hace falta un punto de entrada: `POST /api/intranet/sync` |
| Sin límites de máquina | VM de 4 vCPU y 8 GB; análisis con tope de 2 vCPU y 4 GB | Proceso de análisis separado y con tope |

## Incongruencias encontradas
| # | Hallazgo | Dónde | Propuesta |
| --- | --- | --- | --- |
| 1 | El proyecto de ejemplo "Inventario de farmacia" sugiere a GESA (60 % libre), pero por la regla del README gana Leo (90 % libre, también cubre Software) | `frontend/src/data/mock.ts` | Corregir el dato de ejemplo (el backend sugiere a Leo) |
| 2 | `brief.schema.json` trae `depende_de` por tarea y la tabla `tareas` no tiene dónde guardarlo | `contrato/` | Columna `depende_de` |
| 3 | `proyectos.brief_json` es obligatorio, pero el proyecto debe existir antes del análisis; y `estado` no incluye `error`, que el frontend sí usa | `esquema.sql` ↔ `types.ts` | Hacer `brief_json` opcional y añadir `error` |
| 4 | Las áreas están escritas en 4 archivos (`esquema.sql`, `brief.schema.json`, `types.ts`, `mock.ts`). Agregar una área toca todos | varios | El backend ya lee el catálogo del esquema JSON; el SQL podría pasar a una tabla `areas` |
| 5 | La ocupación la escriben dos fuentes: la confirmación en Queque y la intranet. Si la intranet ya refleja lo confirmado, se contaría doble; si no, la sincronización borra lo confirmado | `personas.porcentaje_ocupado` | Decidir cuál manda. El ejemplo hace que la intranet pise el valor |
| 6 | El README no dice qué pasa si el brief pide 40 % y a la persona le quedan 15 % | reglas de asignación | El ejemplo propone el 15 % y lo explica en el motivo |
| 7 | Dos sugerencias pendientes pueden apuntar a la misma persona (la ocupación no cambia hasta confirmar) | reglas | El ejemplo re-valida al confirmar y ofrece volver a sugerir |
| 8 | `Proyecto.tsx` solo muestra `sugerencias[0]`, pero un proyecto puede pedir varias áreas y varias personas | frontend | Recorrer todas las sugerencias |
| 9 | Equipo permite editar y crear personas, pero el texto dice que llegan solas desde la intranet; se sobrescribirían en la próxima sincronización | frontend | Quitar el botón Editar o marcar esos cambios como locales |
| 10 | `NuevaSolicitud.tsx` guarda solo el nombre del archivo, no el archivo; y no acepta Excel, PowerPoint ni imágenes (el README sí los menciona) | frontend | Guardar el `File`; ampliar `accept` conforme haya extractores |
| 11 | `horas_estimadas` convive con `porcentaje_sugerido` y ninguna regla usa las horas. Un porcentaje de la jornada sin fecha de entrega es una estimación débil para un modelo pequeño | contrato | Decidir si el porcentaje se deriva de horas ÷ semanas disponibles |
| 12 | No hay autenticación en ninguna pantalla y los textos se guardan sin cifrar, con documentos que pueden ser confidenciales | frontend / base | Login por rol y cifrado de la carpeta de datos |
| 13 | `.gitignore` ignora `*.sqlite3` pero no la carpeta donde se guardan los archivos subidos | `.gitignore` | Agregar `backend/datos/` |

## Preguntas para el equipo
1. ¿Confirma una persona (README) o es automática (documento original)?
2. ¿Quién manda sobre el porcentaje ocupado, la intranet o Queque?
3. ¿Qué entrega la intranet (API, base, archivo) y con qué autenticación?
4. ¿Qué modelo local se usará? Con 4 GB de RAM y CPU solamente, el tamaño y el tiempo de respuesta limitan mucho.
5. ¿Cómo se convierte lo que pide el documento en un porcentaje de jornada?
