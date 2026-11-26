-- Ajustes ADITIVOS para el inicio de sesión (punto 12 de docs/ANALISIS_ESTRUCTURA.md: "Login por rol").
-- No cambian ni borran nada de contrato/esquema.sql.

-- Quién puede entrar a Queque. No confundir con "personas": esas llegan de la intranet y se asignan a proyectos.
--   admin        todo (y, más adelante, gestionar usuarios)
--   coordinador  crea solicitudes y confirma asignaciones
--   consulta     solo ve la cola, el dashboard y el equipo
CREATE TABLE usuarios (
  id INTEGER PRIMARY KEY,
  correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
  nombre TEXT NOT NULL,
  hash_contrasena TEXT NOT NULL,                       -- scrypt con sal; nunca la contraseña en claro
  rol TEXT NOT NULL CHECK (rol IN ('admin', 'coordinador', 'consulta')),
  activo INTEGER NOT NULL DEFAULT 1,
  intentos_fallidos INTEGER NOT NULL DEFAULT 0,
  bloqueado_hasta TEXT,                                -- ISO en UTC; NULL = sin bloqueo
  creado_en TEXT NOT NULL
);

-- Una fila por sesión abierta. Se guarda el SHA-256 del token, no el token: si alguien copia la base, no puede usarlas.
CREATE TABLE sesiones (
  token_hash TEXT PRIMARY KEY,
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  creada_en TEXT NOT NULL,
  expira_en TEXT NOT NULL                              -- ISO en UTC
);

CREATE INDEX ix_sesiones_usuario ON sesiones(usuario_id);
CREATE INDEX ix_sesiones_expira ON sesiones(expira_en);
