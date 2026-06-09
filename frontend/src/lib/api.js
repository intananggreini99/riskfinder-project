import axios from 'axios'

/**
 * RiskFinder API Client
 *
 * Backend FastAPI berjalan pada dua service/container berbeda:
 * - DS : Data Scientist Sistem  → build model, management model, monitoring
 * - CA : Credit Analysis Sistem → entry data, prediksi, simpan testing
 *
 * Production Vercel WAJIB memakai:
 * - VITE_DS_API_URL=https://<url-ds-service>
 * - VITE_CA_API_URL=https://<url-ca-service>
 *
 * Development lokal boleh memakai proxy Vite:
 * - /api/ds
 * - /api/ca
 */

export const TOKEN_KEY = 'rf_token'
export const SESSION_KEY = 'rf_session'

const IS_PROD = import.meta.env.PROD

function normalizeBaseUrl(value) {
  if (!value) return ''
  return String(value).trim().replace(/\/+$/, '')
}

function resolveBaseUrl(envName, envValue, devFallback) {
  const normalized = normalizeBaseUrl(envValue)

  if (normalized) return normalized

  if (!IS_PROD) return devFallback

  console.error(
    `[RiskFinder] ${envName} belum dikonfigurasi di Vercel. ` +
      `Frontend production tidak boleh fallback ke ${devFallback}.`
  )

  return ''
}

const DS_BASE = resolveBaseUrl(
  'VITE_DS_API_URL',
  import.meta.env.VITE_DS_API_URL,
  '/api/ds'
)

const CA_BASE = resolveBaseUrl(
  'VITE_CA_API_URL',
  import.meta.env.VITE_CA_API_URL,
  '/api/ca'
)

export const MLFLOW_UI_URL =
  normalizeBaseUrl(import.meta.env.VITE_MLFLOW_UI_URL) || 'http://localhost:5000'

export const API_BASES = {
  ds: DS_BASE,
  ca: CA_BASE,
  mlflow: MLFLOW_UI_URL,
}

// Debug helper.
// Buka browser console lalu ketik:
// window.__RISKFINDER_API_BASES__
if (typeof window !== 'undefined') {
  window.__RISKFINDER_API_BASES__ = API_BASES
}

function makeClient(baseURL, label, envName) {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
  })

  client.interceptors.request.use((config) => {
    if (!baseURL) {
      return Promise.reject(
        new Error(
          `[RiskFinder] ${label} API belum dikonfigurasi. ` +
            `Isi ${envName} di Vercel → Project → Settings → Environment Variables, ` +
            `lalu lakukan deployment ulang.`
        )
      )
    }

    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  })

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

export const dsApi = makeClient(DS_BASE, 'Data Scientist', 'VITE_DS_API_URL')
export const caApi = makeClient(CA_BASE, 'Credit Analysis', 'VITE_CA_API_URL')

export function apiFor(division) {
  return division === 'credit-analysis' ? caApi : dsApi
}

export function errMessage(e, fallback = 'Terjadi kesalahan. Coba lagi.') {
  return (
    e?.response?.data?.detail ||
    e?.response?.data?.message ||
    e?.message ||
    fallback
  )
}