import { OcupacionBar } from '../components/OcupacionBar'
import { useQueque } from '../context/QuequeContext'
import { libreDe } from '../data/mock'

function etiquetaLibre(ocupado: number): { texto: string; clase: string } {
  if (ocupado >= 100) return { texto: 'Al 100 %', clase: 'lleno' }
  if (ocupado <= 0) return { texto: 'Disponible', clase: 'disponible' }
  return { texto: 'Con carga parcial', clase: 'parcial' }
}

export function Dashboard() {
  const { personas } = useQueque()

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
      </div>

      <div className="grid-2">
        {personas.map((persona) => {
          const estado = etiquetaLibre(persona.porcentaje_ocupado)
          const libre = libreDe(persona)

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
    </section>
  )
}
