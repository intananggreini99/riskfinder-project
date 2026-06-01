import { CheckCircle2, AlertTriangle, X, Info } from 'lucide-react'
import { useEffect } from 'react'

/** Kartu statistik ringkas dengan ikon. */
export function StatCard({ icon: Icon, label, value, hint, accent = 'royal' }) {
  const accents = {
    royal: 'text-royal bg-royal/10',
    teal: 'text-teal-600 bg-teal/10',
    sky: 'text-sky-600 bg-sky/10',
    navy: 'text-navy bg-navy-100',
    risk: 'text-risk-high bg-risk-high-bg',
  }
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[13px] font-semibold text-steel">{label}</p>
          <p className="mt-1 font-display text-3xl font-semibold text-navy tabular-nums">{value}</p>
          {hint && <p className="mt-1 text-xs text-navy-300">{hint}</p>}
        </div>
        {Icon && (
          <div className={`grid h-11 w-11 place-items-center rounded-xl ${accents[accent]}`}>
            <Icon className="h-5 w-5" strokeWidth={2.2} />
          </div>
        )}
      </div>
    </div>
  )
}

/** Badge prediksi (Default / Non-Default). */
export function RiskBadge({ label }) {
  const isDefault = label === 1 || label === 'Default'
  return (
    <span
      className={`chip ${
        isDefault ? 'bg-risk-high-bg text-risk-high' : 'bg-risk-low-bg text-risk-low'
      }`}
    >
      {isDefault ? <AlertTriangle className="h-3.5 w-3.5" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
      {isDefault ? 'DEFAULT (1)' : 'NON-DEFAULT (0)'}
    </span>
  )
}

/** Judul section dengan garis aksen. */
export function SectionTitle({ eyebrow, title, desc, right }) {
  return (
    <div className="mb-6 flex items-end justify-between gap-4">
      <div>
        {eyebrow && (
          <p className="mb-1.5 text-xs font-bold uppercase tracking-[0.2em] text-royal">{eyebrow}</p>
        )}
        <h2 className="font-display text-2xl font-semibold text-navy md:text-3xl">{title}</h2>
        {desc && <p className="mt-1.5 max-w-2xl text-sm text-steel">{desc}</p>}
        <div className="rule-accent mt-3" />
      </div>
      {right}
    </div>
  )
}

/** Skeleton loader. */
export function Skeleton({ className = 'h-4 w-full' }) {
  return <div className={`skeleton rounded-md bg-navy-100 ${className}`} />
}

/** Banner notifikasi (error/success/info). */
export function Banner({ kind = 'info', children, onClose }) {
  const map = {
    error: { cls: 'border-risk-high/30 bg-risk-high-bg text-risk-high', Icon: AlertTriangle },
    success: { cls: 'border-teal/30 bg-risk-low-bg text-risk-low', Icon: CheckCircle2 },
    info: { cls: 'border-royal/20 bg-royal/5 text-royal', Icon: Info },
  }
  const { cls, Icon } = map[kind]
  return (
    <div className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm ${cls}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">{children}</div>
      {onClose && (
        <button onClick={onClose} className="shrink-0 opacity-60 hover:opacity-100">
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}

/** Toast yang menutup sendiri. */
export function Toast({ message, onDone, ms = 2600 }) {
  useEffect(() => {
    const t = setTimeout(onDone, ms)
    return () => clearTimeout(t)
  }, [onDone, ms])
  if (!message) return null
  return (
    <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 animate-fade-up">
      <div className="flex items-center gap-2 rounded-xl bg-navy px-4 py-3 text-sm font-medium text-white shadow-card-hover">
        <CheckCircle2 className="h-4 w-4 text-teal-400" />
        {message}
      </div>
    </div>
  )
}

/** Spinner inline. */
export function Spinner({ className = 'h-4 w-4' }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
    </svg>
  )
}

/** Format angka ringkas (NT$). */
export function fmt(n) {
  if (n === null || n === undefined || n === '') return '—'
  const num = Number(n)
  if (Number.isNaN(num)) return String(n)
  return num.toLocaleString('en-US')
}
