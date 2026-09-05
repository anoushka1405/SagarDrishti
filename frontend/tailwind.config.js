/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ocean: {
          950: '#060a12',
          900: '#0a101d',
          850: '#0f172a',
          800: '#142036',
          700: '#1e2e4a',
          600: '#2a4166',
        },
        cyan: {
          400: '#38bdf8',
          500: '#0ea5e9',
          glow: '#00f2fe',
        },
        teal: {
          400: '#2dd4bf',
          500: '#14b8a6',
          glow: '#00e5ff',
        },
        hazard: {
          red: '#ff4d4d',
          amber: '#ffb703',
          green: '#10b981',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'teal-glow': '0 0 20px rgba(45, 212, 191, 0.25)',
        'cyan-glow': '0 0 25px rgba(56, 189, 248, 0.3)',
        'red-glow': '0 0 20px rgba(255, 77, 77, 0.35)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      animation: {
        'radar-sweep': 'radarSweep 4s linear infinite',
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        radarSweep: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        }
      }
    },
  },
  plugins: [],
}
