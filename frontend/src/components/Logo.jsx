/**
 * Logo RiskFinder — dikonversi dari LogoRiskFinder.tsx ke JSX.
 *
 * Penyesuaian untuk relevansi tampilan saat ini:
 *  - prop `tone="light"` membuat teks & perisai cerah agar kontras di atas header navy gelap
 *    (memenuhi prinsip Contrast), tanpa kehilangan identitas gradien teal→cyan.
 *  - prop `mark` me-render hanya lambang perisai (tanpa wordmark) untuk ruang sempit / mobile.
 */
export default function Logo({ className = 'h-10', tone = 'dark', mark = false }) {
  const light = tone === 'light'
  const textRisk = light ? '#FFFFFF' : '#0A2540'
  const textFinder = light ? '#9FC2E8' : '#1E5AA8'
  const tagline = light ? '#7E96B4' : '#5B6B7F'

  const uid = mark ? 'm' : 'f'

  return (
    <svg
      viewBox={mark ? '0 0 64 64' : '0 0 240 64'}
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="RiskFinder — Credit Risk Intelligence"
    >
      <defs>
        <linearGradient id={`rfGrad-${uid}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={light ? '#1E5AA8' : '#0A2540'} />
          <stop offset="100%" stopColor={light ? '#00A8E8' : '#1E5AA8'} />
        </linearGradient>
        <linearGradient id={`rfAccent-${uid}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#00C49A" />
          <stop offset="100%" stopColor="#00A8E8" />
        </linearGradient>
      </defs>

      <g transform="translate(8,8)">
        <path
          d="M24 0 L46 8 V26 C46 38 36 46 24 48 C12 46 2 38 2 26 V8 Z"
          fill={`url(#rfGrad-${uid})`}
        />
        <path
          d="M24 4 L42 10.5 V25.5 C42 35.5 33.5 42.5 24 44 C14.5 42.5 6 35.5 6 25.5 V10.5 Z"
          fill="none"
          stroke="rgba(255,255,255,0.18)"
          strokeWidth="1"
        />
        <circle cx="24" cy="24" r="5" fill="none" stroke={`url(#rfAccent-${uid})`} strokeWidth="1.6" />
        <circle cx="24" cy="24" r="10" fill="none" stroke={`url(#rfAccent-${uid})`} strokeWidth="1.2" opacity="0.7" />
        <circle cx="24" cy="24" r="15" fill="none" stroke={`url(#rfAccent-${uid})`} strokeWidth="0.8" opacity="0.4" />
        <circle cx="24" cy="24" r="2" fill="#00C49A" />
        <line x1="24" y1="24" x2="36" y2="14" stroke="#00C49A" strokeWidth="1.5" strokeLinecap="round" />
      </g>

      {!mark && (
        <g transform="translate(68,0)" fontFamily="Fraunces, Georgia, serif">
          <text x="0" y="32" fontSize="22" fontWeight="700" fill={textRisk} letterSpacing="0.3">
            Risk
          </text>
          <text x="50" y="32" fontSize="22" fontWeight="400" fill={textFinder} letterSpacing="0.3">
            Finder
          </text>
          <text
            x="1"
            y="48"
            fontSize="8"
            fontWeight="600"
            fill={tagline}
            letterSpacing="3"
            fontFamily="Manrope, Helvetica, Arial, sans-serif"
          >
            CREDIT&#160;RISK&#160;INTELLIGENCE
          </text>
        </g>
      )}
    </svg>
  )
}
