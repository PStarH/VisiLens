/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#0D0F12",
        surface: "#13161A",
        sidebar: "#1C1F24",
        border: "#2A2F35",
        primary: "#E5E7EB",
        secondary: "#9CA3AF",
        accent: "#3B82F6",
        "row-hover": "#1F2937",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      fontSize: {
        'xs': ['12px', { lineHeight: '16px' }],
        'sm': ['13px', { lineHeight: '18px' }],
      },
    },
  },
  plugins: [],
}
