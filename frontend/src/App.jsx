import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Login from './pages/Login.jsx'
import MainMenu from './pages/MainMenu.jsx'
import ServiceMLFlow from './pages/ServiceMLFlow.jsx'
import Monitoring from './pages/Monitoring.jsx'
import ModelEvaluation from './pages/ModelEvaluation.jsx'
import EntryData from './pages/EntryData.jsx'
import AnalysisResult from './pages/AnalysisResult.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* ===== Divisi Data Scientist ===== */}
      <Route
        path="/app/menu"
        element={
          <ProtectedRoute allow={['data-scientist']}>
            <MainMenu />
          </ProtectedRoute>
        }
      />
      <Route
        path="/app/mlflow"
        element={
          <ProtectedRoute allow={['data-scientist']}>
            <ServiceMLFlow />
          </ProtectedRoute>
        }
      />
      <Route
        path="/app/monitoring"
        element={
          <ProtectedRoute allow={['data-scientist']}>
            <Monitoring />
          </ProtectedRoute>
        }
      />
      <Route
        path="/app/monitoring/evaluate/:pairId"
        element={
          <ProtectedRoute allow={['data-scientist']}>
            <ModelEvaluation />
          </ProtectedRoute>
        }
      />

      {/* ===== Divisi Credit Analysis ===== */}
      <Route
        path="/app/entry"
        element={
          <ProtectedRoute allow={['credit-analysis']}>
            <EntryData />
          </ProtectedRoute>
        }
      />
      <Route
        path="/app/result"
        element={
          <ProtectedRoute allow={['credit-analysis']}>
            <AnalysisResult />
          </ProtectedRoute>
        }
      />

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
