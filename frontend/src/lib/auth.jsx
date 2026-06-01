import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { apiFor, TOKEN_KEY, SESSION_KEY, errMessage } from './api.js'

const AuthContext = createContext(null)

/** Decode payload JWT tanpa verifikasi (hanya untuk membaca exp/username di sisi klien). */
function decodeJwt(token) {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  })
  const [loading, setLoading] = useState(false)

  // Logout otomatis jika token kedaluwarsa
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) return
    const payload = decodeJwt(token)
    if (payload?.exp && payload.exp * 1000 < Date.now()) logout()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /**
   * Login ke backend FastAPI sesuai divisi.
   * @param {{username:string, password:string, division:'data-scientist'|'credit-analysis'}} creds
   */
  async function login({ username, password, division }) {
    setLoading(true)
    try {
      const api = apiFor(division)
      // FastAPI OAuth2PasswordRequestForm mengharapkan x-www-form-urlencoded
      const form = new URLSearchParams()
      form.append('username', username)
      form.append('password', password)

      const { data } = await api.post('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })

      const token = data.access_token
      localStorage.setItem(TOKEN_KEY, token)

      const payload = decodeJwt(token)
      const sess = {
        username: data.username || username,
        division,
        role: data.role || payload?.role || division,
        loginAt: Date.now(),
      }
      localStorage.setItem(SESSION_KEY, JSON.stringify(sess))
      setSession(sess)
      return { ok: true, session: sess }
    } catch (e) {
      return { ok: false, error: errMessage(e, 'Username atau password salah.') }
    } finally {
      setLoading(false)
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(SESSION_KEY)
    setSession(null)
  }

  const value = useMemo(
    () => ({ session, loading, login, logout, isAuthed: !!session }),
    [session, loading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth harus dipakai di dalam <AuthProvider>')
  return ctx
}
