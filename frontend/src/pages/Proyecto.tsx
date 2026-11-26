import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAvisos } from '../components/Avisos'
import { Icono, type NombreIcono } from '../components/Icono'
import { useAuth } from '../context/AuthContext'
import { useQueque } from '../context/QuequeContext'
import { etiquetaEstado } from '../data/mock'
import type { EstadoProyecto } from '../types'
import { mensajeAmigable } from '../utils/errores'

type EstadoPaso = 'hecho' | 'actual' | 'pendiente' | 'alerta' | 'error'

interface Paso {
  titulo: string
  detalle: string
  estado: EstadoPaso
}

function pasosDe(estado: EstadoProyecto): Paso[] {
  const recibido: Paso = { titulo: 'Recibido', detalle: 'Nota en la cola', estado: 'hecho' }
  switch (estado) {
    case 'nuevo':
      return [
        recibido,
        { titulo: 'Analizado', detalle: 'Leyendo la nota…', estado: 'actual' },
        { titulo: 'Sugerido', detalle: 'Esperando el brief', estado: 'pendiente' },
        { titulo: 'Confirmado', detalle: 'Sin asignar', estado: 'pendiente' },
      ]
    case 'error':
      return [
        recibido,
        { titulo: 'Analizado', detalle: 'El análisis falló', estado: 'error' },
        { titulo: 'Sugerido', detalle: 'Sin brief', estado: 'pendiente' },
        { titulo: 'Confirmado', detalle: 'Sin asignar', estado: 'pendiente' },
      ]
    case 'en_espera':
      return [
        recibido,
        { titulo: 'Analizado', detalle: 'Brief listo', estado: 'hecho' },
        { titulo: 'Sugerido', detalle: 'En espera: nadie libre', estado: 'alerta' },
        { titulo: 'Confirmado', detalle: 'Sin asignar', estado: 'pendiente' },
      ]
    case 'sugerido':
      return [
        recibido,
        { titulo: 'Analizado', detalle: 'Brief listo', estado: 'hecho' },
        { titulo: 'Sugerido', detalle: 'Falta confirmar', estado: 'actual' },
        { titulo: 'Confirmado', detalle: 'Sin asignar', estado: 'pendiente' },
      ]
    case 'confirmado':
      return [
        recibido,
        { titulo: 'Analizado', detalle: 'Brief listo', estado: 'hecho' },
        { titulo: 'Sugerido', detalle: 'Persona elegida', estado: 'hecho' },
        { titulo: 'Confirmado', detalle: 'Asignación hecha', estado: 'hecho' },
      ]
  }
}

function iconoPaso(estado: EstadoPaso, numero: number) {
  if (estado === 'hecho') return <Icono nombre="check" tamano={15} />
  if (estado === 'error' || estado === 'alerta') return <Icono nombre="alerta" tamano={15} />
  return numero
}

const NOTA_LARGA_CARACTERES = 600
const NOTA_LARGA_LINEAS = 10

function NotaOriginal({ texto }: { texto: string }) {
  const [abierta, setAbierta] = useState(false)
  // Une los saltos de Windows (\r\n) y deja como máximo un renglón en blanco seguido.
  const limpio = texto.replace(/\r\n?/g, '\n').replace(/\n{3,}/g, '\n\n').trim()
  const larga =
    limpio.length > NOTA_LARGA_CARACTERES || limpio.split('\n').length > NOTA_LARGA_LINEAS

  return (
    <>
      <p className={`hint nota-original${larga && !abierta ? ' recortada' : ''}`}>{limpio}</p>
      {larga ? (
        <button
          type="button"
          className="nota-toggle"
          onClick={() => setAbierta(!abierta)}
          aria-expanded={abierta}
        >
          {abierta ? 'Ver menos' : `Ver nota completa (${limpio.length.toLocaleString('es-MX')} caracteres)`}
        </button>
      ) : null}
    </>
  )
}

function SoloConsulta() {
  return (
    <p className="solo-consulta">
      <Icono nombre="candado" tamano={15} />
      Tu rol es de consulta: un coordinador o administrador hace los cambios.
    </p>
  )
}

function TituloBrief({ icono, children }: { icono: NombreIcono; children: string }) {
  return (
    <strong className="brief-titulo">
      <span className="brief-icono">
        <Icono nombre={icono} tamano={15} />
      </span>
      {children}
    </strong>
  )
}

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
  const { puedeEditar } = useAuth()
  const avisar = useAvisos()
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

  async function correr(accion: () => Promise<void>, exito: string) {
    setOcupado(true)
    setAccionError(null)
    try {
      await accion()
      avisar(exito)
    } catch (e) {
      const mensaje = mensajeAmigable(e)
      setAccionError(mensaje)
      avisar(mensaje, 'error')
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

      <ol className="pasos" aria-label="Avance del proyecto">
        {pasosDe(proyecto.estado).map((paso, i) => (
          <li key={paso.titulo} className={`paso paso-${paso.estado}`}>
            <span className="paso-marca">{iconoPaso(paso.estado, i + 1)}</span>
            <span className="paso-texto">
              <strong>{paso.titulo}</strong>
              <small>{paso.detalle}</small>
            </span>
          </li>
        ))}
      </ol>

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
                <TituloBrief icono="resumen">Resumen</TituloBrief>
                <p>{brief.resumen}</p>
              </div>
              <div className="brief-item">
                <TituloBrief icono="areas">Áreas requeridas</TituloBrief>
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
                <TituloBrief icono="tareas">Tareas</TituloBrief>
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
                  <TituloBrief icono="supuestos">Supuestos</TituloBrief>
                  <ul className="muted-list">
                    {brief.supuestos.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {brief.preguntas_pendientes.length > 0 ? (
                <div className="brief-item">
                  <TituloBrief icono="preguntas">Preguntas pendientes</TituloBrief>
                  <ul className="muted-list">
                    {brief.preguntas_pendientes.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {proyecto.texto_crudo ? (
                <div className="brief-item">
                  <TituloBrief icono="nota">Nota original</TituloBrief>
                  <NotaOriginal texto={proyecto.texto_crudo} />
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

              {!puedeEditar && !yaConfirmado ? <SoloConsulta /> : null}
              <div className="actions">
                {!yaConfirmado && puedeEditar ? (
                  <>
                    <button
                      className="btn btn-signal"
                      type="button"
                      disabled={ocupado}
                      onClick={() =>
                        void correr(() => confirmarAsignacion(proyecto.id), 'Asignación confirmada')
                      }
                    >
                      Confirmar asignación
                    </button>
                    <button
                      className="btn btn-secondary"
                      type="button"
                      disabled={ocupado}
                      onClick={() => void correr(() => resugerir(proyecto.id), 'Se generó una nueva sugerencia')}
                    >
                      Volver a sugerir
                    </button>
                  </>
                ) : yaConfirmado ? (
                  <span className="chip chip-confirmado">
                    <Icono nombre="check" tamano={14} /> Ya confirmada
                  </span>
                ) : null}
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
              {!puedeEditar && (proyecto.estado === 'error' || proyecto.estado === 'en_espera') ? (
                <SoloConsulta />
              ) : null}
              <div className="actions">
                {proyecto.estado === 'error' && puedeEditar ? (
                  <button
                    className="btn"
                    type="button"
                    disabled={ocupado}
                    onClick={() => void correr(() => reintentar(proyecto.id), 'Análisis reenviado a la cola')}
                  >
                    Reintentar análisis
                  </button>
                ) : null}
                {proyecto.estado === 'en_espera' && puedeEditar ? (
                  <button
                    className="btn btn-secondary"
                    type="button"
                    disabled={ocupado}
                    onClick={() => void correr(() => resugerir(proyecto.id), 'Se generó una nueva sugerencia')}
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
