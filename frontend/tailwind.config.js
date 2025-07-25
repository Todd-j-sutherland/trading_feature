/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'chart-bg': '#1a1a1a',
        'chart-grid': '#2a2a2a',
        'chart-text': '#d1d4dc',
        'buy-signal': '#00ff88',
        'sell-signal': '#ff0088',
        'hold-signal': '#ffa500'
      }
    },
  },
  plugins: [],
}
