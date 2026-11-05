import { useState, type FormEvent } from 'react'
import { OcupacionBar } from '../components/OcupacionBar'
import { useQueque } from '../context/QuequeContext'
import { AREAS } from '../data/mock'
import type { Area, Persona } from '../types'

export function Equipo() {
  const { personas, guardarPersona } = useQueque()
  const [editando, setEditando] = useState<Persona | null>(null)

  function toggleArea(
    areas: Area[],
    area: Area,
    onChange: (next: Area[]) => void,
  ) {
    if (areas.includes(area)) {
      onChange(areas.filter((item) => item !== area))
    } else {
      onChange([...areas, area])
    }
  }

  function onGuardar(event: FormEvent) {
    event.preventDefault()
    if (!editando || editando.areas.length === 0) return
    guardarPersona(editando)
    setEditando(null)
  }

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

      <div className="stack">
        <div className="list">
          {personas.length === 0 ? (
            <div className="empty panel">
              Todavía no hay personas. Se agregarán desde la intranet.
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
                <button
                  className="btn btn-secondary"
                  type="button"
                  onClick={() => setEditando(persona)}
                >
                  Editar
                </button>
              </div>
            ))
          )}
        </div>

        {editando ? (
          <form className="panel stack" onSubmit={onGuardar}>
            <h2>Editar a {editando.nombre}</h2>
            <div className="field">
              <label htmlFor="nombre-edit">Nombre</label>
              <input
                id="nombre-edit"
                value={editando.nombre}
                onChange={(e) =>
                  setEditando({ ...editando, nombre: e.target.value })
                }
              />
            </div>
            <div className="field">
              <span>Áreas</span>
              <div className="tags-edit">
                {AREAS.map((area) => (
                  <button
                    key={area}
                    type="button"
                    className={`tag-toggle${editando.areas.includes(area) ? ' on' : ''}`}
                    onClick={() =>
                      toggleArea(editando.areas, area, (areas) =>
                        setEditando({ ...editando, areas }),
                      )
                    }
                  >
                    {area}
                  </button>
                ))}
              </div>
            </div>
            <div className="field">
              <label htmlFor="ocupado-edit">Porcentaje ocupado</label>
              <input
                id="ocupado-edit"
                type="number"
                min={0}
                max={100}
                value={editando.porcentaje_ocupado}
                onChange={(e) =>
                  setEditando({
                    ...editando,
                    porcentaje_ocupado: Number(e.target.value),
                  })
                }
              />
            </div>
            <div className="form-actions">
              <button className="btn" type="submit">
                Guardar
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => setEditando(null)}
              >
                Cancelar
              </button>
            </div>
          </form>
        ) : null}
      </div>
    </section>
  )
}
