import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  UserPlus, Trash2, Wand2, Play, Users, ArrowLeft, ListPlus, X, Loader2, AlertCircle,
} from 'lucide-react'
import AppShell from '../components/AppShell.jsx'
import { SectionTitle, Banner, fmt } from '../components/ui.jsx'
import { caApi, errMessage } from '../lib/api.js'
import { FIELD_GROUPS, ALL_KEYS, SAMPLE_BORROWER, SAMPLE_RISKY } from '../lib/fields.js'

const emptyForm = () => Object.fromEntries(ALL_KEYS.map((k) => [k, '']))

export default function EntryData() {
  const navigate = useNavigate()
  const [form, setForm] = useState(emptyForm())
  const [queue, setQueue] = useState([]) // peminjam yang sudah ditambahkan
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function setField(key, val) {
    setForm((f) => ({ ...f, [key]: val }))
  }

  function fillSample(which) {
    setForm(which === 'risky' ? { ...SAMPLE_RISKY } : { ...SAMPLE_BORROWER })
    setError('')
  }

  function validate(data) {
    const missing = ALL_KEYS.filter((k) => data[k] === '' || data[k] === null || data[k] === undefined)
    return missing
  }

  function toNumbers(data) {
    const out = {}
    for (const k of ALL_KEYS) out[k] = Number(data[k])
    return out
  }

  // "Input Data Lagi" → simpan form saat ini ke antrean, reset form
  function addToQueue() {
    const missing = validate(form)
    if (missing.length) {
      setError(`Lengkapi ${missing.length} field yang masih kosong sebelum menambah peminjam.`)
      return
    }
    setQueue((q) => [...q, toNumbers(form)])
    setForm(emptyForm())
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function removeFromQueue(idx) {
    setQueue((q) => q.filter((_, i) => i !== idx))
  }

  // "Hasil Analysis" → kirim seluruh peminjam (antrean + form aktif jika terisi) ke /predict
  async function analyze() {
    setError('')
    const borrowers = [...queue]

    // sertakan form aktif bila terisi penuh
    const missing = validate(form)
    if (missing.length !== ALL_KEYS.length) {
      // form sebagian/penuh terisi
      if (missing.length === 0) {
        borrowers.push(toNumbers(form))
      } else {
        setError('Form peminjam aktif belum lengkap. Lengkapi, kosongkan, atau tambahkan ke daftar dahulu.')
        return
      }
    }

    if (borrowers.length === 0) {
      setError('Belum ada data peminjam untuk dianalisis.')
      return
    }

    setSubmitting(true)
    try {
      let results
      try {
        // Batch endpoint
        const { data } = await caApi.post('/predict/batch', { borrowers })
        results = data.results
      } catch (batchErr) {
        // Fallback: panggil /predict satu per satu
        if (batchErr?.response?.status === 404) {
          results = []
          for (const b of borrowers) {
            const { data } = await caApi.post('/predict', b)
            results.push({ input: b, ...data })
          }
        } else {
          throw batchErr
        }
      }
      sessionStorage.setItem('rf_results', JSON.stringify(results))
      navigate('/app/result', { state: { results } })
    } catch (e) {
      // Fallback demo (backend offline): prediksi lokal heuristik agar UI dapat didemokan
      const results = borrowers.map((b) => mockPredict(b))
      sessionStorage.setItem('rf_results', JSON.stringify(results))
      console.warn('Backend prediksi tidak terjangkau, memakai prediksi demo:', errMessage(e))
      navigate('/app/result', { state: { results, demo: true } })
    } finally {
      setSubmitting(false)
    }
  }

  const totalBorrowers = queue.length + (validate(form).length === 0 ? 1 : 0)

  return (
    <AppShell>
      <Link to="/login" className="mb-5 inline-flex items-center gap-1.5 text-sm font-medium text-steel hover:text-navy"
        onClick={(e) => { /* hanya tautan visual balik; biarkan default */ }}>
        <ArrowLeft className="h-4 w-4" /> Beranda
      </Link>

      <SectionTitle eyebrow="Credit Analysis" title="Entry Data Peminjam"/>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* Form */}
        <div className="space-y-5">
          {FIELD_GROUPS.map((group, gi) => (
            <div key={group.id} className="card animate-fade-up p-6" style={{ animationDelay: `${gi * 50}ms` }}>
              <div className="mb-4">
                <h3 className="font-display text-lg font-semibold text-navy">{group.title}</h3>
                <p className="text-xs text-steel">{group.desc}</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {group.fields.map((f) => (
                  <Field key={f.key} f={f} value={form[f.key]} onChange={(v) => setField(f.key, v)} />
                ))}
              </div>
            </div>
          ))}

          {error && <Banner kind="error" onClose={() => setError('')}>{error}</Banner>}

          <div className="flex flex-wrap gap-3">
            <button onClick={addToQueue} className="btn-ghost">
              <ListPlus className="h-4 w-4" /> Input Data Lagi
            </button>
            <button onClick={analyze} disabled={submitting} className="btn-accent flex-1 sm:flex-none">
              {submitting ? <><Loader2 className="h-4 w-4 animate-spin" /> Menganalisis…</>
                : <><Play className="h-4 w-4" /> Hasil Analysis{totalBorrowers > 1 ? ` (${totalBorrowers} peminjam)` : ''}</>}
            </button>
          </div>
        </div>

        {/* Panel antrean peminjam */}
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <div className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-line bg-navy-50/60 px-4 py-3.5">
              <p className="flex items-center gap-2 text-sm font-bold text-navy">
                <Users className="h-4 w-4 text-royal" /> Daftar Peminjam
              </p>
              <span className="chip bg-navy text-white">{queue.length}</span>
            </div>
            <div className="max-h-[460px] space-y-2 overflow-y-auto p-3">
              {queue.length === 0 && (
                <div className="px-3 py-10 text-center">
                  <UserPlus className="mx-auto mb-2 h-8 w-8 text-navy-200" />
                  <p className="text-sm text-steel">Belum ada peminjam ditambahkan.</p>
                  <p className="mt-1 text-xs text-navy-300">Gunakan “Input Data Lagi” untuk antre beberapa peminjam.</p>
                </div>
              )}
              {queue.map((b, i) => (
                <div key={i} className="group flex items-center gap-3 rounded-xl border border-line p-3">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-navy text-xs font-bold text-white">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-navy">Peminjam #{i + 1}</p>
                    <p className="truncate text-xs text-steel">
                      Plafon {fmt(b.LIMIT_BAL)} · Usia {b.AGE} · PAY_0 {b.PAY_0}
                    </p>
                  </div>
                  <button onClick={() => removeFromQueue(i)} className="shrink-0 text-navy-300 transition hover:text-risk-high">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
            {queue.length > 0 && (
              <div className="border-t border-line p-3">
                <button onClick={() => setQueue([])} className="flex w-full items-center justify-center gap-2 rounded-lg py-2 text-xs font-medium text-steel hover:bg-navy-50 hover:text-risk-high">
                  <X className="h-3.5 w-3.5" /> Kosongkan daftar
                </button>
              </div>
            )}
          </div>

          <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-royal/15 bg-royal/5 p-3.5 text-xs text-royal">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>Setiap entry diproses sebagai satu baris data testing: preprocessing identik training → prediksi model aktif → disimpan ke PostgreSQL.</p>
          </div>
        </aside>
      </div>
    </AppShell>
  )
}

function Field({ f, value, onChange }) {
  return (
    <div>
      <label className="label" htmlFor={f.key}>{f.label}</label>
      {f.type === 'select' ? (
        <select id={f.key} className="field appearance-none bg-[length:16px] bg-[right_0.75rem_center] bg-no-repeat pr-9"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%235B6B7F' stroke-width='2.5'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E\")" }}
          value={value} onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}>
          <option value="">Pilih…</option>
          {f.options.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
        </select>
      ) : (
        <div className="relative">
          <input id={f.key} type="number" className={`field ${f.unit ? 'pr-12' : ''}`}
            placeholder={f.placeholder} min={f.min} max={f.max} value={value}
            onChange={(e) => onChange(e.target.value)} />
          {f.unit && <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-navy-300">{f.unit}</span>}
        </div>
      )}
    </div>
  )
}

// Prediksi heuristik lokal untuk mode demo (saat backend belum tersedia)
function mockPredict(b) {
  const lateMonths = ['PAY_0', 'PAY_2', 'PAY_3', 'PAY_4', 'PAY_5', 'PAY_6'].filter((k) => Number(b[k]) > 0).length
  const maxDelay = Math.max(...['PAY_0', 'PAY_2', 'PAY_3', 'PAY_4', 'PAY_5', 'PAY_6'].map((k) => Number(b[k])))
  const util = (Number(b.BILL_AMT1) || 0) / ((Number(b.LIMIT_BAL) || 1) + 1)
  let z = -1.1 + 0.55 * lateMonths + 0.18 * Math.max(maxDelay, 0) + 0.9 * Math.min(util, 1.5) - 0.000001 * (Number(b.LIMIT_BAL) || 0)
  const score = 1 / (1 + Math.exp(-z))
  const label = score >= 0.5 ? 1 : 0
  return { input: b, prediction_label: label, prediction_score: Number(score.toFixed(4)), status: label === 1 ? 'Default' : 'Non-Default' }
}
