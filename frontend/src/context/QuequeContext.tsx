import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  briefFarmacia,
  personasIniciales,
  proyectosIniciales,
} from '../data/mock'
import type { Area, Persona, Proyecto } from '../types'

interface QuequeContextValue {
  personas: Persona[]
  proyectos: Proyecto[]
  agregarSolicitud: (texto: string, archivo?: string) => number
  confirmarAsignacion: (proyectoId: number) => void
  guardarPersona: (persona: Persona) => void
  crearPersona: (nombre: string, areas: Area[], ocupado: number) => void
}

const QuequeContext = createContext<QuequeContextValue | null>(null)

function siguienteId(items: { id: number }[]): number {
  return items.reduce((max, item) => Math.max(max, item.id), 0) + 1
}

export function QuequeProvider({ children }: { children: ReactNode }) {
  const [personas, setPersonas] = useState<Persona[]>(personasIniciales)
  const [proyectos, setProyectos] = useState<Proyecto[]>(proyectosIniciales)

  const value = useMemo<QuequeContextValue>(
    () => ({
      personas,
      proyectos,
      agregarSolicitud(texto, archivo) {
        const id = siguienteId(proyectos)
        const esFarmacia = /farmacia|inventario/i.test(texto)
        const brief = esFarmacia
          ? briefFarmacia
          : {
              proyecto: archivo?.replace(/\.[^.]+$/, '') || 'Nueva solicitud',
              resumen: texto.slice(0, 140) || 'Solicitud sin resumen todavía',
              areas_requeridas: [
                {
                  area: 'Software' as const,
                  horas_estimadas: 80,
                  porcentaje_sugerido: 30,
                  confianza: 'media' as const,
                  justificacion: 'Se asume desarrollo de software a partir del texto',
                },
              ],
              tareas: [
                {
                  titulo: 'Definir alcance',
                  area: 'Software' as const,
                  prioridad: 'alta' as const,
                  depende_de: [],
                },
              ],
              supuestos: ['Brief generado con datos de ejemplo, sin modelo local'],
              preguntas_pendientes: ['¿Qué fecha de entrega se espera?'],
            }

        const candidatas = personas
          .filter((p) => p.areas.includes('Software') && p.porcentaje_ocupado < 100)
          .sort((a, b) => a.porcentaje_ocupado - b.porcentaje_ocupado)

        const elegida = candidatas[0]
        const saltados = personas
          .filter((p) => p.areas.includes('Software') && p.porcentaje_ocupado >= 100)
          .map((p) => ({
            persona_id: p.id,
            motivo: `Está al 100 %${p.proyecto_actual ? ` en ${p.proyecto_actual}` : ''}`,
          }))

        const nuevo: Proyecto = {
          id,
          nombre: brief.proyecto,
          resumen: brief.resumen,
          estado: elegida ? 'sugerido' : 'en_espera',
          brief,
          texto_crudo: texto,
          creado_en: new Date().toISOString(),
          sugerencias: elegida
            ? [
                {
                  persona_id: elegida.id,
                  area: 'Software',
                  porcentaje: brief.areas_requeridas[0]?.porcentaje_sugerido ?? 30,
                  motivo: `${elegida.nombre} tiene Software y ${100 - elegida.porcentaje_ocupado} % libre.`,
                  estado: 'sugerida',
                },
              ]
            : [],
          saltados,
        }

        setProyectos((prev) => [nuevo, ...prev])
        return id
      },
      confirmarAsignacion(proyectoId) {
        setProyectos((prev) =>
          prev.map((proyecto) => {
            if (proyecto.id !== proyectoId) return proyecto
            return {
              ...proyecto,
              estado: 'confirmado',
              sugerencias: proyecto.sugerencias.map((s) => ({
                ...s,
                estado: 'confirmada',
              })),
            }
          }),
        )

        setPersonas((prev) =>
          prev.map((persona) => {
            const proyecto = proyectos.find((p) => p.id === proyectoId)
            const sugerencia = proyecto?.sugerencias.find(
              (s) => s.persona_id === persona.id,
            )
            if (!sugerencia) return persona
            const ocupado = Math.min(
              100,
              persona.porcentaje_ocupado + sugerencia.porcentaje,
            )
            return {
              ...persona,
              porcentaje_ocupado: ocupado,
              proyecto_actual: proyecto?.nombre ?? persona.proyecto_actual,
            }
          }),
        )
      },
      guardarPersona(persona) {
        setPersonas((prev) =>
          prev.map((item) => (item.id === persona.id ? persona : item)),
        )
      },
      crearPersona(nombre, areas, ocupado) {
        setPersonas((prev) => [
          ...prev,
          {
            id: siguienteId(prev),
            nombre,
            areas,
            porcentaje_ocupado: ocupado,
          },
        ])
      },
    }),
    [personas, proyectos],
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
