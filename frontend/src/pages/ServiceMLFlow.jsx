import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Database, Play, Loader2, CheckCircle2, ArrowLeft, RotateCcw, Sparkles,
  Package, Cloud, HardDrive, FileCode2, FileText, Terminal, ExternalLink,
  FileSpreadsheet, GitBranch, FolderGit2, Boxes, Settings2, AlertTriangle, Info,
} from 'lucide-react'
import AppShell from '../components/AppShell.jsx'
import { SectionTitle, Banner, StatCard } from '../components/ui.jsx'
import { dsApi, errMessage, MLFLOW_UI_URL } from '../lib/api.js'

/* Tahapan yang dijalankan entry point `main` (sesuai Preprocessing_Modeling_EndToEnd.ipynb). */
const PIPELINE = [
  { phase: 'Preprocessing · Step 1–11', steps: [
    'Eliminasi non-prediktif & standarisasi nama', 'Handling duplicate', 'Tandai inkonsistensi → NaN',
    'Train–test split (stratified 70/30)', 'Imputasi modus per-kelas', 'Outlier IQR capping',
    'Feature extraction', 'Encoding (OHE/label)', 'Binning AGE', 'Feature selection (korelasi+ANOVA)',
    'Feature scaling (StandardScaler)',
  ]},
  { phase: 'Modeling · Step 12–17', steps: [
    'Compare models (RF/GB/Ada/XGB)', 'Hyperparameter tuning', 'Validation (holdout & K-fold)',
    'Evaluasi (ROC AUC, CM, report)', 'Finalisasi & prediksi',
    'Simpan artifact .pkl → Volume + DVC',
  ]},
]

const LANG_ICON = { python: FileCode2, yaml: FileText, text: FileText }

export default function ServiceMLFlow() {
  const [tab, setTab] = useState('project')          // project | mlflow
  const [spec, setSpec] = useState(null)
  const [active, setActive] = useState(0)
  const [cfg, setCfg] = useState({
    entry_point: 'main', test_size: 0.3, random_state: 42, n_trials: 80, model_version: '',
  })
  const [status, setStatus] = useState('idle')       // idle | running | success | error
  const [logs, setLogs] = useState('')
  const [result, setResult] = useState(null)
  const [offline, setOffline] = useState(false)
  const consoleRef = useRef(null)

  useEffect(() => {
    let cancel = false
    ;(async () => {
      try {
        const { data } = await dsApi.get('/mlflow/projects/spec')
        if (!cancel) setSpec(data)
      } catch (e) {
        if (!cancel) { setSpec(DEMO_SPEC); setOffline(true) }
      }
    })()
    return () => { cancel = true }
  }, [])

  useEffect(() => {
    if (consoleRef.current) consoleRef.current.scrollTop = consoleRef.current.scrollHeight
  }, [logs, status])

  const files = spec?.files || []
  const file = files[active] || files[0]
  const nextVersion = spec?.next_version || 'V1'
  const mlflowUrl = (MLFLOW_UI_URL || spec?.mlflow_ui_url || '').trim()
  const running = status === 'running'

  async function runProject() {
    setStatus('running'); setResult(null)
    const preview = cmdPreview(cfg)
    setLogs(`$ ${preview}\n[mlflow] menyiapkan project (env-manager: local)…\n[mlflow] menjalankan entry point '${cfg.entry_point}'…\n`)
    try {
      const { data } = await dsApi.post('/mlflow/projects/run', cfg)
      setLogs(data.logs || preview)
      setResult(data)
      setStatus(data.status === 'success' ? 'success' : 'error')
    } catch (e) {
      const demo = DEMO_RUN(cfg, nextVersion)
      setLogs(demo.logs); setResult(demo); setStatus('success'); setOffline(true)
      console.warn('Backend MLflow tidak terjangkau, memakai ringkasan demo:', errMessage(e))
    }
  }

  function reset() { setStatus('idle'); setLogs(''); setResult(null) }

  return (
    <AppShell>
      <Link to="/app/menu" className="mb-5 inline-flex items-center gap-1.5 text-sm font-medium text-steel hover:text-navy">
        <ArrowLeft className="h-4 w-4" /> Main Menu
      </Link>

      <SectionTitle
        eyebrow="Build Model"
        title="Service ML Flow · MLflow Projects"
        desc="Workbench MLflow: jalankan source code preprocessing & modeling sebagai MLflow Project untuk menghasilkan preprocessing & model versi baru yang tersimpan otomatis."
        right={
          <div className="flex items-center gap-2">
            {offline && (
              <span className="chip bg-gold-100 text-gold-700" title="Backend belum terjangkau — menampilkan mode contoh">
                <Info className="h-3.5 w-3.5" /> mode contoh
              </span>
            )}
            {status !== 'idle' && (
              <button onClick={reset} className="btn-ghost btn-sm"><RotateCcw className="h-4 w-4" /> Reset</button>
            )}
          </div>
        }
      />

      {/* Tab bar */}
      <div className="mb-6 inline-flex gap-1 rounded-xl border border-line bg-white p-1">
        <button onClick={() => setTab('project')} className={`tab ${tab === 'project' ? 'tab-active' : ''}`}>
          <FolderGit2 className="h-4 w-4" /> MLflow Project
        </button>
        <button onClick={() => setTab('mlflow')} className={`tab ${tab === 'mlflow' ? 'tab-active' : ''}`}>
          <GitBranch className="h-4 w-4" /> MLflow Tracking UI
        </button>
      </div>

      {tab === 'project' ? (
        <>
          {/* Workbench: explorer + run config */}
          <div className="grid gap-5 lg:grid-cols-[1.55fr_1fr]">
            {/* ---------- Project Explorer ---------- */}
            <div className="card overflow-hidden">
              <div className="flex flex-wrap items-center gap-3 border-b border-line bg-navy-50/60 px-5 py-3.5">
                <div className="grid h-9 w-9 place-items-center rounded-xl bg-white text-royal shadow-sm">
                  <FolderGit2 className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <p className="font-mono text-sm font-bold text-navy">{spec?.name || 'riskfinder-credit-risk'}</p>
                  <p className="text-xs text-steel">MLflow Project · entry points: {(spec?.entry_points || ['main']).join(', ')}</p>
                </div>
              </div>

              {/* File tabs */}
              <div className="flex flex-wrap gap-1 border-b border-line px-3 py-2">
                {files.map((f, i) => {
                  const Icon = LANG_ICON[f.language] || FileText
                  const on = i === active
                  return (
                    <button key={f.path} onClick={() => setActive(i)}
                      className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 font-mono text-xs transition ${
                        on ? 'bg-navy text-white' : 'text-navy-600 hover:bg-navy-50'
                      }`}>
                      <Icon className={`h-3.5 w-3.5 ${on ? 'text-gold-300' : 'text-navy-400'}`} />
                      {f.label}
                    </button>
                  )
                })}
              </div>

              {/* Code panel */}
              <CodePanel content={file?.content || ''} />

              <div className="flex items-start gap-2 border-t border-line bg-navy-50/40 px-5 py-3 text-xs text-steel">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-royal" />
                <span>
                  Inilah source code yang dieksekusi <code className="rounded bg-white px-1 py-0.5 font-mono text-[11px] text-navy">mlflow run</code>.
                  Ubah parameter eksekusi di panel <b>Run</b>; untuk mengubah logika pipeline, edit berkas ini di repo lalu build &amp; push ulang image.
                </span>
              </div>
            </div>

            {/* ---------- Run configuration ---------- */}
            <div className="space-y-5">
              <div className="card p-5">
                <p className="mb-4 flex items-center gap-2 text-sm font-bold text-navy">
                  <Settings2 className="h-4 w-4 text-royal" /> Konfigurasi Run
                </p>
                <div className="space-y-3.5">
                  <div>
                    <label className="label">Entry point</label>
                    <select disabled={running} className="field" value={cfg.entry_point}
                      onChange={(e) => setCfg({ ...cfg, entry_point: e.target.value })}>
                      <option value="main">main · preprocessing + modeling (Step 1–17)</option>
                      <option value="preprocessing">preprocessing · hanya Step 1–11</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Test size</label>
                    <input type="number" step="0.05" min="0.1" max="0.4" disabled={running} className="field"
                      value={cfg.test_size} onChange={(e) => setCfg({ ...cfg, test_size: parseFloat(e.target.value) })} />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="label">Random state</label>
                      <input type="number" disabled={running} className="field" value={cfg.random_state}
                        onChange={(e) => setCfg({ ...cfg, random_state: parseInt(e.target.value) })} />
                    </div>
                    <div>
                      <label className="label">N trials</label>
                      <input type="number" disabled={running || cfg.entry_point === 'preprocessing'} className="field"
                        value={cfg.n_trials} onChange={(e) => setCfg({ ...cfg, n_trials: parseInt(e.target.value) })} />
                    </div>
                  </div>
                  <div>
                    <label className="label">Label versi (opsional)</label>
                    <input type="text" disabled={running} placeholder={`kosong → otomatis ${nextVersion}`} className="field"
                      value={cfg.model_version} onChange={(e) => setCfg({ ...cfg, model_version: e.target.value })} />
                    <p className="mt-1.5 text-xs text-steel">
                      Menghasilkan <code className="font-mono text-[11px] text-navy">preprocessing_artifacts_{cfg.model_version || nextVersion}.pkl</code> &amp;{' '}
                      <code className="font-mono text-[11px] text-navy">best_credit_model_{cfg.model_version || nextVersion}.pkl</code>
                    </p>
                  </div>
                </div>

                {/* command preview */}
                <div className="mt-4 overflow-x-auto rounded-lg bg-navy-900 px-3 py-2.5 font-mono text-[11.5px] leading-relaxed text-gold-200">
                  <span className="text-navy-300">$ </span>{cmdPreview(cfg)}
                </div>

                <button onClick={runProject} disabled={running} className="btn-gold mt-4 w-full">
                  {running ? <><Loader2 className="h-4 w-4 animate-spin" /> Menjalankan…</> : <><Play className="h-4 w-4" /> Run MLflow Project</>}
                </button>
              </div>

              {/* Dataset source */}
              <div className="card overflow-hidden">
                <div className="flex items-center gap-3 border-b border-line bg-navy-50/60 px-5 py-3.5">
                  <div className="grid h-9 w-9 place-items-center rounded-xl bg-white text-royal shadow-sm">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-navy">Sumber Dataset · DVC</p>
                    <p className="text-xs text-steel">Remote: Google Drive (gdrive)</p>
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex items-center gap-3 rounded-xl border border-line p-3">
                    <FileSpreadsheet className="h-5 w-5 text-gold-600" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-mono text-xs font-medium text-navy">{spec?.dataset_file || 'defaultCreditCardClients.xls'}</p>
                      <p className="text-xs text-steel">30.000 baris · 23 fitur · target DEFAULT</p>
                    </div>
                    <span className="chip bg-gold-100 text-gold-700">tracked</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Tahapan entry point */}
          <div className="mt-5 card p-5">
            <p className="mb-4 flex items-center gap-2 text-sm font-bold text-navy">
              <Boxes className="h-4 w-4 text-royal" /> Tahapan entry point <code className="font-mono text-xs text-gold-700">main</code>
            </p>
            <div className="grid gap-x-8 gap-y-3 md:grid-cols-2">
              {PIPELINE.map((p) => (
                <div key={p.phase}>
                  <p className="mb-2 text-xs font-bold uppercase tracking-wider text-royal">{p.phase}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {p.steps.map((s) => (
                      <span key={s} className="chip border border-line bg-navy-50/60 text-navy-600">{s}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ---------- Console + hasil ---------- */}
          {status !== 'idle' && (
            <div className="mt-6 animate-fade-up space-y-5">
              <div className="card overflow-hidden">
                <div className="flex items-center justify-between border-b border-navy-700/40 bg-navy px-5 py-3">
                  <p className="flex items-center gap-2 text-sm font-bold text-white">
                    <Terminal className="h-4 w-4 text-gold-300" /> Konsol Eksekusi · mlflow run
                  </p>
                  <span className={`chip ${
                    status === 'running' ? 'bg-white/10 text-gold-200'
                    : status === 'success' ? 'bg-risk-low-bg text-risk-low'
                    : 'bg-risk-high-bg text-risk-high'
                  }`}>
                    {status === 'running' ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> berjalan</>
                      : status === 'success' ? <><CheckCircle2 className="h-3.5 w-3.5" /> selesai</>
                      : <><AlertTriangle className="h-3.5 w-3.5" /> gagal</>}
                  </span>
                </div>
                <pre ref={consoleRef} className="max-h-80 overflow-auto bg-navy-900 p-4 font-mono text-[12.5px] leading-relaxed text-navy-100">
{logs || '…'}{status === 'running' ? '\n▌' : ''}
                </pre>
              </div>

              {status === 'error' && (
                <Banner kind="error">
                  Run gagal. {result?.error || 'Periksa konsol di atas.'} {' '}
                  Pastikan dataset tersedia (DVC) dan PostgreSQL terhubung.
                </Banner>
              )}

              {status === 'success' && result && (
                <>
                  <Banner kind="success">
                    Run selesai{result.version ? ` (versi ${result.version})` : ''}. Artifact{' '}
                    <b>{result.artifacts?.preprocessing}</b> dan <b>{result.artifacts?.model}</b>{' '}
                    tersimpan otomatis ke Docker Volume &amp; DVC, serta terdaftar di Monitoring.
                  </Banner>

                  {result.metrics && (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                      <StatCard icon={Sparkles} label="ROC AUC (Test)" value={result.metrics.roc_auc_test} accent="teal" />
                      <StatCard icon={Sparkles} label="ROC AUC (Train)" value={result.metrics.roc_auc_train} accent="royal" />
                      <StatCard label="F1-Score" value={result.metrics.f1} accent="sky" />
                      <StatCard label="Gap Train–Test" value={result.metrics.gap} accent="navy" />
                    </div>
                  )}

                  <div className="grid gap-4 md:grid-cols-2">
                    {[
                      { name: result.artifacts?.preprocessing, label: 'Artifact Preprocessing', size: result.artifacts?.preprocessing_size },
                      { name: result.artifacts?.model, label: 'Artifact Model', size: result.artifacts?.model_size },
                    ].map((a) => (
                      <div key={a.label} className="card flex items-center gap-4 p-5">
                        <div className="grid h-12 w-12 place-items-center rounded-xl bg-navy text-gold-300">
                          <Package className="h-6 w-6" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold uppercase tracking-wide text-steel">{a.label}</p>
                          <p className="truncate font-mono text-sm font-medium text-navy">{a.name || '—'}</p>
                          {a.size && <p className="text-xs text-steel">{a.size}</p>}
                        </div>
                        <div className="flex flex-col items-end gap-1 text-xs text-steel">
                          <span className="flex items-center gap-1"><HardDrive className="h-3.5 w-3.5" /> Volume</span>
                          <span className="flex items-center gap-1"><Cloud className="h-3.5 w-3.5" /> DVC</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {result.datasets?.length > 0 && (
                    <div className="card p-5">
                      <p className="mb-3 text-sm font-bold text-navy">Set Data Tersimpan</p>
                      <div className="grid gap-3 sm:grid-cols-2">
                        {result.datasets.map((d) => (
                          <div key={d.name} className="flex items-center justify-between rounded-xl border border-line p-3.5">
                            <div>
                              <p className="font-mono text-sm font-medium text-navy">{d.name}</p>
                              <p className="text-xs text-steel">{Number(d.rows).toLocaleString()} baris</p>
                            </div>
                            <div className="flex gap-1.5">
                              <span className="chip bg-royal/10 text-royal">DVC</span>
                              <span className="chip bg-navy-100 text-navy">PostgreSQL</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-3">
                    <Link to="/app/monitoring" className="btn-primary">Lanjut ke Monitoring Model</Link>
                    {mlflowUrl && (
                      <button onClick={() => setTab('mlflow')} className="btn-ghost">
                        <GitBranch className="h-4 w-4" /> Lihat di MLflow Tracking UI
                      </button>
                    )}
                    <button onClick={runProject} className="btn-ghost"><RotateCcw className="h-4 w-4" /> Run lagi</button>
                  </div>
                </>
              )}
            </div>
          )}
        </>
      ) : (
        /* ---------- MLflow Tracking UI ---------- */
        <MlflowTab url={mlflowUrl} experiment={spec?.experiment} />
      )}
    </AppShell>
  )
}

/* ============================ Sub-komponen ============================ */

function CodePanel({ content }) {
  const lines = (content || '').replace(/\n$/, '').split('\n')
  return (
    <div className="max-h-[460px] overflow-auto bg-navy-900">
      <table className="w-full border-collapse font-mono text-[12.5px] leading-[1.55]">
        <tbody>
          {lines.map((ln, i) => (
            <tr key={i}>
              <td className="select-none border-r border-navy-700/50 px-3 py-0 text-right align-top text-navy-400">{i + 1}</td>
              <td className="whitespace-pre px-4 py-0 align-top text-navy-100">{ln || ' '}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MlflowTab({ url, experiment }) {
  const showFrame = url && !/^https?:\/\/localhost|127\.0\.0\.1/.test(url) || (url && window.location.hostname === 'localhost')
  return (
    <div className="card overflow-hidden animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-navy-50/60 px-5 py-3.5">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-white text-royal shadow-sm">
            <GitBranch className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold text-navy">MLflow Tracking UI</p>
            <p className="text-xs text-steel">Experiment: <span className="font-mono">{experiment || 'credit-risk-build'}</span></p>
          </div>
        </div>
        {url && (
          <a href={url} target="_blank" rel="noreferrer" className="btn-ghost btn-sm">
            <ExternalLink className="h-4 w-4" /> Buka di tab baru
          </a>
        )}
      </div>

      {url && showFrame ? (
        <iframe title="MLflow Tracking UI" src={url} className="h-[72vh] w-full bg-white" />
      ) : (
        <div className="p-8">
          <Banner kind="info">
            {url
              ? <>Server MLflow menunjuk <span className="font-mono">{url}</span> (lokal). Saat aplikasi dibuka dari domain publik, alamat lokal tidak dapat ditampilkan dalam iframe.</>
              : <>URL web UI MLflow belum dikonfigurasi.</>}
          </Banner>
          <div className="mt-4 space-y-2 text-sm text-steel">
            <p className="font-semibold text-navy">Mengaktifkan tampilan MLflow:</p>
            <p>1. Jalankan/deploy server MLflow, lalu salin URL publiknya.</p>
            <p>2. Set <code className="rounded bg-navy-50 px-1.5 py-0.5 font-mono text-[12px] text-navy">VITE_MLFLOW_UI_URL</code> di Vercel (frontend) dan{' '}
              <code className="rounded bg-navy-50 px-1.5 py-0.5 font-mono text-[12px] text-navy">MLFLOW_UI_URL</code> di ds-service (backend).</p>
            <p>3. Lokal: jalankan <code className="rounded bg-navy-50 px-1.5 py-0.5 font-mono text-[12px] text-navy">docker compose up</code> lalu buka{' '}
              <a className="text-royal underline" href="http://localhost:5000" target="_blank" rel="noreferrer">http://localhost:5000</a>.</p>
          </div>
        </div>
      )}
    </div>
  )
}

/* ============================ Util & demo ============================ */

function cmdPreview(cfg) {
  return `mlflow run . -e ${cfg.entry_point} --env-manager local -P test_size=${cfg.test_size} -P random_state=${cfg.random_state} -P n_trials=${cfg.n_trials} -P model_version="${cfg.model_version}"`
}

function DEMO_RUN(cfg, nextVersion) {
  const v = (cfg.model_version || nextVersion || 'V1').replace(/^model_/i, '')
  return {
    status: 'success',
    run_id: 'run_' + Math.random().toString(16).slice(2, 12),
    mlflow_run_id: Math.random().toString(16).slice(2, 12),
    version: v,
    algorithm: 'GradientBoosting',
    logs:
      `$ ${cmdPreview(cfg)}\n` +
      `2025/01/01 10:00:00 INFO mlflow.projects: === Created directory /tmp/.../mlflow ===\n` +
      `2025/01/01 10:00:00 INFO mlflow.projects.backend.local: === Running command 'python train_pipeline.py' ===\n` +
      `================================================================\n RiskFinder · MLflow Project — Build Model\n================================================================\n` +
      `[MLflow Project] entry point=main  version=${v}\n` +
      `[1/7] dvc pull → memuat dataset defaultCreditCardClients.xls ...\n      dataset OK · 30,000 baris × 24 kolom\n` +
      `[mlflow] tracking aktif · experiment=credit-risk-build\n` +
      `[2/7] preprocessing (Step 1–11) ...\n      fitur final = 22 · train=20,976 test=8,990\n` +
      `[3/7] modeling: compare → tuning → validation → evaluasi (Step 12–16) ...\n      algoritma terbaik = GradientBoosting\n      ROC AUC train=0.8123 test=0.7841 gap=0.0282\n` +
      `[4/7] menyimpan artifact .pkl → Docker Volume + DVC (Step 17) ...\n      preprocessing_artifacts_${v}.pkl (12 KB) · best_credit_model_${v}.pkl (1.4 MB)\n` +
      `[5/7] menulis set train/test → DVC (CSV) ...\n[6/7] meregistrasi katalog → PostgreSQL ...\n` +
      `[7/7] selesai. Artifact siap dipasangkan di halaman Monitoring Model.\n` +
      `2025/01/01 10:03:20 INFO mlflow.projects: === Run succeeded ===`,
    metrics: { roc_auc_test: '0.7841', roc_auc_train: '0.8123', f1: '0.5402', recall: '0.6217', gap: '0.0282' },
    artifacts: {
      preprocessing: `preprocessing_artifacts_${v}.pkl`, model: `best_credit_model_${v}.pkl`,
      preprocessing_size: '12 KB', model_size: '1.4 MB',
    },
    datasets: [
      { name: 'X_train.csv', rows: 20976 }, { name: 'X_test.csv', rows: 8990 },
      { name: 'y_train.csv', rows: 20976 }, { name: 'y_test.csv', rows: 8990 },
    ],
    mlflow_ui_url: '',
  }
}

const DEMO_SPEC = {
  name: 'riskfinder-credit-risk',
  entry_points: ['main', 'preprocessing'],
  default_params: { test_size: 0.3, random_state: 42, n_trials: 80, model_version: '' },
  experiment: 'credit-risk-build',
  dataset_file: 'defaultCreditCardClients.xls',
  next_version: 'V1',
  mlflow_ui_url: '',
  files: [
    { path: 'mlproject/MLproject', label: 'MLproject', language: 'yaml', editable: false, content:
`name: riskfinder-credit-risk

python_env: python_env.yaml

entry_points:
  main:
    parameters:
      test_size:     { type: float,  default: 0.30 }
      random_state:  { type: float,  default: 42 }
      n_trials:      { type: float,  default: 80 }
      model_version: { type: string, default: "" }
    command: >
      python train_pipeline.py
      --test_size {test_size} --random_state {random_state}
      --n_trials {n_trials} --model_version "{model_version}"

  preprocessing:
    parameters:
      test_size:     { type: float,  default: 0.30 }
      random_state:  { type: float,  default: 42 }
    command: >
      python train_pipeline.py --only preprocessing
      --test_size {test_size} --random_state {random_state}
` },
    { path: 'mlproject/train_pipeline.py', label: 'train_pipeline.py', language: 'python', editable: true, content:
`# Entry point MLflow Project — Build Model RiskFinder (ringkas; lihat repo untuk versi penuh)
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # -> /app
from app.ml import pipeline
from app.config import settings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test_size", type=float, default=0.30)
    ap.add_argument("--random_state", type=float, default=42)
    ap.add_argument("--n_trials", type=float, default=80)
    ap.add_argument("--model_version", type=str, default="")
    args = ap.parse_args()
    cfg = {"test_size": args.test_size, "random_state": int(args.random_state),
           "n_trials": int(args.n_trials), "model_version": args.model_version}
    from app.database import SessionLocal
    db = SessionLocal()
    result = pipeline.run_build(cfg, db=db, log=print)   # Step 1-17 + simpan .pkl otomatis
    db.close()
    with open(os.path.join(settings.ARTIFACT_DIR, "last_run_result.json"), "w") as f:
        json.dump({**result, "status": "success"}, f)

if __name__ == "__main__":
    main()
` },
    { path: 'app/ml/preprocessing.py', label: 'preprocessing.py', language: 'python', editable: true, content:
`# Preprocessing — Step 1-11 (ringkas; lihat repo untuk versi penuh)
def run_preprocessing(dataset_raw, test_size=0.30, random_state=42):
    # Step 1  drop ID, rename target, PAY_0 -> PAY_1
    # Step 2  drop_duplicates()
    # Step 3  EDUCATION/MARRIAGE inkonsisten -> NaN
    # Step 4  train_test_split(stratify=y)
    # Step 5  imputasi modus per-kelas DEFAULT
    # Step 6  outlier IQR capping (batas dari TRAIN)
    # Step 7  feature extraction (utilisasi, tren, telat, ...)
    # Step 8  encoding: OHE MARRIAGE, label SEX
    # Step 9  binning AGE -> AGE_GROUP
    # Step 10 feature selection (korelasi > 0.85, ANOVA p > 0.05)
    # Step 11 StandardScaler (kolom kontinu)
    artifacts = {"scaler": ..., "final_columns": [...], "sex_mapping": {...}}
    return X_train, X_test, y_train, y_test, artifacts
` },
    { path: 'app/ml/training.py', label: 'training.py', language: 'python', editable: true, content:
`# Modeling — Step 12-17 (ringkas; lihat repo untuk versi penuh)
def train_and_evaluate(X_train, X_test, y_train, y_test, n_trials=80):
    # Step 12 compare: RandomForest, GradientBoosting, AdaBoost, XGBoost (CV ROC AUC)
    # Step 13 hyperparameter tuning (Optuna / BayesSearch)
    # Step 14 validation: holdout & stratified K-fold
    # Step 15 evaluasi: ROC AUC, confusion matrix, classification report, learning curve
    # Step 16 finalisasi & prediksi
    metrics = {"algorithm": "GradientBoosting", "roc_auc_test": 0.7841, "gap": 0.0282, ...}
    return best_model, metrics, evaluation
` },
  ],
}
