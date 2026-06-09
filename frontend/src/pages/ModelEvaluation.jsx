import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { ArrowLeft, GitCompare, Grid3x3, FileText, Gauge, Layers } from 'lucide-react'
import AppShell from '../components/AppShell.jsx'
import { SectionTitle, StatCard, Banner } from '../components/ui.jsx'
import { dsApi, errMessage } from '../lib/api.js'

export default function ModelEvaluation() {
  const { pairId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancel = false
    async function load() {
      try {
        setError('')
        const { data } = await dsApi.get(`/monitoring/pairs/${pairId}/evaluation`)
        if (!cancel) setData(data)
      } catch (e) {
        if (cancel) return
        setError(errMessage(e, 'Data evaluasi model belum tersedia di PostgreSQL.'))
        setData(null)
      }
    }
    load()
    return () => { cancel = true }
  }, [pairId])

  if (error) {
    return (
      <AppShell>
        <Link to="/app/monitoring" className="mb-5 inline-flex items-center gap-1.5 text-sm font-medium text-steel hover:text-navy">
          <ArrowLeft className="h-4 w-4" /> Management Model
        </Link>
        <Banner kind="error">
          <b>Evaluasi tidak dapat dimuat.</b> {error}
        </Banner>
      </AppShell>
    )
  }

  if (!data) {
    return <AppShell><div className="card h-96 animate-pulse" /></AppShell>
  }

  const { tn, fp, fn, tp } = data.confusion_matrix

  return (
    <AppShell>
      <Link to="/app/monitoring" className="mb-5 inline-flex items-center gap-1.5 text-sm font-medium text-steel hover:text-navy">
        <ArrowLeft className="h-4 w-4" /> Management Model
      </Link>

      <SectionTitle eyebrow="Evaluasi Model"
        title={<span className="inline-flex items-center gap-2"><Layers className="h-6 w-6 text-royal" />{data.pair_name}</span>}
        desc="Performa pasangan Model + Preprocessing pada data testing." />

      {/* Ringkasan skor */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Gauge} label="ROC AUC (Train)" value={data.roc_auc_train.toFixed(4)} accent="royal" />
        <StatCard icon={Gauge} label="ROC AUC (Test)" value={data.roc_auc_test.toFixed(4)} accent="teal" />
        <StatCard icon={GitCompare} label="Gap Train–Test" value={data.gap.toFixed(4)} accent="sky" hint={data.gap < 0.05 ? 'Generalisasi baik' : 'Indikasi overfit'} />
        <StatCard label="Akurasi" value={(((tp + tn) / (tp + tn + fp + fn)) * 100).toFixed(1) + '%'} accent="navy" />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        {/* Learning Curve ROC AUC */}
        <div className="card p-6">
          <div className="mb-1 flex items-center gap-2">
            <GitCompare className="h-4 w-4 text-royal" />
            <p className="text-sm font-bold text-navy">Learning Curve · ROC AUC</p>
          </div>
          <p className="mb-5 text-xs text-steel">
            Gap rata-rata Train–Test: <b className="text-navy">{data.gap.toFixed(4)}</b>
            {data.gap < 0.05 ? ' — kurva konvergen, model menggeneralisasi dengan baik.' : ' — perhatikan potensi overfitting.'}
          </p>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.learning_curve} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E6ECF3" vertical={false} />
                <XAxis dataKey="size" tick={{ fill: '#5B6B7F', fontSize: 12 }} axisLine={{ stroke: '#E6ECF3' }} tickLine={false} />
                <YAxis domain={[0.6, 0.95]} tick={{ fill: '#5B6B7F', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #E6ECF3', fontSize: 13 }} />
                <Legend wrapperStyle={{ fontSize: 13, paddingTop: 8 }} />
                <Line type="monotone" dataKey="train" name="Training" stroke="#1E5AA8" strokeWidth={2.4} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="test" name="Testing" stroke="#C9A227" strokeWidth={2.4} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confusion Matrix */}
        <div className="card p-6">
          <div className="mb-5 flex items-center gap-2">
            <Grid3x3 className="h-4 w-4 text-royal" />
            <p className="text-sm font-bold text-navy">Confusion Matrix</p>
          </div>
          <div className="mx-auto max-w-xs">
            <div className="mb-1.5 grid grid-cols-[auto_1fr_1fr] gap-1.5 text-center text-[11px] font-semibold text-steel">
              <span />
              <span>Pred 0</span>
              <span>Pred 1</span>
            </div>
            <div className="grid grid-cols-[auto_1fr_1fr] gap-1.5">
              <span className="flex items-center justify-center text-[11px] font-semibold text-steel [writing-mode:vertical-rl] rotate-180">Aktual 0</span>
              <CMCell value={tn} label="TN" tone="good" />
              <CMCell value={fp} label="FP" tone="bad" />
              <span className="flex items-center justify-center text-[11px] font-semibold text-steel [writing-mode:vertical-rl] rotate-180">Aktual 1</span>
              <CMCell value={fn} label="FN" tone="bad" />
              <CMCell value={tp} label="TP" tone="good" />
            </div>
          </div>
          <dl className="mt-6 space-y-2 text-sm">
            <Row k="True Negative (TN)" v={tn} />
            <Row k="False Positive (FP)" v={fp} />
            <Row k="False Negative (FN)" v={fn} />
            <Row k="True Positive (TP)" v={tp} />
          </dl>
        </div>
      </div>

      {/* Classification Report */}
      <div className="mt-6 card overflow-hidden">
        <div className="flex items-center gap-2 border-b border-line px-6 py-4">
          <FileText className="h-4 w-4 text-royal" />
          <p className="text-sm font-bold text-navy">Classification Report</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-navy-50/50 text-left text-xs font-semibold uppercase tracking-wide text-steel">
                <th className="px-6 py-3">Kelas</th>
                <th className="px-6 py-3 text-right">Precision</th>
                <th className="px-6 py-3 text-right">Recall</th>
                <th className="px-6 py-3 text-right">F1-Score</th>
                <th className="px-6 py-3 text-right">Support</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.classification_report.map((r) => (
                <tr key={r.label} className="hover:bg-navy-50/40">
                  <td className="px-6 py-3.5 font-medium text-navy">{r.label}</td>
                  <td className="px-6 py-3.5 text-right font-mono tabular-nums text-navy-600">{r.precision.toFixed(3)}</td>
                  <td className="px-6 py-3.5 text-right font-mono tabular-nums text-navy-600">{r.recall.toFixed(3)}</td>
                  <td className="px-6 py-3.5 text-right font-mono tabular-nums text-navy-600">{r.f1.toFixed(3)}</td>
                  <td className="px-6 py-3.5 text-right font-mono tabular-nums text-steel">{r.support.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  )
}

function CMCell({ value, label, tone }) {
  const cls = tone === 'good' ? 'bg-teal/10 text-teal-600 border-teal/20' : 'bg-risk-high-bg text-risk-high border-risk-high/20'
  return (
    <div className={`rounded-xl border p-4 text-center ${cls}`}>
      <p className="font-display text-2xl font-semibold tabular-nums">{value.toLocaleString()}</p>
      <p className="text-[11px] font-semibold opacity-80">{label}</p>
    </div>
  )
}

function Row({ k, v }) {
  return (
    <div className="flex items-center justify-between border-b border-line/60 pb-1.5">
      <dt className="text-steel">{k}</dt>
      <dd className="font-mono font-semibold text-navy tabular-nums">{v.toLocaleString()}</dd>
    </div>
  )
}