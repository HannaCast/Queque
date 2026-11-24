import type { Persona, Proyecto } from './types'

async function leerError(respuesta: Response): Promise<string> {
  try {
    const cuerpo = await respuesta.json()
    if (typeof cuerpo?.detail === 'string') return cuerpo.detail
    return JSON.stringify(cuerpo?.detail ?? cuerpo)
  } catch {
    return respuesta.statusText || 'Error de red'
  }
}

async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  const respuesta = await fetch(ruta, init)
  if (!respuesta.ok) {
    throw new Error(await leerError(respuesta))
  }
  if (respuesta.status === 204) {
    return undefined as T
  }
  return respuesta.json() as Promise<T>
}

export function listarProyectos(): Promise<Proyecto[]> {
  return pedir('/api/proyectos')
}

export function obtenerProyecto(id: number): Promise<Proyecto> {
  return pedir(`/api/proyectos/${id}`)
}

export function listarPersonas(): Promise<Persona[]> {
  return pedir('/api/personas')
}

export async function crearSolicitud(
  texto: string,
  archivo?: File,
): Promise<number> {
  const datos = new FormData()
  if (texto.trim()) datos.append('texto', texto.trim())
  if (archivo) datos.append('archivo', archivo)
  const cuerpo = await pedir<{ id: number }>('/api/solicitudes', {
    method: 'POST',
    body: datos,
  })
  return cuerpo.id
}

export function confirmarProyecto(id: number): Promise<Proyecto> {
  return pedir(`/api/proyectos/${id}/confirmar`, { method: 'POST' })
}

export function resugerirProyecto(id: number): Promise<Proyecto> {
  return pedir(`/api/proyectos/${id}/resugerir`, { method: 'POST' })
}

export function reintentarProyecto(id: number): Promise<Proyecto> {
  return pedir(`/api/proyectos/${id}/reintentar`, { method: 'POST' })
}
