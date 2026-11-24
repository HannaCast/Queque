export type Area = 'Software' | 'Redes' | 'Marketing' | 'Mecatrónica'
export type Confianza = 'alta' | 'media' | 'baja'
export type Prioridad = 'alta' | 'media' | 'baja'
export type EstadoProyecto = 'nuevo' | 'sugerido' | 'confirmado' | 'en_espera' | 'error'
export type EstadoAsignacion = 'sugerida' | 'confirmada'

export interface AreaRequerida {
  area: Area
  horas_estimadas: number
  porcentaje_sugerido: number
  confianza: Confianza
  justificacion: string
}

export interface Tarea {
  titulo: string
  area: Area
  prioridad: Prioridad
  depende_de: string[]
}

export interface Brief {
  proyecto: string
  resumen: string
  areas_requeridas: AreaRequerida[]
  tareas: Tarea[]
  supuestos: string[]
  preguntas_pendientes: string[]
}

export interface Persona {
  id: number
  nombre: string
  porcentaje_ocupado: number
  areas: Area[]
  proyecto_actual?: string
  libre?: number
}

export interface AsignacionSugerida {
  persona_id: number
  area: Area
  porcentaje: number
  motivo: string
  estado: EstadoAsignacion
}

export interface PersonaSaltada {
  persona_id: number
  motivo: string
}

export interface Proyecto {
  id: number
  nombre: string
  resumen: string
  estado: EstadoProyecto
  brief?: Brief
  texto_crudo?: string
  creado_en: string
  sugerencias: AsignacionSugerida[]
  saltados: PersonaSaltada[]
  requiere_revision?: boolean
  error?: string
}
