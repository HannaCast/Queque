import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { QuequeProvider } from './context/QuequeContext'
import { Cola } from './pages/Cola'
import { Dashboard } from './pages/Dashboard'
import { Equipo } from './pages/Equipo'
import { NuevaSolicitud } from './pages/NuevaSolicitud'
import { Proyecto } from './pages/Proyecto'

export default function App() {
  return (
    <QuequeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Cola />} />
            <Route path="nueva" element={<NuevaSolicitud />} />
            <Route path="proyecto/:id" element={<Proyecto />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="equipo" element={<Equipo />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QuequeProvider>
  )
}
