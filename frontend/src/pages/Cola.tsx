import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AvisoError, Esqueleto, Vacio } from '../components/Estados'
import { Icono } from '../components/Icono'
import { useAuth } from '../context/AuthContext'
import { useQueque } from '../context/QuequeContext'
import { etiquetaEstado } from '../data/mock'
import type { EstadoProyecto } from '../types'

type Filtro = 'todos' | EstadoProyecto

const pestanas: { valor: Filtro; etiqueta: string }[] = [
  { valor: 'todos', etiqueta: 'Todos' },
  { valor: 'nuevo', etiqueta: 'Recién llegados' },
  { valor: 'sugerido', etiqueta: 'Con sugerencia' },
  { valor: 'en_espera', etiqueta: 'En espera' },
  { valor: 'confirmado', etiqueta: 'Asignados' },
  { valor: 'error', etiqueta: 'Con error' },
]

export function Cola() {
  const { proyectos, personas, cargando, error, refrescar } = useQueque()
  const { puedeEditar } = useAuth()
  const [filtro, setFiltro] = useState<Filtro>('todos')
  const [busqueda, setBusqueda] = useState('')

  const contar = (valor: Filtro) =>
    valor === 'todos' ? proyectos.length : proyectos.filter((p) => p.estado === valor).length

  const termino = busqueda.trim().toLowerCase()
  const visibles = proyectos.filter((p) => {
    if (filtro !== 'todos' && p.estado !== filtro) return false
    if (!termino) return true
    return `${p.nombre} ${p.resumen}`.toLowerCase().includes(termino)
  })

  // "Con error" solo aparece cuando hay alguno, para no llenar la barra de pestañas vacías.
  const pestanasVisibles = pestanas.filter(
    (p) => p.valor !== 'error' || contar('error') > 0 || filtro === 'error',
  )

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
            <Icono nombre="actualizar" tamano={16} />
            Actualizar
          </button>
          {puedeEditar ? (
            <Link className="btn" to="/nueva">
              <Icono nombre="nueva" tamano={16} />
              Nueva solicitud
            </Link>
          ) : null}
        </div>
      </div>

      {error ? <AvisoError mensaje={error} /> : null}

      <div className="toolbar">
        <div className="pestanas" role="tablist" aria-label="Filtrar por estado">
          {pestanasVisibles.map((p) => (
            <button
              key={p.valor}
              type="button"
              role="tab"
              aria-selected={filtro === p.valor}
              className={`pestana${filtro === p.valor ? ' activa' : ''}`}
              onClick={() => setFiltro(p.valor)}
            >
              {p.etiqueta}
              <span className="pestana-contador">{contar(p.valor)}</span>
            </button>
          ))}
        </div>
        <label className="buscador">
          <Icono nombre="buscar" tamano={16} />
          <input
            type="search"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar proyecto…"
            aria-label="Buscar proyecto por nombre o resumen"
          />
        </label>
      </div>

      {cargando ? (
        <Esqueleto filas={4} />
      ) : proyectos.length === 0 ? (
        <Vacio icono="bandeja" titulo="Todavía no hay proyectos en la cola">
          {puedeEditar ? (
            <>
              Crea una <Link to="/nueva">nueva solicitud</Link> para empezar.
            </>
          ) : (
            'Cuando lleguen solicitudes aparecerán aquí.'
          )}
        </Vacio>
      ) : visibles.length === 0 ? (
        <Vacio icono="buscar" titulo="Sin resultados">
          Ningún proyecto coincide con el filtro o la búsqueda.
        </Vacio>
      ) : (
        <div className="list">
          {visibles.map((proyecto) => {
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
          })}
        </div>
      )}
    </section>
  )
}
