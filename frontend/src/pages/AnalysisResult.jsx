import { useMemo } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, RotateCcw, Users, AlertTriangle, CheckCircle2, ShieldAlert, Gauge, Database,
} from 'lucide-react'
import AppShell from '../components/AppShell.jsx'
import { SectionTitle, StatCard, RiskBadge, Banner, fmt } from '../components/ui.jsx'

export default function AnalysisResult() {
  const location = useLocation()
  const navigate = useNavigate()

  const results = useMemo(() => {
    if (location.state?.results) return location.state.results
    const raw = sessionStorage.getItem('rf_results')
    return raw ? JSON.parse(raw) : []
  }, [location.state])

  const isDemo = location.state?.demo

  const stats = useMemo(() => {
    const total = results.length
    const defaults = results.filter((r) => r.prediction_label === 1).length
    const avg = total ? results.reduce((s, r) => s + Number(r.prediction_score), 0) / total : 0
    return { total, defaults, nonDefaults: total - defaults, avg }
  }, [results])

  if (!results.length) {
    return (
      <AppShell>
        <div className="card mx-auto max-w-md p-10 text-center">
          <ShieldAlert className="mx-auto mb-3 h-10 w-10 text-navy-200" />
          <h2 className="font-display text-xl font-semibold text-navy">Belum ada hasil analisis</h2>
          <p className="mt-2 text-sm text-steel">Silakan masukkan data peminjam terlebih dahulu.</p>
          <Link to="/app/entry" className="btn-primary mt-5 inline-flex">Ke Entry Data</Link>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <Link to="/app/entry" className="mb-5 inline-flex items-center gap-1.5 text-sm font-medium text-steel hover:text-navy">
        <ArrowLeft className="h-4 w-4" /> Entry Data
      </Link>

      <SectionTitle eyebrow="Credit Analysis" title="Hasil Analysis"
        desc="Hasil prediksi gagal bayar (default) untuk tiap peminjam. Seluruh hasil telah dicatat ke PostgreSQL (skema snowflake)."
        right={
          <button onClick={() => navigate('/app/entry')} className="btn-ghost btn-sm">
            <RotateCcw className="h-4 w-4" /> Analisis lagi
          </button>
        } />

      {isDemo && (
        <div className="mb-5">
          <Banner kind="info">
            Mode demo: backend prediksi belum terjangkau, hasil dihitung dengan estimasi heuristik lokal.
            Setelah container Credit Analysis aktif, prediksi memakai <b>model_final.pkl</b> sungguhan.
          </Banner>
        </div>
      )}

      {/* Ringkasan */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Users} label="Total Peminjam" value={stats.total} accent="navy" />
        <StatCard icon={AlertTriangle} label="Diprediksi Default" value={stats.defaults} accent="risk" hint="label = 1" />
        <StatCard icon={CheckCircle2} label="Diprediksi Lancar" value={stats.nonDefaults} accent="teal" hint="label = 0" />
        <StatCard icon={Gauge} label="Rata-rata Skor" value={stats.avg.toFixed(4)} accent="royal" />
      </div>

      {/* Kartu hasil per peminjam */}
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {results.map((r, i) => (
          <ResultCard key={i} index={i + 1} r={r} />
        ))}
      </div>

      {/* Tabel ringkas */}
      <div className="mt-6 card overflow-hidden">
        <div className="flex items-center gap-2 border-b border-line px-6 py-4">
          <Database className="h-4 w-4 text-royal" />
          <p className="text-sm font-bold text-navy">Rekapitulasi Tersimpan</p>
          <span className="ml-auto text-xs text-steel">PostgreSQL · schema snowflake</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-navy-50/50 text-left text-xs font-semibold uppercase tracking-wide text-steel">
                <th className="px-6 py-3">#</th>
                <th className="px-6 py-3 text-right">Plafon</th>
                <th className="px-6 py-3 text-right">Usia</th>
                <th className="px-6 py-3 text-right">PAY_0</th>
                <th className="px-6 py-3 text-right">Skor</th>
                <th className="px-6 py-3 text-center">Hasil</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {results.map((r, i) => (
                <tr key={i} className="hover:bg-navy-50/40">
                  <td className="px-6 py-3.5 font-mono text-steel">{i + 1}</td>
                  <td className="px-6 py-3.5 text-right font-mono tabular-nums text-navy-600">{fmt(r.input.LIMIT_BAL)}</td>
                  <td className="px-6 py-3.5 text-right tabular-nums text-navy-600">{r.input.AGE}</td>
                  <td className="px-6 py-3.5 text-right tabular-nums text-navy-600">{r.input.PAY_0}</td>
                  <td className="px-6 py-3.5 text-right font-mono font-semibold tabular-nums text-navy">{Number(r.prediction_score).toFixed(4)}</td>
                  <td className="px-6 py-3.5 text-center"><RiskBadge label={r.prediction_label} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  )
}

function ResultCard({ index, r }) {
  const isDefault = r.prediction_label === 1
  const score = Number(r.prediction_score)
  const pct = Math.round(score * 100)

  return (
    <div className={`card overflow-hidden border-l-4 ${isDefault ? 'border-l-risk-high' : 'border-l-risk-low'}`}>
      <div className="flex items-center justify-between p-5">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-navy text-sm font-bold text-white">
            {index}
          </span>
          <div>
            <p className="font-display text-lg font-semibold text-navy">Peminjam #{index}</p>
            <p className="text-xs text-steel">
              Plafon {fmt(r.input.LIMIT_BAL)} · Usia {r.input.AGE} · {r.input.SEX === 1 ? 'Laki-laki' : 'Perempuan'}
            </p>
          </div>
        </div>
        <RiskBadge label={r.prediction_label} />
      </div>

      {/* Gauge skor */}
      <div className="px-5 pb-5">
        <div className="mb-1.5 flex items-center justify-between text-xs">
          <span className="font-semibold text-steel">Prediction Score</span>
          <span className={`font-mono font-bold ${isDefault ? 'text-risk-high' : 'text-risk-low'}`}>{score.toFixed(4)}</span>
        </div>
        <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-navy-100">
          <div className={`h-full rounded-full ${isDefault ? 'bg-gradient-to-r from-rose-400 to-risk-high' : 'bg-gradient-to-r from-teal to-risk-low'}`}
            style={{ width: `${pct}%` }} />
          {/* ambang 0.7 */}
          <div className="absolute top-0 h-full w-px bg-navy-400" style={{ left: '70%' }} title="ambang 0.7" />
        </div>
        <div className="mt-1 flex justify-between text-[10px] text-navy-300">
          <span>0.0</span><span>ambang 0.7</span><span>1.0</span>
        </div>

        <p className={`mt-4 rounded-xl px-3.5 py-2.5 text-sm font-medium ${isDefault ? 'bg-risk-high-bg text-risk-high' : 'bg-risk-low-bg text-risk-low'}`}>
          {isDefault
            ? `Berisiko gagal bayar — peluang default ${pct}%. Disarankan review manual / mitigasi.`
            : `Cenderung lancar — peluang default ${pct}%. Risiko kredit relatif rendah.`}
        </p>
      </div>
    </div>
  )
}
