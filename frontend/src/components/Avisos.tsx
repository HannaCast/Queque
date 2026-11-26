import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'
import { Icono } from './Icono'

type TipoAviso = 'exito' | 'info' | 'error'

interface Aviso {
  id: number
  tipo: TipoAviso
  texto: string
}

type Avisar = (texto: string, tipo?: TipoAviso) => void

const AvisosContext = createContext<Avisar | null>(null)

const DURACION_MS = 3800

export function AvisosProvider({ children }: { children: ReactNode }) {
  const [avisos, setAvisos] = useState<Aviso[]>([])
  const siguiente = useRef(1)

  const cerrar = useCallback((id: number) => {
    setAvisos((prev) => prev.filter((a) => a.id !== id))
  }, [])

  const avisar = useCallback<Avisar>(
    (texto, tipo = 'exito') => {
      const id = siguiente.current++
      setAvisos((prev) => [...prev.slice(-2), { id, tipo, texto }])
      window.setTimeout(() => cerrar(id), DURACION_MS)
    },
    [cerrar],
  )

  return (
    <AvisosContext.Provider value={avisar}>
      {children}
      <div className="avisos" role="status" aria-live="polite">
        {avisos.map((aviso) => (
          <div key={aviso.id} className={`aviso aviso-${aviso.tipo}`}>
            <span className="aviso-icono">
              <Icono
                nombre={aviso.tipo === 'error' ? 'alerta' : aviso.tipo === 'info' ? 'reloj' : 'check'}
                tamano={16}
              />
            </span>
            <span className="aviso-texto">{aviso.texto}</span>
            <button
              type="button"
              className="aviso-cerrar"
              aria-label="Cerrar aviso"
              onClick={() => cerrar(aviso.id)}
            >
              <Icono nombre="cerrar" tamano={14} />
            </button>
          </div>
        ))}
      </div>
    </AvisosContext.Provider>
  )
}

export function useAvisos(): Avisar {
  const ctx = useContext(AvisosContext)
  if (!ctx) {
    throw new Error('useAvisos debe usarse dentro de AvisosProvider')
  }
  return ctx
}
