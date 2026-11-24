import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import * as api from '../api'
import type { Persona, Proyecto } from '../types'

interface QuequeContextValue {
  personas: Persona[]
  proyectos: Proyecto[]
  cargando: boolean
  error: string | null
  refrescar: () => Promise<void>
  agregarSolicitud: (texto: string, archivo?: File) => Promise<number>
  confirmarAsignacion: (proyectoId: number) => Promise<void>
  resugerir: (proyectoId: number) => Promise<void>
  reintentar: (proyectoId: number) => Promise<void>
  obtenerProyecto: (proyectoId: number) => Promise<Proyecto>
}

const QuequeContext = createContext<QuequeContextValue | null>(null)

export function QuequeProvider({ children }: { children: ReactNode }) {
  const [personas, setPersonas] = useState<Persona[]>([])
  const [proyectos, setProyectos] = useState<Proyecto[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refrescar = useCallback(async () => {
    const [listaPersonas, listaProyectos] = await Promise.all([
      api.listarPersonas(),
      api.listarProyectos(),
    ])
    setPersonas(listaPersonas)
    setProyectos(listaProyectos)
    setError(null)
  }, [])

  useEffect(() => {
    let vivo = true
    ;(async () => {
      try {
        await refrescar()
      } catch (e) {
        if (vivo) {
          setError(
            e instanceof Error
              ? e.message
              : 'No se pudo cargar la API. ¿Está corriendo el backend?',
          )
        }
      } finally {
        if (vivo) setCargando(false)
      }
    })()
    return () => {
      vivo = false
    }
  }, [refrescar])

  const value = useMemo<QuequeContextValue>(
    () => ({
      personas,
      proyectos,
      cargando,
      error,
      refrescar,
      async agregarSolicitud(texto, archivo) {
        const id = await api.crearSolicitud(texto, archivo)
        await refrescar()
        return id
      },
      async confirmarAsignacion(proyectoId) {
        await api.confirmarProyecto(proyectoId)
        await refrescar()
      },
      async resugerir(proyectoId) {
        await api.resugerirProyecto(proyectoId)
        await refrescar()
      },
      async reintentar(proyectoId) {
        await api.reintentarProyecto(proyectoId)
        await refrescar()
      },
      async obtenerProyecto(proyectoId) {
        const proyecto = await api.obtenerProyecto(proyectoId)
        setProyectos((prev) => {
          const sin = prev.filter((p) => p.id !== proyecto.id)
          return [proyecto, ...sin].sort((a, b) =>
            a.creado_en < b.creado_en ? 1 : -1,
          )
        })
        return proyecto
      },
    }),
    [personas, proyectos, cargando, error, refrescar],
  )

  return (
    <QuequeContext.Provider value={value}>{children}</QuequeContext.Provider>
  )
}

export function useQueque() {
  const ctx = useContext(QuequeContext)
  if (!ctx) {
    throw new Error('useQueque debe usarse dentro de QuequeProvider')
  }
  return ctx
}
