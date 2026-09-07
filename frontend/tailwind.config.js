/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        ks: {
          50: '#eef2fb',
          100: '#d5e0f2',
          200: '#aabde4',
          300: '#6e93cf',
          400: '#3a69ba',
          500: '#1e4d9a',
          600: '#173b7a',
          700: '#122e5e',
          800: '#0d2046',
          900: '#071530',
        },
      },
    },
  },
  plugins: [],
}
