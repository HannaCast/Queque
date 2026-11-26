import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import * as api from '../api'
import { useAvisos } from '../components/Avisos'
import type { Rol, Usuario } from '../types'

interface AuthContextValue {
  usuario: Usuario | null
  /** true mientras se pregunta al backend si ya había una sesión abierta. */
  comprobando: boolean
  /** Admin y coordinador crean solicitudes y confirman; consulta solo ve. */
  puedeEditar: boolean
  entrar: (correo: string, contrasena: string) => Promise<void>
  salir: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function etiquetaRol(rol: Rol): string {
  switch (rol) {
    case 'admin':
      return 'Administrador'
    case 'coordinador':
      return 'Coordinador'
    case 'consulta':
      return 'Consulta'
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const avisar = useAvisos()
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [comprobando, setComprobando] = useState(true)

  useEffect(() => {
    let vivo = true
    api
      .usuarioActual()
      .then((u) => {
        if (vivo) setUsuario(u)
      })
      .catch(() => {
        // Si el backend no responde, se muestra el login; ahí se verá el error al intentar entrar.
      })
      .finally(() => {
        if (vivo) setComprobando(false)
      })
    return () => {
      vivo = false
    }
  }, [])

  // Cualquier 401 de la API (sesión vencida, usuario desactivado) regresa al login.
  // Varias peticiones pueden fallar a la vez: el ref hace que el aviso salga una sola vez.
  const hayUsuario = useRef(false)
  useEffect(() => {
    hayUsuario.current = usuario !== null
  }, [usuario])

  useEffect(() => {
    function alExpirar() {
      if (!hayUsuario.current) return
      hayUsuario.current = false
      setUsuario(null)
      avisar('Tu sesión terminó. Vuelve a iniciar sesión.', 'info')
    }
    window.addEventListener(api.EVENTO_SESION_EXPIRADA, alExpirar)
    return () => window.removeEventListener(api.EVENTO_SESION_EXPIRADA, alExpirar)
  }, [avisar])

  const entrar = useCallback(async (correo: string, contrasena: string) => {
    const u = await api.iniciarSesion(correo, contrasena)
    setUsuario(u)
  }, [])

  const salir = useCallback(async () => {
    try {
      await api.cerrarSesion()
    } finally {
      setUsuario(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      usuario,
      comprobando,
      puedeEditar: usuario?.rol === 'admin' || usuario?.rol === 'coordinador',
      entrar,
      salir,
    }),
    [usuario, comprobando, entrar, salir],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth debe usarse dentro de AuthProvider')
  }
  return ctx
}
