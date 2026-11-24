import { OcupacionBar } from '../components/OcupacionBar'
import { useQueque } from '../context/QuequeContext'

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

      {error ? <p className="saltado">{error}</p> : null}

      <div className="list">
        {cargando ? (
          <div className="empty panel">Cargando el equipo…</div>
        ) : personas.length === 0 ? (
          <div className="empty panel">
            Todavía no hay personas. Se agregarán desde la intranet o con{' '}
            <code>python -m app.cli seed</code> en el backend.
          </div>
        ) : (
          personas.map((persona) => (
            <div className="row" key={persona.id}>
              <div className="row-main">
                <h3>{persona.nombre}</h3>
                <p>
                  {persona.areas.join(' · ')}
                  {persona.proyecto_actual
                    ? ` · ${persona.proyecto_actual}`
                    : ''}
                </p>
                <div style={{ marginTop: '0.75rem', maxWidth: 280 }}>
                  <OcupacionBar ocupado={persona.porcentaje_ocupado} />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  )
}
