import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#f6f7fb',
        ink: '#111827',
        muted: '#6b7280',
        line: '#e5e7eb',
        accent: '#0f766e',
        accentSoft: '#ecfeff',
      },
      boxShadow: {
        panel: '0 16px 40px rgba(15, 23, 42, 0.08)',
      },
    },
  },
  plugins: [],
};

export default config;
