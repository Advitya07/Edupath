/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: { extend: { colors: { ink: '#0e1a2f', panel: '#15253d', line: '#284163' }, boxShadow: { glow: '0 0 36px rgba(56,189,248,.13)' } } },
  plugins: []
}
