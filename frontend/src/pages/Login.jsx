import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { FlaskConical, ShieldCheck, Lock, User, ArrowRight, Eye, EyeOff } from 'lucide-react'
import Logo from '../components/Logo.jsx'
import { Banner, Spinner } from '../components/ui.jsx'
import { useAuth } from '../lib/auth.jsx'

const DIVISIONS = [
  {
    id: 'data-scientist',
    name: 'Data Scientist',
    desc: 'Build model, ML Flow & monitoring',
    icon: FlaskConical,
  },
  {
    id: 'credit-analysis',
    name: 'Credit Analysis',
    desc: 'Entry data & prediksi gagal bayar',
    icon: ShieldCheck,
  },
]

export default function Login() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [division, setDivision] = useState('data-scientist')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!username || !password) {
      setError('Mohon isi username dan password.')
      return
    }
    const res = await login({ username, password, division })
    if (res.ok) {
      const home = division === 'credit-analysis' ? '/app/entry' : '/app/menu'
      navigate(location.state?.from || home, { replace: true })
    } else {
      setError(res.error)
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      {/* ===== Panel brand (kiri) ===== */}
      <aside className="relative hidden overflow-hidden bg-navy lg:block">
        <div className="bg-grid absolute inset-0 opacity-[0.5]" />
        {/* Glow dekoratif */}
        <div className="absolute -left-24 top-24 h-72 w-72 rounded-full bg-sky/20 blur-3xl" />
        <div className="absolute bottom-10 right-0 h-80 w-80 rounded-full bg-teal/20 blur-3xl" />

        <div className="relative flex h-full flex-col justify-between p-12 xl:p-16">
          <Logo tone="light" className="h-11" />

          <div className="max-w-md">
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-semibold tracking-wide text-teal-400">
              <span className="h-1.5 w-1.5 rounded-full bg-teal" /> CREDIT RISK INTELLIGENCE
            </p>
            <h1 className="font-display text-4xl font-semibold leading-tight text-white xl:text-5xl">
              Prediksi gagal bayar dengan presisi.
            </h1>
            <p className="mt-5 text-[15px] leading-relaxed text-white/70">
              Platform analisis risiko kredit end-to-end — dari preprocessing &amp; modeling oleh tim
              Data Scientist, hingga keputusan kredit real-time oleh tim Credit Analysis.
            </p>

            <div className="mt-8 grid grid-cols-3 gap-3">
              {[
                ['ROC AUC', 'Evaluasi'],
                ['FastAPI', 'Inference'],
                ['PostgreSQL', 'Audit trail'],
              ].map(([a, b]) => (
                <div key={a} className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <p className="font-display text-lg font-semibold text-white">{a}</p>
                  <p className="text-xs text-white/55">{b}</p>
                </div>
              ))}
            </div>
          </div>

          <p className="text-xs text-white/40">
            © {new Date().getFullYear()} RiskFinder Team · Seluruh akses tercatat &amp; terenkripsi (JWT)
          </p>
        </div>
      </aside>

      {/* ===== Form (kanan) ===== */}
      <div className="flex items-center justify-center bg-canvas px-5 py-10">
        <div className="w-full max-w-md animate-fade-up">
          <div className="mb-8 lg:hidden">
            <Logo className="h-10" />
          </div>

          <h2 className="font-display text-3xl font-semibold text-navy">Hi! Welcome to RiskFinder</h2>

          {/* Pemilih divisi (Divisi) */}
          <div className="mt-7">
            <span className="label">Divisi</span>
            <div className="grid grid-cols-2 gap-3">
              {DIVISIONS.map((d) => {
                const active = division === d.id
                return (
                  <button
                    type="button"
                    key={d.id}
                    onClick={() => setDivision(d.id)}
                    className={`group rounded-xl border p-3.5 text-left transition-all ${
                      active
                        ? 'border-royal bg-royal/5 shadow-ring'
                        : 'border-line bg-white hover:border-navy-200'
                    }`}
                  >
                    <div
                      className={`mb-2 grid h-9 w-9 place-items-center rounded-lg transition ${
                        active ? 'bg-navy text-white' : 'bg-navy-50 text-navy-500'
                      }`}
                    >
                      <d.icon className="h-4.5 w-4.5" strokeWidth={2.1} />
                    </div>
                    <p className="text-sm font-bold text-navy">{d.name}</p>
                  </button>
                )
              })}
            </div>
          </div>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <div>
              <label className="label" htmlFor="username">Username</label>
              <div className="relative">
                <User className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-navy-300" />
                <input
                  id="username"
                  className="field pl-10"
                  placeholder="mis. intan_anggreini99"
                  value={username}
                  autoComplete="username"
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="password">Password</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-navy-300" />
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  className="field pl-10 pr-10"
                  placeholder="••••••••"
                  value={password}
                  autoComplete="current-password"
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-navy-300 hover:text-navy"
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && <Banner kind="error" onClose={() => setError('')}>{error}</Banner>}

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? <Spinner /> : <>Masuk <ArrowRight className="h-4 w-4" /></>}
            </button>
          </form>
          
        </div>
      </div>
    </div>
  )
}
