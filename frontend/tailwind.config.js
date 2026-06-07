/** @type {import('tailwindcss').Config} */

/**
 * Palet RiskFinder — BIRU · GOLD · PUTIH (banking corporate, minimalis, elegan).
 *
 * Catatan migrasi warna:
 *  - `gold` adalah aksen utama yang baru (emas perbankan, hangat namun tidak norak).
 *  - Token lama `teal` SENGAJA dialiaskan ke nilai `gold` agar seluruh kelas lama
 *    (mis. `text-teal-600`, `bg-teal/10`, `from-teal`) otomatis ikut tema emas tanpa
 *    harus mengubah puluhan className di seluruh halaman → menjaga prinsip Consistency.
 *  - Makna sukses/bahaya tetap memakai token `risk` (hijau/merah), bukan `teal`,
 *    sehingga tidak ada ambiguitas semantik.
 */
const gold = {
  DEFAULT: '#C9A227',
  50: '#FBF6E7',
  100: '#F6EBC4',
  200: '#ECD78D',
  300: '#E0C25A',
  400: '#D2A93C',
  500: '#C9A227',
  600: '#A07D17',
  700: '#7C5F11',
}

export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Biru korporat — diturunkan dari logo RiskFinder
        navy: {
          DEFAULT: '#0A2540',
          50: '#F2F5F9',
          100: '#E2E9F1',
          200: '#C2D0E2',
          300: '#94AAC7',
          400: '#5B7299',
          500: '#33486E',
          600: '#1E3354',
          700: '#152844',
          800: '#0A2540',
          900: '#061829',
        },
        royal: {
          DEFAULT: '#1E5AA8',
          400: '#3C7BC9',
          500: '#1E5AA8',
          600: '#194B8C',
        },
        sky: {
          DEFAULT: '#2E86C9',
          400: '#5AA4DC',
          500: '#2E86C9',
          600: '#1F6BA8',
        },
        // Aksen emas (baru)
        gold,
        // Alias kompatibilitas: kelas `*-teal-*` lama → emas
        teal: gold,
        steel: '#5B6B7F',
        risk: {
          high: '#E11D48',
          'high-bg': '#FEF2F4',
          low: '#0E9F6E',
          'low-bg': '#F0FAF6',
        },
        canvas: '#F7F9FC',
        line: '#E6ECF3',
      },
      fontFamily: {
        // Fraunces = display serif (selaras logo); Manrope = teks korporat bersih
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Manrope', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(10,37,64,0.04), 0 8px 24px -12px rgba(10,37,64,0.12)',
        'card-hover': '0 2px 4px rgba(10,37,64,0.06), 0 16px 40px -16px rgba(10,37,64,0.20)',
        ring: '0 0 0 4px rgba(30,90,168,0.10)',
        gold: '0 8px 24px -12px rgba(201,162,39,0.55)',
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.25rem',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.5s cubic-bezier(0.16,1,0.3,1) both',
        'fade-in': 'fade-in 0.4s ease both',
      },
    },
  },
  plugins: [],
}
