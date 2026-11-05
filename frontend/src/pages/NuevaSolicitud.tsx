import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueque } from '../context/QuequeContext'

export function NuevaSolicitud() {
  const { agregarSolicitud } = useQueque()
  const navigate = useNavigate()
  const [texto, setTexto] = useState('')
  const [archivo, setArchivo] = useState<string | undefined>()
  const [analizando, setAnalizando] = useState(false)

  function onFileChange(fileList: FileList | null) {
    const file = fileList?.[0]
    setArchivo(file?.name)
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!texto.trim() && !archivo) return

    setAnalizando(true)
    window.setTimeout(() => {
      const id = agregarSolicitud(
        texto.trim() || `Archivo recibido: ${archivo}`,
        archivo,
      )
      navigate(`/proyecto/${id}`)
    }, 1200)
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <p className="section-label">Entrada</p>
          <h1>Nueva solicitud</h1>
          <p>
            Pega la nota cruda o sube el archivo. No hace falta un formato previo:
            el sistema la lee y arma el brief.
          </p>
        </div>
      </div>

      <form className="panel stack" onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="nota">Nota del proyecto</label>
          <textarea
            id="nota"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Ejemplo: hay que hacer un sistema de inventarios para una farmacia..."
            disabled={analizando}
          />
          <span className="hint">
            Puede venir desordenado, incompleto o con faltas. Eso es el caso normal.
          </span>
        </div>

        <div className="field">
          <label htmlFor="archivo">Archivo opcional</label>
          <input
            id="archivo"
            type="file"
            accept=".txt,.doc,.docx,.pdf,.md"
            onChange={(e) => onFileChange(e.target.files)}
            disabled={analizando}
          />
          {archivo ? <span className="hint">Seleccionado: {archivo}</span> : null}
        </div>

        {analizando ? (
          <div className="analizando" role="status" aria-live="polite">
            <strong>Analizando el documento…</strong>
            <span>Usando solo el cupo de CPU y RAM del análisis.</span>
            <div className="analizando-bar">
              <span />
            </div>
          </div>
        ) : (
          <div className="form-actions">
            <button
              className="btn"
              type="submit"
              disabled={!texto.trim() && !archivo}
            >
              Enviar a la cola
            </button>
          </div>
        )}
      </form>
    </section>
  )
}
