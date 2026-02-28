/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        display: ['"Orbitron"', '"Rajdhani"', 'sans-serif'],
        body: ['"IBM Plex Sans"', '"Roboto Mono"', 'sans-serif'],
      },
      colors: {
        'void': {
          950: '#0a0a0f',
          900: '#12121a',
          800: '#1a1a25',
          700: '#252532',
        },
        'cyber': {
          primary: '#00ff9f',
          secondary: '#00d4ff',
          accent: '#ff006e',
          warning: '#ffbe0b',
        },
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, #1a1a25 1px, transparent 1px), linear-gradient(to bottom, #1a1a25 1px, transparent 1px)",
        'scanline': 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 255, 159, 0.03) 2px, rgba(0, 255, 159, 0.03) 4px)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in': 'slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
