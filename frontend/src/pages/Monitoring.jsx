import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Boxes,
  Activity,
  Layers,
  Cpu,
  Plus,
  CheckCircle2,
  Rocket,
  TrendingUp,
  TrendingDown,
  ChevronRight,
  BadgeCheck,
  Loader2,
} from 'lucide-react'
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
} from 'recharts'
import AppShell from '../components/AppShell.jsx'
import { SectionTitle, StatCard, Banner, Toast } from '../components/ui.jsx'
import { dsApi, errMessage } from '../lib/api.js'
import { POSITIVE_THRESHOLD } from '../lib/monitoringDemo.js'

const NAV = [
  { id: 'management', label: 'Management Model', icon: Boxes },
  { id: 'monitoring', label: 'Monitoring Model', icon: Activity },
]

const EMPTY_TESTING = {
  avg_score: 0,
  total: 0,
  history: [],
}

export default function Monitoring() {
  const [view, setView] = useState('management')
  const [models, setModels] = useState([])
  const [preps, setPreps] = useState([])
  const [pairs, setPairs] = useState([])
  const [testing, setTesting] = useState(EMPTY_TESTING)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [toast, setToast] = useState('')

  async function loadMonitoringData(cancelled = () => false) {
    setLoading(true)
    setLoadError('')

    try {
      const [m, p, pr, t] = await Promise.all([
        dsApi.get('/monitoring/models'),
        dsApi.get('/monitoring/preprocessings'),
        dsApi.get('/monitoring/pairs'),
        dsApi.get('/monitoring/testing-history'),
      ])

      if (cancelled()) return

      setModels(Array.isArray(m.data) ? m.data : [])
      setPreps(Array.isArray(p.data) ? p.data : [])
      setPairs(Array.isArray(pr.data) ? pr.data : [])
      setTesting(t.data || EMPTY_TESTING)
    } catch (e) {
      if (cancelled()) return

      console.error('Gagal memuat monitoring dari ds-service:', e)

      setModels([])
      setPreps([])
      setPairs([])
      setTesting(EMPTY_TESTING)
      setLoadError(
        `Gagal memuat data monitoring dari backend. ${errMessage(e)}. ` +
          'Pastikan VITE_DS_API_URL benar dan ds-service memakai DATABASE_URL Neon yang sama dengan ca-service.'
      )
    } finally {
      if (!cancelled()) setLoading(false)
    }
  }

  useEffect(() => {
    let cancel = false
    loadMonitoringData(() => cancel)
    return () => { cancel = true }
  }, [])

  return (
    <AppShell>
      <div className="grid gap-6 lg:grid-cols-[230px_1fr]">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <p className="mb-3 px-1 text-xs font-bold uppercase tracking-[0.18em] text-steel">
            Monitoring
          </p>

          <nav className="flex gap-2 lg:flex-col">
            {NAV.map((n) => {
              const active = view === n.id

              return (
                <button
                  key={n.id}
                  onClick={() => setView(n.id)}
                  className={`flex flex-1 items-center gap-2.5 rounded-xl px-3.5 py-3 text-sm font-semibold transition lg:flex-none ${
                    active
                      ? 'bg-navy text-white shadow-card'
                      : 'border border-line bg-white text-navy-600 hover:bg-navy-50'
                  }`}
                >
                  <n.icon className={`h-4.5 w-4.5 ${active ? 'text-teal-400' : 'text-navy-400'}`} />
                  {n.label}
                </button>
              )
            })}
          </nav>

          <div className="mt-4 hidden rounded-xl border border-line bg-white p-4 lg:block">
            <p className="text-[11px] font-bold uppercase tracking-wide text-steel">
              Model deployment
            </p>

            {pairs.find((p) => p.active) ? (
              <div className="mt-2">
                <p className="flex items-center gap-1.5 text-sm font-bold text-navy">
                  <BadgeCheck className="h-4 w-4 text-teal-600" />
                  {pairs.find((p) => p.active).name}
                </p>
                <p className="mt-1 text-xs text-steel">Aktif pada FastAPI · Credit Analysis</p>
              </div>
            ) : (
              <p className="mt-2 text-xs text-steel">Belum ada pasangan aktif.</p>
            )}
          </div>
        </aside>

        <div className="min-w-0">
          {loadError && (
            <div className="mb-5">
              <Banner kind="error" onClose={() => setLoadError('')}>
                {loadError}
              </Banner>
            </div>
          )}

          {loading ? (
            <div className="card flex items-center justify-center gap-3 p-10 text-sm font-medium text-steel">
              <Loader2 className="h-5 w-5 animate-spin" />
              Memuat data dari database…
            </div>
          ) : view === 'management' ? (
            <ManagementView
              models={models}
              preps={preps}
              pairs={pairs}
              setPairs={setPairs}
              onToast={setToast}
            />
          ) : (
            <MonitoringView testing={testing} />
          )}
        </div>
      </div>

      <Toast message={toast} onDone={() => setToast('')} />
    </AppShell>
  )
}

function ManagementView({ models, preps, pairs, setPairs, onToast }) {
  const navigate = useNavigate()
  const [selModel, setSelModel] = useState('')
  const [selPrep, setSelPrep] = useState('')
  const [err, setErr] = useState('')

  async function createPair() {
    setErr('')

    if (!selModel || !selPrep) {
      setErr('Pilih satu model dan satu preprocessing untuk membuat pasangan.')
      return
    }

    const exists = pairs.some((x) => x.model === selModel && x.preprocessing === selPrep)

    if (exists) {
      setErr('Pasangan tersebut sudah ada.')
      return
    }

    try {
      const { data } = await dsApi.post('/monitoring/pairs', {
        model: selModel,
        preprocessing: selPrep,
      })

      setPairs([...pairs, data])
      setSelModel('')
      setSelPrep('')
      onToast('Pasangan Model + Preprocessing berhasil dibuat.')
    } catch (e) {
      setErr(`Gagal membuat pasangan di database: ${errMessage(e)}`)
    }
  }

  async function deploy(id) {
    try {
      await dsApi.post(`/monitoring/pairs/${id}/deploy`)
      setPairs(pairs.map((p) => ({ ...p, active: p.id === id })))
      onToast('Pasangan dipilih sebagai model deployment FastAPI.')
    } catch (e) {
      setErr(`Gagal deploy pasangan model: ${errMessage(e)}`)
    }
  }

  return (
    <div className="animate-fade-in">
      <SectionTitle title="Model & Preprocessing Artifacts Management" />

      <div className="grid gap-5 md:grid-cols-2">
        <ArtifactColumn
          title="Model Artifacts"
          icon={Cpu}
          items={models}
          selected={selModel}
          onSelect={setSelModel}
          render={(m) => (
            <>
              <p className="font-mono text-sm font-semibold text-navy">{m.id}</p>
              <p className="text-xs text-steel">{m.algo} · ROC AUC {m.roc_auc}</p>
            </>
          )}
        />

        <ArtifactColumn
          title="Preprocessing Artifacts"
          icon={Layers}
          items={preps}
          selected={selPrep}
          onSelect={setSelPrep}
          render={(p) => (
            <>
              <p className="font-mono text-sm font-semibold text-navy">{p.id}</p>
              <p className="text-xs text-steel">{p.features} fitur final</p>
            </>
          )}
        />
      </div>

      <div className="mt-5 card p-5">
        <p className="mb-3 text-sm font-bold text-navy">Building a Machine Learning Pipeline</p>

        <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-end">
          <div className="flex flex-1 items-center gap-3">
            <span className="chip bg-navy-100 text-navy">{selModel || 'pilih model'}</span>
            <Plus className="h-4 w-4 text-steel" />
            <span className="chip bg-navy-100 text-navy">{selPrep || 'pilih preprocessing'}</span>
          </div>

          <button onClick={createPair} className="btn-accent btn-sm">
            <Plus className="h-4 w-4" /> Build
          </button>
        </div>

        {err && (
          <div className="mt-3">
            <Banner kind="error" onClose={() => setErr('')}>
              {err}
            </Banner>
          </div>
        )}
      </div>

      <div className="mt-6">
        <p className="mb-3 text-sm font-bold text-navy">List Machine Learning Pipeline</p>

        <div className="space-y-3">
          {pairs.length === 0 && (
            <div className="card p-8 text-center text-sm text-steel">
              Belum ada pasangan model dari database.
            </div>
          )}

          {pairs.map((p) => (
            <div
              key={p.id}
              className="group card flex items-center gap-4 p-4 transition hover:shadow-card-hover"
            >
              <button
                onClick={() => navigate(`/app/monitoring/evaluate/${p.id}`)}
                className="flex flex-1 items-center gap-4 text-left"
              >
                <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-royal to-sky text-white">
                  <Layers className="h-5 w-5" />
                </div>

                <div className="min-w-0">
                  <p className="flex items-center gap-2 font-semibold text-navy">
                    {p.name}
                    {p.active && (
                      <span className="chip bg-teal/10 text-teal-600">
                        <CheckCircle2 className="h-3 w-3" /> aktif
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-steel">
                    ROC AUC (test) {p.metrics?.roc_auc_test} · klik untuk evaluasi
                  </p>
                </div>
              </button>

              <div className="flex items-center gap-2">
                {!p.active && (
                  <button onClick={() => deploy(p.id)} className="btn-ghost btn-sm">
                    <Rocket className="h-4 w-4" /> Deploy
                  </button>
                )}

                <ChevronRight className="h-5 w-5 text-navy-200 transition group-hover:translate-x-0.5 group-hover:text-royal" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ArtifactColumn({ title, icon: Icon, items, selected, onSelect, render }) {
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-2.5 border-b border-line bg-navy-50/60 px-4 py-3">
        <Icon className="h-4 w-4 text-royal" />
        <p className="text-sm font-bold text-navy">{title}</p>
        <span className="ml-auto chip bg-white text-steel">{items.length}</span>
      </div>

      <div className="space-y-2 p-3">
        {items.length === 0 && (
          <p className="p-4 text-center text-sm text-steel">Belum ada data dari database.</p>
        )}

        {items.map((it) => {
          const active = selected === it.id

          return (
            <button
              key={it.id}
              onClick={() => onSelect(it.id)}
              className={`w-full rounded-xl border p-3 text-left transition ${
                active
                  ? 'border-royal bg-royal/5 shadow-ring'
                  : 'border-line hover:bg-navy-50'
              }`}
            >
              {render(it)}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function MonitoringView({ testing }) {
  const data = testing || EMPTY_TESTING

  const positives = useMemo(
    () => data.history.filter((h) => Number(h.score) >= POSITIVE_THRESHOLD),
    [data]
  )

  const negatives = useMemo(
    () => data.history.filter((h) => Number(h.score) < POSITIVE_THRESHOLD),
    [data]
  )

  const chart = useMemo(
    () => [...data.history].reverse().map((h, i) => ({
      name: `t${i + 1}`,
      score: Number(Number(h.score).toFixed(4)),
    })),
    [data]
  )

  return (
    <div className="animate-fade-in">
      <SectionTitle title="Monitoring Model Deployment" />

      {data.total === 0 && (
        <div className="mb-5">
          <Banner kind="info">
            Belum ada data testing tersimpan di PostgreSQL/Neon.
            Lakukan prediksi melalui Credit Analysis dan pastikan response API memiliki testing_id.
          </Banner>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          icon={Activity}
          label="Rata-rata Prediction Score"
          value={Number(data.avg_score || 0).toFixed(4)}
          accent="royal"
          hint={`dari ${data.total || 0} testing`}
        />

        <StatCard
          icon={TrendingUp}
          label="Predicted Positive"
          value={positives.length}
          accent="risk"
          hint={`score ≥ ${POSITIVE_THRESHOLD}`}
        />

        <StatCard
          icon={TrendingDown}
          label="Predicted Negative"
          value={negatives.length}
          accent="teal"
          hint={`score < ${POSITIVE_THRESHOLD}`}
        />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <HistoryGroup
          title="Predicted Positive"
          hint={`Prediction score ≥ ${POSITIVE_THRESHOLD}`}
          tone="high"
          rows={positives}
        />

        <HistoryGroup
          title="Predicted Negative"
          hint={`Prediction score < ${POSITIVE_THRESHOLD}`}
          tone="low"
          rows={negatives}
        />
      </div>

      <div className="mt-6 card p-6">
        <p className="mb-1 text-sm font-bold text-navy">Tren Prediction Score per Testing</p>
        <p className="mb-5 text-xs text-steel">
          Garis ambang {POSITIVE_THRESHOLD} memisahkan prediksi positif &amp; negatif.
        </p>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chart} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
              <defs>
                <linearGradient id="sc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#1E5AA8" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#1E5AA8" stopOpacity={0} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#E6ECF3" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: '#5B6B7F', fontSize: 12 }} axisLine={{ stroke: '#E6ECF3' }} tickLine={false} />
              <YAxis domain={[0, 1]} tick={{ fill: '#5B6B7F', fontSize: 12 }} axisLine={false} tickLine={false} />

              <Tooltip
                contentStyle={{ borderRadius: 12, border: '1px solid #E6ECF3', fontSize: 13 }}
                labelStyle={{ color: '#0A2540', fontWeight: 700 }}
              />

              <ReferenceLine
                y={POSITIVE_THRESHOLD}
                stroke="#E11D48"
                strokeDasharray="5 4"
                label={{
                  value: `ambang ${POSITIVE_THRESHOLD}`,
                  fill: '#E11D48',
                  fontSize: 11,
                  position: 'insideTopRight',
                }}
              />

              <Area
                type="monotone"
                dataKey="score"
                stroke="#1E5AA8"
                strokeWidth={2.4}
                fill="url(#sc)"
                dot={{ r: 3, fill: '#1E5AA8' }}
                activeDot={{ r: 5 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function HistoryGroup({ title, hint, tone, rows }) {
  const dot = tone === 'high' ? 'bg-risk-high' : 'bg-risk-low'

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
        <div className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${dot}`} />
          <p className="text-sm font-bold text-navy">{title}</p>
        </div>
        <span className="text-xs text-steel">{hint}</span>
      </div>

      <div className="max-h-[420px] divide-y divide-line overflow-y-auto">
        {rows.length === 0 && (
          <p className="p-6 text-center text-sm text-steel">Belum ada data.</p>
        )}

        {rows.map((r) => (
          <div key={r.id} className="p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className={`font-mono text-sm font-bold ${tone === 'high' ? 'text-risk-high' : 'text-risk-low'}`}>
                {Number(r.score).toFixed(4)}
              </span>
              <span className="text-xs text-steel">{r.at}</span>
            </div>

            <pre className="overflow-x-auto rounded-lg bg-navy-50 p-2.5 font-mono text-[11px] leading-relaxed text-navy-600">
{JSON.stringify(r.input, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  )
}