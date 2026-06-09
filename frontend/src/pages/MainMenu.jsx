import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Hammer, Activity, ArrowRight, ExternalLink, Loader2 } from 'lucide-react'
import AppShell from '../components/AppShell.jsx'
import { Banner } from '../components/ui.jsx'
import { useAuth } from '../lib/auth.jsx'
import { MLFLOW_UI_URL } from '../lib/api.js'

const CARDS = [
  {
    kind: 'mlflow',
    icon: Hammer,
    title: 'Build Model',
    desc: 'Buka web UI MLflow lokal untuk menjalankan eksperimen dan melihat tracking run.',
    accent: 'from-royal to-gold-400',
  },
  {
    to: '/app/monitoring',
    icon: Activity,
    title: 'Monitoring Model',
    desc: 'Kelola artifact, pasangan model + preprocessing, evaluasi, dan histori testing.',
    accent: 'from-navy to-royal',
  },
]

export default function MainMenu() {
  const { session } = useAuth()
  const [checkingMlflow, setCheckingMlflow] = useState(false)
  const [mlflowError, setMlflowError] = useState('')

  async function openLocalMlflow() {
    setCheckingMlflow(true)
    setMlflowError('')
    try {
      // mode no-cors cukup untuk membedakan server reachable vs connection refused.
      await fetch(MLFLOW_UI_URL, { mode: 'no-cors', cache: 'no-store' })
      window.location.href = MLFLOW_UI_URL
    } catch {
      setMlflowError(
        `Container MLFlow lokal belum running. Jalankan \`docker compose up -d mlflow\` atau pastikan ${MLFLOW_UI_URL} dapat dibuka.`
      )
    } finally {
      setCheckingMlflow(false)
    }
  }

  return (
    <AppShell>
      {/* Hero ringkas */}
      <div className="animate-fade-up">
        <p className="mb-1.5 text-xs font-bold uppercase tracking-[0.2em] text-royal">Main Menu</p>
        <h1 className="font-display text-3xl font-semibold text-navy md:text-4xl">
          Selamat datang, {session?.username?.split('_')[0] || 'Data Scientist'} 👋
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-steel">
          Pilih layanan yang ingin Anda gunakan.
        </p>
      </div>

      {mlflowError && (
        <div className="mt-5 animate-fade-up">
          <Banner kind="error" onClose={() => setMlflowError('')}>
            <span className="font-medium">{mlflowError}</span>
          </Banner>
        </div>
      )}

      {/* Dua kartu menu utama */}
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        {CARDS.map((c, i) => {
          const Icon = c.icon
          if (c.kind === 'mlflow') {
            return (
              <button
                key={c.kind}
                type="button"
                onClick={openLocalMlflow}
                disabled={checkingMlflow}
                style={{ animationDelay: `${i * 80}ms` }}
                className="group card animate-fade-up p-7 text-left transition-all hover:-translate-y-0.5 hover:shadow-card-hover disabled:cursor-wait disabled:opacity-75"
              >
                <div className={`mb-5 inline-grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br ${c.accent} text-white shadow-lg`}>
                  {checkingMlflow ? <Loader2 className="h-7 w-7 animate-spin" /> : <Icon className="h-7 w-7" strokeWidth={2} />}
                </div>
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <h2 className="font-display text-2xl font-semibold text-navy">{c.title}</h2>
                    <p className="mt-1 max-w-sm text-sm text-steel">{c.desc}</p>
                    <p className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-royal">
                      <ExternalLink className="h-3.5 w-3.5" /> {MLFLOW_UI_URL}
                    </p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-navy-300 transition group-hover:translate-x-1 group-hover:text-royal" />
                </div>
              </button>
            )
          }
          return (
            <Link
              key={c.to}
              to={c.to}
              style={{ animationDelay: `${i * 80}ms` }}
              className="group card animate-fade-up p-7 transition-all hover:-translate-y-0.5 hover:shadow-card-hover"
            >
              <div className={`mb-5 inline-grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br ${c.accent} text-white shadow-lg`}>
                <Icon className="h-7 w-7" strokeWidth={2} />
              </div>
              <div className="flex items-center justify-between gap-2">
                <div>
                  <h2 className="font-display text-2xl font-semibold text-navy">{c.title}</h2>
                  <p className="mt-1 max-w-sm text-sm text-steel">{c.desc}</p>
                </div>
                <ArrowRight className="h-5 w-5 text-navy-300 transition group-hover:translate-x-1 group-hover:text-royal" />
              </div>
            </Link>
          )
        })}
      </div>
    </AppShell>
  )
}
