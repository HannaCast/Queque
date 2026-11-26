import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { QuequeProvider } from '../context/QuequeContext'

/** Sin sesión manda al login (recordando a dónde iba). Con sesión carga los datos y muestra la página. */
export function RequiereSesion() {
  const { usuario, comprobando } = useAuth()
  const location = useLocation()

  if (comprobando) {
    return (
      <div className="pantalla-carga" role="status" aria-live="polite">
        <span className="brand-mark" aria-hidden="true" />
        Cargando…
      </div>
    )
  }

  if (!usuario) {
    return <Navigate to="/login" replace state={{ desde: location.pathname }} />
  }

  return (
    <QuequeProvider>
      <Outlet />
    </QuequeProvider>
  )
}
