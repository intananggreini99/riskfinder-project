import { Link } from 'react-router-dom'
import { Hammer, Activity, ArrowRight, Database, GitBranch, Boxes } from 'lucide-react'
import AppShell from '../components/AppShell.jsx'
import { useAuth } from '../lib/auth.jsx'

const CARDS = [
  {
    to: '/app/mlflow',
    icon: Hammer,
    title: 'Build Model',
    accent: 'from-royal to-gold-400',
  },
  {
    to: '/app/monitoring',
    icon: Activity,
    title: 'Monitoring Model',
    accent: 'from-navy to-royal',
  },
]

export default function MainMenu() {
  const { session } = useAuth()
  return (
    <AppShell>
      {/* Hero ringkas */}
      <div className="animate-fade-up">
        <p className="mb-1.5 text-xs font-bold uppercase tracking-[0.2em] text-royal">Main Menu</p>
        <h1 className="font-display text-3xl font-semibold text-navy md:text-4xl">
          Selamat datang, {session?.username?.split('_')[0] || 'Data Scientist'} 👋
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-steel">
          Pilih layanan yang ingin Anda gunakan. Seluruh artifact tersimpan terpusat di Docker Volume
          dan terversioning melalui DVC.
        </p>
      </div>

      {/* Dua kartu menu utama */}
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        {CARDS.map((c, i) => (
          <Link
            key={c.to}
            to={c.to}
            style={{ animationDelay: `${i * 80}ms` }}
            className="group card animate-fade-up p-7 transition-all hover:-translate-y-0.5 hover:shadow-card-hover"
          >
            <div
              className={`mb-5 inline-grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br ${c.accent} text-white shadow-lg`}
            >
              <c.icon className="h-7 w-7" strokeWidth={2} />
            </div>
            <div className="flex items-center gap-2">
              <h2 className="font-display text-2xl font-semibold text-navy">{c.title}</h2>
            </div>
          </Link>
        ))}
      </div>

    </AppShell>
  )
}
