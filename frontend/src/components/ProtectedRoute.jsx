import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth.jsx'

/**
 * Membatasi akses rute.
 * @param {string[]} [allow] - divisi yang diizinkan ('data-scientist' | 'credit-analysis').
 *                              Jika kosong, cukup terautentikasi.
 */
export default function ProtectedRoute({ children, allow }) {
  const { session, isAuthed } = useAuth()
  const location = useLocation()

  if (!isAuthed) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (allow && !allow.includes(session.division)) {
    // Arahkan ke beranda divisi yang sesuai
    const home = session.division === 'credit-analysis' ? '/app/entry' : '/app/menu'
    return <Navigate to={home} replace />
  }

  return children
}
