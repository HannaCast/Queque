import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQueque } from '../context/QuequeContext'
import { etiquetaEstado } from '../data/mock'

export function Proyecto() {
  const { id } = useParams()
  const {
    proyectos,
    personas,
    confirmarAsignacion,
    resugerir,
    reintentar,
    obtenerProyecto,
  } = useQueque()
  const proyectoId = Number(id)
  const proyecto = proyectos.find((p) => p.id === proyectoId)
  const [accionError, setAccionError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  useEffect(() => {
    if (!Number.isFinite(proyectoId)) return
    let vivo = true
    let timer: number | undefined

    async function consultar() {
      try {
        const actual = await obtenerProyecto(proyectoId)
        if (!vivo) return
        if (actual.estado === 'nuevo') {
          timer = window.setTimeout(consultar, 2500)
        }
      } catch {
        if (vivo) timer = window.setTimeout(consultar, 4000)
      }
    }

    if (!proyecto || proyecto.estado === 'nuevo') {
      void consultar()
    }

    return () => {
      vivo = false
      if (timer) window.clearTimeout(timer)
    }
  }, [proyectoId, proyecto?.estado, obtenerProyecto])

  if (!proyecto) {
    return (
      <section className="page">
        <div className="panel empty">
          Cargando el proyecto… Si no aparece,{' '}
          <Link to="/">vuelve a la cola</Link>.
        </div>
      </section>
    )
  }

  const brief = proyecto.brief
  const yaConfirmado = proyecto.estado === 'confirmado'
  const analizando = proyecto.estado === 'nuevo'

  async function correr(accion: () => Promise<void>) {
    setOcupado(true)
    setAccionError(null)
    try {
      await accion()
    } catch (e) {
      setAccionError(e instanceof Error ? e.message : 'No se pudo completar la acción')
    } finally {
      setOcupado(false)
    }
  }

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

      {analizando ? (
        <div className="analizando" role="status" aria-live="polite" style={{ marginBottom: '1rem' }}>
          <strong>Analizando el documento…</strong>
          <span>El worker está leyendo la nota. Esta pantalla se actualiza sola.</span>
          <div className="analizando-bar">
            <span />
          </div>
        </div>
      ) : null}

      {proyecto.estado === 'error' ? (
        <div className="saltado" style={{ marginBottom: '1rem' }}>
          Error de análisis: {proyecto.error || 'sin detalle'}
        </div>
      ) : null}

      {proyecto.requiere_revision ? (
        <div className="sugerencia-box" style={{ marginBottom: '1rem' }}>
          Este brief pide revisión humana (confianza baja o incoherencias).
        </div>
      ) : null}

      {accionError ? <p className="saltado">{accionError}</p> : null}

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
            <p className="hint">
              {analizando
                ? 'Todavía no hay brief. Esperando al análisis.'
                : 'Este proyecto todavía no tiene brief.'}
            </p>
          )}
        </article>

        <aside className="panel sugerencia">
          <h2>Sugerencia</h2>
          {proyecto.sugerencias.length > 0 ? (
            <>
              {proyecto.sugerencias.map((sugerencia) => {
                const persona = personas.find((p) => p.id === sugerencia.persona_id)
                return (
                  <div className="sugerencia-box" key={`${sugerencia.area}-${sugerencia.persona_id}`}>
                    <h3>{persona?.nombre ?? `Persona ${sugerencia.persona_id}`}</h3>
                    <p>
                      Área {sugerencia.area} · carga propuesta {sugerencia.porcentaje}%
                    </p>
                    <p className="hint" style={{ marginTop: '0.45rem' }}>
                      {sugerencia.motivo}
                    </p>
                  </div>
                )
              })}

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
                  <>
                    <button
                      className="btn btn-signal"
                      type="button"
                      disabled={ocupado}
                      onClick={() =>
                        void correr(() => confirmarAsignacion(proyecto.id))
                      }
                    >
                      Confirmar asignación
                    </button>
                    <button
                      className="btn btn-secondary"
                      type="button"
                      disabled={ocupado}
                      onClick={() => void correr(() => resugerir(proyecto.id))}
                    >
                      Volver a sugerir
                    </button>
                  </>
                ) : (
                  <span className="chip chip-confirmado">Ya confirmada</span>
                )}
                <Link className="btn btn-secondary" to="/dashboard">
                  Ver dashboard
                </Link>
              </div>
            </>
          ) : (
            <div className="stack">
              <p className="hint">
                {proyecto.estado === 'en_espera'
                  ? 'Nadie tiene porcentaje libre en el área pedida. El proyecto queda en espera.'
                  : proyecto.estado === 'error'
                    ? 'No hay sugerencia porque el análisis falló.'
                    : 'Todavía no hay sugerencia.'}
              </p>
              <div className="actions">
                {proyecto.estado === 'error' ? (
                  <button
                    className="btn"
                    type="button"
                    disabled={ocupado}
                    onClick={() => void correr(() => reintentar(proyecto.id))}
                  >
                    Reintentar análisis
                  </button>
                ) : null}
                {proyecto.estado === 'en_espera' ? (
                  <button
                    className="btn btn-secondary"
                    type="button"
                    disabled={ocupado}
                    onClick={() => void correr(() => resugerir(proyecto.id))}
                  >
                    Volver a sugerir
                  </button>
                ) : null}
              </div>
            </div>
          )}
        </aside>
      </div>
    </section>
  )
}
