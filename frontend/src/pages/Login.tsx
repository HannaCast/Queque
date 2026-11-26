import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Icono } from '../components/Icono'
import { useAuth } from '../context/AuthContext'
import { mensajeAmigable } from '../utils/errores'

export function Login() {
  const { usuario, comprobando, entrar } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const desde = (location.state as { desde?: string } | null)?.desde ?? '/'

  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [verContrasena, setVerContrasena] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!comprobando && usuario) {
    return <Navigate to={desde} replace />
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!correo.trim() || !contrasena) return
    setEnviando(true)
    setError(null)
    try {
      await entrar(correo.trim(), contrasena)
      navigate(desde, { replace: true })
    } catch (e) {
      setError(mensajeAmigable(e, 'No se pudo iniciar sesión.'))
      setEnviando(false)
    }
  }

  return (
    <div className="login">
      <section className="login-hero" aria-hidden="false">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <span className="brand-name">Nextword</span>
        </div>
        <div className="login-hero-texto">
          <span className="login-pastilla">
            <span className="punto" aria-hidden="true" />
            Encolado de proyectos
          </span>
          <h1>
            Cada proyecto, <span className="resaltado">con la persona</span> correcta
          </h1>
          <p>
            Recibe notas, genera el brief y confirma quién tiene espacio para tomar el
            siguiente proyecto.
          </p>
        </div>
        <p className="login-hero-pie">Queque · Nextword</p>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={onSubmit} noValidate>
          <span className="login-icono" aria-hidden="true">
            <Icono nombre="candado" tamano={22} />
          </span>
          <h2>Inicia sesión</h2>
          <p className="hint">Usa el correo y la contraseña que te dio el administrador.</p>

          <div className="field">
            <label htmlFor="correo">Correo</label>
            <div className="campo-icono">
              <Icono nombre="correo" tamano={17} />
              <input
                id="correo"
                type="email"
                autoComplete="username"
                value={correo}
                onChange={(e) => setCorreo(e.target.value)}
                placeholder="tu@correo.com"
                disabled={enviando}
                required
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="contrasena">Contraseña</label>
            <div className="campo-icono">
              <Icono nombre="candado" tamano={17} />
              <input
                id="contrasena"
                type={verContrasena ? 'text' : 'password'}
                autoComplete="current-password"
                value={contrasena}
                onChange={(e) => setContrasena(e.target.value)}
                disabled={enviando}
                required
              />
              <button
                type="button"
                className="campo-boton"
                onClick={() => setVerContrasena(!verContrasena)}
                aria-label={verContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              >
                <Icono nombre={verContrasena ? 'ojoCerrado' : 'ojo'} tamano={17} />
              </button>
            </div>
          </div>

          {error ? (
            <p className="login-error" role="alert">
              <Icono nombre="alerta" tamano={16} />
              {error}
            </p>
          ) : null}

          <button className="btn login-boton" type="submit" disabled={enviando || !correo.trim() || !contrasena}>
            {enviando ? 'Entrando…' : 'Iniciar sesión'}
          </button>
        </form>
      </section>
    </div>
  )
}
