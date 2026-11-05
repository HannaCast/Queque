import { Link, useParams } from 'react-router-dom'
import { useQueque } from '../context/QuequeContext'
import { etiquetaEstado } from '../data/mock'

export function Proyecto() {
  const { id } = useParams()
  const { proyectos, personas, confirmarAsignacion } = useQueque()
  const proyecto = proyectos.find((p) => p.id === Number(id))

  if (!proyecto) {
    return (
      <section className="page">
        <div className="panel empty">
          No encontramos ese proyecto. <Link to="/">Volver a la cola</Link>
        </div>
      </section>
    )
  }

  const brief = proyecto.brief
  const sugerencia = proyecto.sugerencias[0]
  const persona = personas.find((p) => p.id === sugerencia?.persona_id)
  const yaConfirmado = proyecto.estado === 'confirmado'

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="section-label">Proyecto</p>
          <h1>{proyecto.nombre}</h1>
          <p>{proyecto.resumen}</p>
        </div>
        <span className={`chip chip-${proyecto.estado}`}>
          {etiquetaEstado(proyecto.estado)}
        </span>
      </div>

      <div className="split">
        <article className="panel">
          <h2>Brief</h2>
          {brief ? (
            <div className="brief-grid">
              <div className="brief-item">
                <strong>Resumen</strong>
                <p>{brief.resumen}</p>
              </div>
              <div className="brief-item">
                <strong>Áreas requeridas</strong>
                <ul className="muted-list">
                  {brief.areas_requeridas.map((area) => (
                    <li key={area.area}>
                      {area.area} · {area.porcentaje_sugerido}% sugerido ·
                      confianza {area.confianza}. {area.justificacion}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="brief-item">
                <strong>Tareas</strong>
                <ul className="muted-list">
                  {brief.tareas.map((tarea) => (
                    <li key={tarea.titulo}>
                      {tarea.titulo} ({tarea.area}, {tarea.prioridad})
                    </li>
                  ))}
                </ul>
              </div>
              {brief.supuestos.length > 0 ? (
                <div className="brief-item">
                  <strong>Supuestos</strong>
                  <ul className="muted-list">
                    {brief.supuestos.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {brief.preguntas_pendientes.length > 0 ? (
                <div className="brief-item">
                  <strong>Preguntas pendientes</strong>
                  <ul className="muted-list">
                    {brief.preguntas_pendientes.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {proyecto.texto_crudo ? (
                <div className="brief-item">
                  <strong>Nota original</strong>
                  <p className="hint">{proyecto.texto_crudo}</p>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="hint">Este proyecto todavía no tiene brief.</p>
          )}
        </article>

        <aside className="panel sugerencia">
          <h2>Sugerencia</h2>
          {persona && sugerencia ? (
            <>
              <div className="sugerencia-box">
                <h3>{persona.nombre}</h3>
                <p>
                  Área {sugerencia.area} · carga propuesta {sugerencia.porcentaje}%
                </p>
                <p className="hint" style={{ marginTop: '0.45rem' }}>
                  {sugerencia.motivo}
                </p>
              </div>

              {proyecto.saltados.map((saltado) => {
                const quien = personas.find((p) => p.id === saltado.persona_id)
                return (
                  <div className="saltado" key={saltado.persona_id}>
                    Se saltó a {quien?.nombre ?? 'alguien'}: {saltado.motivo}
                  </div>
                )
              })}

              <div className="actions">
                {!yaConfirmado ? (
                  <button
                    className="btn btn-signal"
                    type="button"
                    onClick={() => confirmarAsignacion(proyecto.id)}
                  >
                    Confirmar asignación
                  </button>
                ) : (
                  <span className="chip chip-confirmado">Ya confirmada</span>
                )}
                <Link className="btn btn-secondary" to="/dashboard">
                  Ver dashboard
                </Link>
              </div>
            </>
          ) : (
            <p className="hint">
              Todavía no hay sugerencia. Si nadie tiene porcentaje libre en el
              área pedida, el proyecto queda en espera.
            </p>
          )}
        </aside>
      </div>
    </section>
  )
}
