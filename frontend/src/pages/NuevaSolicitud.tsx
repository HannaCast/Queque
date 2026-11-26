import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAvisos } from '../components/Avisos'
import { Vacio } from '../components/Estados'
import { useAuth } from '../context/AuthContext'
import { useQueque } from '../context/QuequeContext'
import { mensajeAmigable } from '../utils/errores'

export function NuevaSolicitud() {
  const { agregarSolicitud } = useQueque()
  const { puedeEditar } = useAuth()
  const navigate = useNavigate()
  const avisar = useAvisos()
  const [texto, setTexto] = useState('')
  const [archivo, setArchivo] = useState<File | undefined>()
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!texto.trim() && !archivo) return

    setEnviando(true)
    setError(null)
    try {
      const id = await agregarSolicitud(texto, archivo)
      avisar('Solicitud enviada a la cola')
      navigate(`/proyecto/${id}`)
    } catch (e) {
      setError(mensajeAmigable(e, 'No se pudo enviar la solicitud'))
      setEnviando(false)
    }
  }

  if (!puedeEditar) {
    return (
      <section className="page">
        <div className="page-header">
          <div>
            <p className="section-label">Entrada</p>
            <h1>Nueva solicitud</h1>
          </div>
        </div>
        <Vacio icono="candado" titulo="No tienes permiso para crear solicitudes">
          Tu rol es de consulta. Pide a un coordinador o administrador que la registre.
        </Vacio>
      </section>
    )
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
            disabled={enviando}
          />
          <span className="hint">
            Puede venir desordenado, incompleto o con faltas. Eso es el caso normal.
          </span>
        </div>

        <div className="field">
          <span id="archivo-label">Archivo opcional</span>
          <label
            className={`file-picker${archivo ? ' has-file' : ''}${enviando ? ' is-disabled' : ''}`}
            htmlFor="archivo"
          >
            <input
              id="archivo"
              type="file"
              accept=".txt,.md,.docx,.pdf"
              onChange={(e) => setArchivo(e.target.files?.[0])}
              disabled={enviando}
              aria-labelledby="archivo-label"
            />
            <span className="file-picker-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
                <path
                  d="M12 16V4m0 0 4 4m-4-4-4 4M5 16.5V18a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1.5"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
            <span className="file-picker-copy">
              <strong>{archivo ? archivo.name : 'Seleccionar archivo'}</strong>
              <small>
                {archivo
                  ? 'Haz clic para cambiarlo'
                  : 'TXT, MD, DOCX o PDF con texto'}
              </small>
            </span>
          </label>
        </div>

        {error ? <p className="saltado">{error}</p> : null}

        {enviando ? (
          <div className="analizando" role="status" aria-live="polite">
            <strong>Enviando a la cola…</strong>
            <span>El análisis sigue en el worker; la pantalla del proyecto se actualiza sola.</span>
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
