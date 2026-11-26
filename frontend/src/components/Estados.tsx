import type { ReactNode } from 'react'
import { Icono, type NombreIcono } from './Icono'

export function Esqueleto({ filas = 3, alto = 76 }: { filas?: number; alto?: number }) {
  return (
    <div className="list" aria-busy="true" aria-label="Cargando">
      {Array.from({ length: filas }, (_, i) => (
        <div key={i} className="esqueleto" style={{ height: alto }}>
          <span className="esqueleto-linea" style={{ width: '45%' }} />
          <span className="esqueleto-linea corta" style={{ width: '70%' }} />
        </div>
      ))}
    </div>
  )
}

interface VacioProps {
  icono: NombreIcono
  titulo: string
  children?: ReactNode
}

export function Vacio({ icono, titulo, children }: VacioProps) {
  return (
    <div className="empty panel">
      <span className="empty-icono">
        <Icono nombre={icono} tamano={26} />
      </span>
      <strong>{titulo}</strong>
      {children ? <p>{children}</p> : null}
    </div>
  )
}

export function AvisoError({ mensaje }: { mensaje: string }) {
  return (
    <div className="error-box" role="alert">
      <span className="error-box-icono">
        <Icono nombre="sinConexion" tamano={20} />
      </span>
      <div>
        <strong>No se pudo cargar la información</strong>
        <p>{mensaje}</p>
      </div>
    </div>
  )
}
