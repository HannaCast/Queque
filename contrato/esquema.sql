-- Base de Queque.
-- trabajos guarda la solicitud y el brief.
-- personas, habilidades, proyectos, tareas y asignaciones guardan al equipo y la carga.

CREATE TABLE trabajos (
  id INTEGER PRIMARY KEY,
  nombre_archivo TEXT,
  texto_crudo TEXT,
  estado TEXT NOT NULL CHECK (
    estado IN ('pendiente', 'procesando', 'listo', 'error', 'revision')
  ),
  brief_json TEXT,
  error TEXT,
  creado_en TEXT NOT NULL,
  actualizado_en TEXT NOT NULL
);

CREATE TABLE personas (
  id INTEGER PRIMARY KEY,
  nombre TEXT NOT NULL,
  porcentaje_ocupado REAL NOT NULL CHECK (
    porcentaje_ocupado >= 0 AND porcentaje_ocupado <= 100
  ),
  actualizado_en TEXT NOT NULL
);

CREATE TABLE habilidades (
  id INTEGER PRIMARY KEY,
  persona_id INTEGER NOT NULL REFERENCES personas(id),
  area TEXT NOT NULL CHECK (
    area IN ('Software', 'Redes', 'Marketing', 'Mecatrónica')
  ),
  UNIQUE (persona_id, area)
);

CREATE TABLE proyectos (
  id INTEGER PRIMARY KEY,
  trabajo_id INTEGER REFERENCES trabajos(id),
  nombre TEXT NOT NULL,
  resumen TEXT,
  estado TEXT NOT NULL CHECK (
    estado IN ('nuevo', 'sugerido', 'confirmado', 'en_espera')
  ),
  brief_json TEXT NOT NULL,
  creado_en TEXT NOT NULL
);

CREATE TABLE tareas (
  id INTEGER PRIMARY KEY,
  proyecto_id INTEGER NOT NULL REFERENCES proyectos(id),
  titulo TEXT NOT NULL,
  area TEXT NOT NULL,
  prioridad TEXT NOT NULL CHECK (prioridad IN ('alta', 'media', 'baja')),
  estado TEXT NOT NULL CHECK (
    estado IN ('pendiente', 'sugerida', 'confirmada', 'en_espera')
  )
);

CREATE TABLE asignaciones (
  id INTEGER PRIMARY KEY,
  proyecto_id INTEGER NOT NULL REFERENCES proyectos(id),
  tarea_id INTEGER REFERENCES tareas(id),
  persona_id INTEGER NOT NULL REFERENCES personas(id),
  area TEXT NOT NULL,
  porcentaje REAL NOT NULL CHECK (porcentaje >= 0 AND porcentaje <= 100),
  estado TEXT NOT NULL CHECK (estado IN ('sugerida', 'confirmada')),
  motivo TEXT,
  confirmada_en TEXT
);
