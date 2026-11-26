import type { Persona, Proyecto, Usuario } from './types'

/** Se lanza cuando la API responde 401 fuera del login: la sesión venció o se cerró. */
export const EVENTO_SESION_EXPIRADA = 'queque:sesion-expirada'

async function leerError(respuesta: Response): Promise<string> {
  try {
    const cuerpo = await respuesta.json()
    if (typeof cuerpo?.detail === 'string') return cuerpo.detail
    return JSON.stringify(cuerpo?.detail ?? cuerpo)
  } catch {
    return respuesta.statusText || 'Error de red'
  }
}

async function pedir<T>(ruta: string, init?: RequestInit, avisarSiExpira = true): Promise<T> {
  const respuesta = await fetch(ruta, { credentials: 'same-origin', ...init })
  if (!respuesta.ok) {
    if (respuesta.status === 401 && avisarSiExpira) {
      window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA))
    }
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

// --- Sesión ---
export function iniciarSesion(correo: string, contrasena: string): Promise<Usuario> {
  return pedir(
    '/api/auth/login',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ correo, contrasena }),
    },
    false,
  )
}

export function cerrarSesion(): Promise<void> {
  return pedir('/api/auth/logout', { method: 'POST' }, false)
}

/** Devuelve el usuario con sesión, o null si no hay sesión. */
export async function usuarioActual(): Promise<Usuario | null> {
  const respuesta = await fetch('/api/auth/yo', { credentials: 'same-origin' })
  if (respuesta.status === 401) return null
  if (!respuesta.ok) throw new Error(await leerError(respuesta))
  return respuesta.json() as Promise<Usuario>
}
