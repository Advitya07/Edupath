/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: { extend: { colors: { ink: '#07111f', panel: '#101d30', line: '#23354e' }, boxShadow: { glow: '0 0 36px rgba(56,189,248,.13)' } } },
  plugins: []
}
