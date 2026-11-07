/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0B0F14',
        surface: {
          DEFAULT: '#101419',
          lowest: '#0A0E13',
          low: '#14181F',
          mid: '#181E26',
          high: '#1E2631',
          highest: '#26313F',
        },
        border: {
          DEFAULT: '#1F2937',
          subtle: '#19222D',
          focus: '#06B6D4',
        },
        primary: {
          DEFAULT: '#06B6D4',
          glow: '#4CD7F6',
          dim: 'rgba(6, 182, 212, 0.12)',
        },
        bull: {
          DEFAULT: '#10B981',
          dim: 'rgba(16, 185, 129, 0.12)',
          border: '#059669',
        },
        bear: {
          DEFAULT: '#EF4444',
          dim: 'rgba(239, 68, 68, 0.12)',
          border: '#DC2626',
        },
        amber: {
          DEFAULT: '#F59E0B',
          dim: 'rgba(245, 158, 11, 0.12)',
          border: '#D97706',
        },
        text: {
          prominent: '#F9FAFB',
          standard: '#9CA3AF',
          muted: '#6B7280',
          faint: '#4B5563',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      fontSize: {
        'micro': ['0.625rem', { lineHeight: '0.875rem', letterSpacing: '0.04em' }],
        'tiny': ['0.6875rem', { lineHeight: '0.9375rem' }],
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.8125rem', { lineHeight: '1.125rem' }],
        'base': ['0.875rem', { lineHeight: '1.25rem' }],
        'md': ['1rem', { lineHeight: '1.375rem' }],
        'lg': ['1.125rem', { lineHeight: '1.5rem' }],
        'xl': ['1.25rem', { lineHeight: '1.625rem' }],
        '2xl': ['1.5rem', { lineHeight: '1.875rem' }],
      },
      borderRadius: {
        none: '0px',
        xs: '2px',
        sm: '4px',
        DEFAULT: '4px',
      },
    },
  },
  plugins: [],
};
