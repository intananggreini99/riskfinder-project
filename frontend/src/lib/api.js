import axios from 'axios'

/**
 * Dua backend FastAPI berjalan di dua container Docker terpisah:
 *  - DS  : Data Scientist Sistem  (build model, monitoring)
 *  - CA  : Credit Analysis Sistem (entry data, prediksi)
 *
 * Saat dev lokal, Vite mem-proxy /api/ds dan /api/ca (lihat vite.config.js).
 * Saat produksi (Vercel), pakai VITE_DS_API_URL & VITE_CA_API_URL.
 */
const DS_BASE = import.meta.env.VITE_DS_API_URL || '/api/ds'
const CA_BASE = import.meta.env.VITE_CA_API_URL || '/api/ca'

export const TOKEN_KEY = 'rf_token'
export const SESSION_KEY = 'rf_session'

function makeClient(baseURL) {
  const client = axios.create({ baseURL, timeout: 30000 })

  // Sisipkan Bearer token JWT pada setiap request
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })

  // Tangani 401 → bersihkan sesi dan arahkan ke login
  client.interceptors.response.use(
    (res) => res,
    (err) => {
      if (err.response && err.response.status === 401) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(SESSION_KEY)
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login'
        }
      }
      return Promise.reject(err)
    }
  )
  return client
}

export const dsApi = makeClient(DS_BASE)
export const caApi = makeClient(CA_BASE)

/** Pilih client sesuai divisi user yang sedang login. */
export function apiFor(division) {
  return division === 'credit-analysis' ? caApi : dsApi
}

/** Ekstrak pesan error yang ramah dari response axios. */
export function errMessage(e, fallback = 'Terjadi kesalahan. Coba lagi.') {
  return (
    e?.response?.data?.detail ||
    e?.response?.data?.message ||
    e?.message ||
    fallback
  )
}
