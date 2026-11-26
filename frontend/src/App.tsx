import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AvisosProvider } from './components/Avisos'
import { Layout } from './components/Layout'
import { RequiereSesion } from './components/RequiereSesion'
import { AuthProvider } from './context/AuthContext'
import { Cola } from './pages/Cola'
import { Dashboard } from './pages/Dashboard'
import { Equipo } from './pages/Equipo'
import { Login } from './pages/Login'
import { NuevaSolicitud } from './pages/NuevaSolicitud'
import { Proyecto } from './pages/Proyecto'

export default function App() {
  return (
    <AvisosProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="login" element={<Login />} />
            <Route element={<RequiereSesion />}>
              <Route element={<Layout />}>
                <Route index element={<Cola />} />
                <Route path="nueva" element={<NuevaSolicitud />} />
                <Route path="proyecto/:id" element={<Proyecto />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="equipo" element={<Equipo />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </AvisosProvider>
  )
}
