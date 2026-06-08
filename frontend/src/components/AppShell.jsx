import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { LogOut, ChevronDown, ShieldCheck, FlaskConical } from 'lucide-react'
import Logo from './Logo.jsx'
import { useAuth } from '../lib/auth.jsx'

export default function AppShell({ children, max = 'max-w-7xl' }) {
  const { session, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const home = session?.division === 'credit-analysis' ? '/app/entry' : '/app/menu'
  const DivIcon = session?.division === 'credit-analysis' ? ShieldCheck : FlaskConical
  const divLabel =
    session?.division === 'credit-analysis' ? 'Credit Analysis' : 'Data Scientist'

  return (
    <div className="min-h-screen bg-canvas">
      {/* Topbar */}
      <header className="sticky top-0 z-40 border-b border-navy-700/40 bg-navy/95 backdrop-blur">
        <div className={`mx-auto flex h-16 items-center justify-between px-4 sm:px-6 ${max}`}>
          <Link to={home} className="flex items-center gap-3">
            <Logo tone="light" className="h-9" />
          </Link>

          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-1.5 rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold text-white/90 sm:inline-flex">
              <DivIcon className="h-3.5 w-3.5 text-teal-400" />
              {divLabel}
            </span>

            <div className="relative">
              <button
                onClick={() => setOpen((v) => !v)}
                className="flex items-center gap-2 rounded-xl bg-white/10 px-2.5 py-1.5 text-sm font-medium text-white transition hover:bg-white/15"
              >
                <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-teal to-sky text-xs font-bold text-navy">
                  {session?.username?.slice(0, 2).toUpperCase()}
                </span>
                <span className="hidden max-w-[140px] truncate sm:inline">{session?.username}</span>
                <ChevronDown className="h-4 w-4 opacity-70" />
              </button>

              {open && (
                <>
                  <div className="fixed inset-0 z-0" onClick={() => setOpen(false)} />
                  <div className="absolute right-0 z-10 mt-2 w-56 animate-fade-up overflow-hidden rounded-xl border border-line bg-white shadow-card-hover">
                    <div className="border-b border-line px-4 py-3">
                      <p className="truncate text-sm font-semibold text-navy">{session?.username}</p>
                      <p className="text-xs text-steel">{divLabel} Sistem</p>
                    </div>
                    <button
                      onClick={() => {
                        logout()
                        navigate('/login')
                      }}
                      className="flex w-full items-center gap-2 px-4 py-3 text-sm font-medium text-risk-high transition hover:bg-risk-high-bg"
                    >
                      <LogOut className="h-4 w-4" />
                      Keluar
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className={`mx-auto px-4 py-8 sm:px-6 ${max}`}>{children}</main>

      <footer className="border-t border-line py-6">
        <div className={`mx-auto flex flex-col items-center justify-between gap-2 px-4 text-xs text-steel sm:flex-row sm:px-6 ${max}`}>
          <span>© {new Date().getFullYear()} RiskFinder Team</span>
        </div>
      </footer>
    </div>
  )
}
