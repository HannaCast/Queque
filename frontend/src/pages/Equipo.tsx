import { AvisoError, Esqueleto, Vacio } from '../components/Estados'
import { Icono } from '../components/Icono'
import { OcupacionBar } from '../components/OcupacionBar'
import { useQueque } from '../context/QuequeContext'
import { iniciales } from '../utils/texto'

function estadoDe(ocupado: number): { texto: string; clase: string } {
  if (ocupado >= 100) return { texto: 'Al 100 %', clase: 'lleno' }
  if (ocupado <= 0) return { texto: 'Disponible', clase: 'disponible' }
  return { texto: 'Carga parcial', clase: 'parcial' }
}

export function Equipo() {
  const { personas, cargando, error } = useQueque()

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="section-label">Personas</p>
          <h1>Equipo</h1>
          <p>
            Las personas llegan solas desde la intranet. Aquí se ve su área, su
            ocupación y en qué proyecto están.
          </p>
        </div>
      </div>

      {error ? <AvisoError mensaje={error} /> : null}

      {cargando ? (
        <Esqueleto filas={3} alto={150} />
      ) : personas.length === 0 ? (
        <Vacio icono="equipo" titulo="Todavía no hay personas">
          Se agregarán desde la intranet o con <code>python -m app.cli seed</code> en el backend.
        </Vacio>
      ) : (
        <div className="equipo-grid">
          {personas.map((persona) => {
            const estado = estadoDe(persona.porcentaje_ocupado)
            return (
              <article className="persona-card" key={persona.id}>
                <div className="persona-cabecera">
                  <span className="avatar" aria-hidden="true">
                    {iniciales(persona.nombre)}
                  </span>
                  <div className="persona-nombre">
                    <h3>{persona.nombre}</h3>
                    <span className={`estado-libre ${estado.clase}`}>{estado.texto}</span>
                  </div>
                </div>

                <div className="areas">
                  {persona.areas.map((area) => (
                    <span className="chip" key={area}>
                      {area}
                    </span>
                  ))}
                </div>

                <OcupacionBar ocupado={persona.porcentaje_ocupado} />

                <p className="persona-proyecto">
                  <Icono nombre="resumen" tamano={15} />
                  {persona.proyecto_actual ?? 'Sin proyecto confirmado'}
                </p>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
