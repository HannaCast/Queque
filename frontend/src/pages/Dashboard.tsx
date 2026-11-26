import { AvisoError, Esqueleto } from '../components/Estados'
import { Icono, type NombreIcono } from '../components/Icono'
import { OcupacionBar } from '../components/OcupacionBar'
import { useQueque } from '../context/QuequeContext'
import { libreDe } from '../data/mock'

function etiquetaLibre(ocupado: number): { texto: string; clase: string } {
  if (ocupado >= 100) return { texto: 'Al 100 %', clase: 'lleno' }
  if (ocupado <= 0) return { texto: 'Disponible', clase: 'disponible' }
  return { texto: 'Con carga parcial', clase: 'parcial' }
}

interface Metrica {
  etiqueta: string
  valor: string
  detalle: string
  icono: NombreIcono
  tono: 'azul' | 'cian' | 'ambar' | 'verde'
}

export function Dashboard() {
  const { personas, proyectos, cargando, error, refrescar } = useQueque()

  const enCola = proyectos.filter((p) => p.estado === 'nuevo' || p.estado === 'sugerido').length
  const enEspera = proyectos.filter((p) => p.estado === 'en_espera').length
  const asignados = proyectos.filter((p) => p.estado === 'confirmado').length
  const promedio =
    personas.length > 0
      ? Math.round(personas.reduce((suma, p) => suma + p.porcentaje_ocupado, 0) / personas.length)
      : 0
  const conEspacio = personas.filter((p) => p.porcentaje_ocupado < 100).length

  const metricas: Metrica[] = [
    {
      etiqueta: 'En cola',
      valor: String(enCola),
      detalle: 'recién llegados o con sugerencia',
      icono: 'bandeja',
      tono: 'azul',
    },
    {
      etiqueta: 'En espera',
      valor: String(enEspera),
      detalle: 'sin nadie con porcentaje libre',
      icono: 'reloj',
      tono: 'ambar',
    },
    {
      etiqueta: 'Asignados',
      valor: String(asignados),
      detalle: 'proyectos confirmados',
      icono: 'check',
      tono: 'verde',
    },
    {
      etiqueta: 'Ocupación promedio',
      valor: `${promedio}%`,
      detalle: `${conEspacio} de ${personas.length} personas con espacio`,
      icono: 'grafica',
      tono: 'cian',
    },
  ]

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="section-label">Tiempo real</p>
          <h1>Dashboard</h1>
          <p>
            Cómo va cada persona: en qué proyecto está, qué porcentaje tiene
            ocupado y cuánto le queda libre para un proyecto nuevo.
          </p>
        </div>
        <button className="btn btn-secondary" type="button" onClick={() => void refrescar()}>
          <Icono nombre="actualizar" tamano={16} />
          Actualizar
        </button>
      </div>

      {error ? <AvisoError mensaje={error} /> : null}

      {cargando ? (
        <Esqueleto filas={3} alto={120} />
      ) : (
        <>
          <div className="metricas">
            {metricas.map((m) => (
              <article className={`metrica metrica-${m.tono}`} key={m.etiqueta}>
                <span className="metrica-icono">
                  <Icono nombre={m.icono} tamano={20} />
                </span>
                <div>
                  <p className="metrica-etiqueta">{m.etiqueta}</p>
                  <p className="metrica-valor">{m.valor}</p>
                  <p className="metrica-detalle">{m.detalle}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="grid-2">
            {personas.map((persona) => {
              const estado = etiquetaLibre(persona.porcentaje_ocupado)
              const libre = persona.libre ?? libreDe(persona)

              return (
                <article className="person-block" key={persona.id}>
                  <div className="person-top">
                    <div>
                      <h3>{persona.nombre}</h3>
                      <div className="areas">
                        {persona.areas.map((area) => (
                          <span className="chip" key={area}>
                            {area}
                          </span>
                        ))}
                      </div>
                    </div>
                    <span className={`estado-libre ${estado.clase}`}>
                      {estado.texto}
                    </span>
                  </div>

                  <OcupacionBar ocupado={persona.porcentaje_ocupado} />

                  <div>
                    <p className="section-label">Proyecto actual</p>
                    <p style={{ marginTop: '0.35rem' }}>
                      {persona.proyecto_actual ?? 'Sin proyecto confirmado'}
                    </p>
                    <p className="hint" style={{ marginTop: '0.35rem' }}>
                      {libre}% libre para tomar un proyecto nuevo
                    </p>
                  </div>
                </article>
              )
            })}
          </div>
        </>
      )}
    </section>
  )
}
