import { Link } from 'react-router-dom'
import { Hammer, Activity, ArrowRight, Database, GitBranch, Boxes } from 'lucide-react'
import AppShell from '../components/AppShell.jsx'
import { useAuth } from '../lib/auth.jsx'

const CARDS = [
  {
    to: '/app/mlflow',
    icon: Hammer,
    title: 'Build Model',
    desc: 'Jalankan Service ML Flow: preprocessing data & modeling dari dataset DVC hingga menghasilkan artifact preprocessing dan model.',
    points: ['Preprocessing 17 tahapan', 'Training & tuning', 'Simpan .pkl ke Docker Volume + DVC'],
    accent: 'from-royal to-sky',
  },
  {
    to: '/app/monitoring',
    icon: Activity,
    title: 'Monitoring Model',
    desc: 'Kelola pasangan Model + Preprocessing, evaluasi performa, pilih model deployment, dan pantau skor prediksi testing.',
    points: ['Management Model + Preprocessing', 'Evaluasi (ROC AUC, dsb.)', 'Monitoring skor & histori testing'],
    accent: 'from-teal to-sky',
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
              <ArrowRight className="h-5 w-5 text-navy-300 transition-all group-hover:translate-x-1 group-hover:text-royal" />
            </div>
            <p className="mt-2 text-sm leading-relaxed text-steel">{c.desc}</p>
            <ul className="mt-5 space-y-2">
              {c.points.map((p) => (
                <li key={p} className="flex items-center gap-2.5 text-sm text-navy-600">
                  <span className="h-1.5 w-1.5 rounded-full bg-teal" />
                  {p}
                </li>
              ))}
            </ul>
          </Link>
        ))}
      </div>

      {/* Strip arsitektur */}
      <div className="mt-8 grid animate-fade-up gap-4 rounded-2xl border border-line bg-white p-6 sm:grid-cols-3">
        {[
          { icon: Database, t: 'DVC + Google Drive', d: 'defaultCreditCardClients.xls' },
          { icon: GitBranch, t: 'MLflow Tracking', d: 'Eksperimen & registry' },
          { icon: Boxes, t: 'Docker Volume', d: 'preprocessing.pkl · model.pkl' },
        ].map((x) => (
          <div key={x.t} className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-navy-50 text-navy">
              <x.icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-navy">{x.t}</p>
              <p className="text-xs text-steel">{x.d}</p>
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  )
}
