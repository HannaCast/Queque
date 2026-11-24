import { Link } from 'react-router-dom'
import { useQueque } from '../context/QuequeContext'
import { etiquetaEstado } from '../data/mock'

export function Cola() {
  const { proyectos, personas, cargando, error, refrescar } = useQueque()

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="section-label">Inicio</p>
          <h1>Cola</h1>
          <p>
            Solicitudes recién llegadas, con sugerencia lista y ya asignadas.
            Desde aquí abres un proyecto o creas una nota nueva.
          </p>
        </div>
        <div className="actions">
          <button className="btn btn-secondary" type="button" onClick={() => void refrescar()}>
            Actualizar
          </button>
          <Link className="btn" to="/nueva">
            Nueva solicitud
          </Link>
        </div>
      </div>

      {error ? <p className="saltado">{error}</p> : null}

      <div className="list">
        {cargando ? (
          <div className="empty panel">Cargando la cola…</div>
        ) : proyectos.length === 0 ? (
          <div className="empty panel">Todavía no hay proyectos en la cola.</div>
        ) : (
          proyectos.map((proyecto) => {
            const asignada = proyecto.sugerencias[0]
            const persona = personas.find((p) => p.id === asignada?.persona_id)

            return (
              <Link key={proyecto.id} className="row" to={`/proyecto/${proyecto.id}`}>
                <div className="row-main">
                  <h3>{proyecto.nombre}</h3>
                  <p>{proyecto.resumen}</p>
                </div>
                <div className="meta">
                  <span className={`chip chip-${proyecto.estado}`}>
                    {etiquetaEstado(proyecto.estado)}
                  </span>
                  {persona ? (
                    <span className="chip">
                      {asignada?.estado === 'confirmada' ? 'Asignado a' : 'Sugerido'}:{' '}
                      {persona.nombre}
                    </span>
                  ) : null}
                </div>
              </Link>
            )
          })
        )}
      </div>
    </section>
  )
}
