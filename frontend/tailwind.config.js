/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Palet korporat perbankan — diturunkan dari logo RiskFinder
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
        teal: {
          DEFAULT: '#00C49A',
          400: '#14D6AC',
          500: '#00C49A',
          600: '#00A081',
        },
        sky: {
          DEFAULT: '#00A8E8',
          400: '#33BBEE',
          500: '#00A8E8',
          600: '#008CC2',
        },
        steel: '#5B6B7F',
        risk: {
          high: '#E11D48',
          'high-bg': '#FEF2F4',
          low: '#0E9F6E',
          'low-bg': '#F0FAF6',
        },
        canvas: '#F6F8FB',
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
