-- Ajustes ADITIVOS sobre contrato/esquema.sql. No cambian ni borran nada del contrato.
-- Cuando el equipo los apruebe, conviene pasarlos a contrato/esquema.sql.

-- brief.schema.json trae depende_de por tarea, pero la tabla tareas no tenía dónde guardarlo.
ALTER TABLE tareas ADD COLUMN depende_de TEXT NOT NULL DEFAULT '[]';   -- lista JSON de títulos

-- Las personas llegan de la intranet: hace falta su identificador allá para poder actualizarlas.
ALTER TABLE personas ADD COLUMN id_externo TEXT;
CREATE UNIQUE INDEX ux_personas_id_externo ON personas(id_externo);

-- El frontend muestra "proyecto actual"; para quien aún no tiene proyectos en Queque lo informa la intranet.
ALTER TABLE personas ADD COLUMN proyecto_intranet TEXT;

CREATE INDEX ix_trabajos_estado ON trabajos(estado, id);
CREATE INDEX ix_asignaciones_persona ON asignaciones(persona_id, estado);
CREATE INDEX ix_asignaciones_proyecto ON asignaciones(proyecto_id, estado);
