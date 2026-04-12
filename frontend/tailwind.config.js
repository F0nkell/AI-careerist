/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Montserrat', 'sans-serif'],
      },
      colors: {
        gold: {
          50: '#fff9eb',
          100: '#fdf0c8',
          200: '#fbe090',
          300: '#f7ca54',
          400: '#f3b022',
          500: '#ea910f',
          600: '#cc6e0a',
          700: '#a9500b',
        },
        bg: "var(--color-bg)",
        text: "var(--color-text)",
        hint: "var(--color-hint)",
        link: "var(--color-link)",
        button: "var(--color-button)",
        buttonText: "var(--color-button-text)",
        secondaryBg: "var(--color-secondary-bg)",
      }
    },
  },
  plugins: [],
}