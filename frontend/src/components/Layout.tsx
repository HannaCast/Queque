import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { etiquetaRol, useAuth } from '../context/AuthContext'
import { useQueque } from '../context/QuequeContext'
import { iniciales } from '../utils/texto'
import { useAvisos } from './Avisos'
import { Icono, type NombreIcono } from './Icono'

const VERSION = '0.0.0'
const CLAVE_TEMA = 'queque-tema'

type Tema = 'claro' | 'oscuro'

const links: { to: string; label: string; icono: NombreIcono; end?: boolean; soloEdicion?: boolean }[] = [
  { to: '/', label: 'Cola', icono: 'cola', end: true },
  { to: '/nueva', label: 'Nueva solicitud', icono: 'nueva', soloEdicion: true },
  { to: '/dashboard', label: 'Dashboard', icono: 'dashboard' },
  { to: '/equipo', label: 'Equipo', icono: 'equipo' },
]

function temaGuardado(): Tema {
  try {
    return localStorage.getItem(CLAVE_TEMA) === 'oscuro' ? 'oscuro' : 'claro'
  } catch {
    return 'claro'
  }
}

export function Layout() {
  const { proyectos } = useQueque()
  const { usuario, puedeEditar, salir } = useAuth()
  const avisar = useAvisos()
  const navigate = useNavigate()
  const [menuAbierto, setMenuAbierto] = useState(false)
  const [tema, setTema] = useState<Tema>(temaGuardado)

  const pendientes = proyectos.filter((p) => p.estado !== 'confirmado').length
  const visibles = links.filter((link) => !link.soloEdicion || puedeEditar)

  async function cerrarSesion() {
    await salir()
    avisar('Cerraste sesión', 'info')
    navigate('/login', { replace: true })
  }

  useEffect(() => {
    document.documentElement.dataset.theme = tema === 'oscuro' ? 'dark' : 'light'
    try {
      localStorage.setItem(CLAVE_TEMA, tema)
    } catch {
      // Sin almacenamiento disponible: el tema solo dura esta visita.
    }
  }, [tema])

  return (
    <div className="app-shell">
      <header className={`topbar${menuAbierto ? ' menu-abierto' : ''}`}>
        <div className="topbar-fila">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-name">Nextword</span>
            <span className="brand-tag">encolado de proyectos</span>
          </div>
          <div className="topbar-botones">
            {usuario ? (
              <div className="usuario-chip" title={usuario.correo}>
                <span className="usuario-avatar" aria-hidden="true">
                  {iniciales(usuario.nombre)}
                </span>
                <span className="usuario-datos">
                  <strong>{usuario.nombre}</strong>
                  <small>{etiquetaRol(usuario.rol)}</small>
                </span>
              </div>
            ) : null}
            <button
              type="button"
              className="icon-btn"
              onClick={() => void cerrarSesion()}
              aria-label="Cerrar sesión"
              title="Cerrar sesión"
            >
              <Icono nombre="salir" />
            </button>
            <button
              type="button"
              className="icon-btn"
              onClick={() => setTema(tema === 'oscuro' ? 'claro' : 'oscuro')}
              aria-label={tema === 'oscuro' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
              title={tema === 'oscuro' ? 'Modo claro' : 'Modo oscuro'}
            >
              <Icono nombre={tema === 'oscuro' ? 'sol' : 'luna'} />
            </button>
            <button
              type="button"
              className="icon-btn menu-toggle"
              onClick={() => setMenuAbierto(!menuAbierto)}
              aria-label={menuAbierto ? 'Cerrar menú' : 'Abrir menú'}
              aria-expanded={menuAbierto}
              aria-controls="nav-principal"
            >
              <Icono nombre={menuAbierto ? 'cerrar' : 'menu'} />
            </button>
          </div>
        </div>
        <nav className="nav" id="nav-principal" aria-label="Principal">
          {visibles.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              onClick={() => setMenuAbierto(false)}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              <Icono nombre={link.icono} tamano={17} />
              <span>{link.label}</span>
              {link.to === '/' && pendientes > 0 ? (
                <span className="nav-contador" aria-label={`${pendientes} pendientes`}>
                  {pendientes}
                </span>
              ) : null}
            </NavLink>
          ))}
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="footer">
        <div className="footer-inner">
          <span className="footer-marca">
            <span className="brand-mark" aria-hidden="true" />
            Queque · Nextword
          </span>
          <span>Encolado y asignación de proyectos</span>
          <span className="footer-version">v{VERSION}</span>
        </div>
      </footer>
    </div>
  )
}
