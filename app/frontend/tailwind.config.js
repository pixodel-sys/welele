/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    borderRadius: {
      'none': '0px',
      'sm': '4px',
      DEFAULT: '7px',
      'md': '7px',
      'lg': '7px',
      'xl': '7px',
      '2xl': '7px',
      '3xl': '7px',
      'full': '7px',
      'circle': '9999px',
    },
    extend: {
      colors: {
        welele: {
          black: "#0B0C0E",
          surface: "#141519",
          "surface-2": "#1C1E22",
          "surface-3": "#282A30",
          cream: "#FFF5EA",
          white: "#FFF5EA",
          muted: "#A8A5A1",
          orange: "#FF6B00",
          amber: "#FFA000",
          gold: "#FFC400",
          red: "#FF1744",
          pink: "#FF2A6D",
          magenta: "#E6007A",
          charcoal: "#1C1E22",
          success: "#00E676",
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Manrope', 'Outfit', 'system-ui', '-apple-system', 'sans-serif'],
        rounded: ['"Plus Jakarta Sans"', 'Outfit', 'sans-serif'],
        cinematic: ['"Plus Jakarta Sans"', 'Outfit', 'sans-serif'],
        condensed: ['"Barlow Condensed"', '"Plus Jakarta Sans"', 'sans-serif']
      },
      aspectRatio: {
        '9/16': '9 / 16',
        '8/16': '8 / 16'
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float-up': 'floatUp 2.5s ease-out forwards',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        floatUp: {
          '0%': { transform: 'translateY(0) scale(0.8)', opacity: '1' },
          '100%': { transform: 'translateY(-220px) scale(1.3)', opacity: '0' }
        },
        glow: {
          '0%': { boxShadow: '0 0 10px rgba(255, 107, 0, 0.4)' },
          '100%': { boxShadow: '0 0 25px rgba(230, 0, 122, 0.8)' }
        }
      }
    },
  },
  plugins: [],
}
