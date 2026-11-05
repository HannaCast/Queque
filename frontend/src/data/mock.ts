import type { Brief, Persona, Proyecto } from '../types'

export const AREAS = ['Software', 'Redes', 'Marketing', 'Mecatrónica'] as const

export const briefFarmacia: Brief = {
  proyecto: 'Inventario de farmacia',
  resumen: 'Sistema para controlar existencias y caducidades',
  areas_requeridas: [
    {
      area: 'Software',
      horas_estimadas: 120,
      porcentaje_sugerido: 40,
      confianza: 'alta',
      justificacion: 'Sistema de control de existencias',
    },
  ],
  tareas: [
    {
      titulo: 'Diseñar base de datos',
      area: 'Software',
      prioridad: 'alta',
      depende_de: [],
    },
  ],
  supuestos: ['El documento no indica cuántas sucursales hay'],
  preguntas_pendientes: ['¿Se usarán lectores de código de barras?'],
}

export const personasIniciales: Persona[] = [
  {
    id: 1,
    nombre: 'Moody',
    porcentaje_ocupado: 100,
    areas: ['Software'],
    proyecto_actual: 'Portal de alumnos',
  },
  {
    id: 2,
    nombre: 'GESA',
    porcentaje_ocupado: 40,
    areas: ['Software', 'Redes'],
    proyecto_actual: 'Campaña de redes',
  },
  {
    id: 3,
    nombre: 'Leo',
    porcentaje_ocupado: 10,
    areas: ['Software', 'Mecatrónica'],
    proyecto_actual: 'Sensor de temperatura',
  },
]

export const proyectosIniciales: Proyecto[] = [
  {
    id: 1,
    nombre: 'Inventario de farmacia',
    resumen: 'Sistema para controlar existencias y caducidades',
    estado: 'sugerido',
    brief: briefFarmacia,
    texto_crudo:
      'hay que hacer un sistema de inventarios para una farmacia, controlar existencias y caducidades, salió rapidísimo en un word',
    creado_en: '2026-10-29T09:12:00',
    sugerencias: [
      {
        persona_id: 2,
        area: 'Software',
        porcentaje: 40,
        motivo:
          'GESA tiene Software y 60 % libre. Moody está al 100 % y se salta.',
        estado: 'sugerida',
      },
    ],
    saltados: [
      {
        persona_id: 1,
        motivo: 'Está al 100 % en Portal de alumnos',
      },
    ],
  },
  {
    id: 2,
    nombre: 'Sensor de temperatura',
    resumen: 'Monitoreo de temperatura en laboratorio',
    estado: 'confirmado',
    creado_en: '2026-10-20T11:00:00',
    sugerencias: [
      {
        persona_id: 3,
        area: 'Mecatrónica',
        porcentaje: 10,
        motivo: 'Leo tiene Mecatrónica y disponibilidad',
        estado: 'confirmada',
      },
    ],
    saltados: [],
  },
  {
    id: 3,
    nombre: 'Nota sin título',
    resumen: 'Pendiente de análisis',
    estado: 'nuevo',
    texto_crudo: 'necesitan una landing para el evento de egresados',
    creado_en: '2026-10-29T13:40:00',
    sugerencias: [],
    saltados: [],
  },
]

export function libreDe(persona: Persona): number {
  return Math.max(0, 100 - persona.porcentaje_ocupado)
}

export function etiquetaEstado(estado: Proyecto['estado']): string {
  switch (estado) {
    case 'nuevo':
      return 'Recién llegado'
    case 'sugerido':
      return 'Con sugerencia'
    case 'confirmado':
      return 'Asignado'
    case 'en_espera':
      return 'En espera'
    case 'error':
      return 'Error'
  }
}
