/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Aetheric Intelligence - Deep Space Design System
        'background': '#101319',
        'background-deep': '#080B10',
        'surface': '#101319',
        'surface-dim': '#101319',
        'surface-bright': '#36393f',
        'surface-container-lowest': '#0b0e13',
        'surface-container-low': '#191c21',
        'surface-container': '#1d2025',
        'surface-container-high': '#272a30',
        'surface-container-highest': '#32353b',
        'surface-glass': 'rgba(255, 255, 255, 0.04)',
        'border-glass': 'rgba(255, 255, 255, 0.06)',
        'grid-line': 'rgba(255, 255, 255, 0.03)',
        
        // Primary Color (Gold)
        'primary': '#ffd87f',
        'on-primary': '#3f2e00',
        'primary-container': '#f0b90b',
        'on-primary-container': '#644b00',
        'primary-fixed': '#ffdf99',
        'primary-fixed-dim': '#f6be16',
        'on-primary-fixed': '#251a00',
        'on-primary-fixed-variant': '#5a4300',
        'inverse-primary': '#775a00',
        
        // Secondary Color (Teal)
        'secondary': '#46f1bc',
        'on-secondary': '#003828',
        'secondary-container': '#02d4a1',
        'on-secondary-container': '#00563f',
        'secondary-fixed': '#55fdc7',
        'secondary-fixed-dim': '#29e0ac',
        'on-secondary-fixed': '#002116',
        'on-secondary-fixed-variant': '#00513c',
        
        // Tertiary Color (Red)
        'tertiary': '#ffd2d3',
        'on-tertiary': '#680019',
        'tertiary-container': '#ffaaae',
        'on-tertiary-container': '#a1002c',
        'tertiary-fixed': '#ffdada',
        'tertiary-fixed-dim': '#ffb3b5',
        'on-tertiary-fixed': '#40000c',
        'on-tertiary-fixed-variant': '#920027',
        
        // Error
        'error': '#ffb4ab',
        'on-error': '#690005',
        'error-container': '#93000a',
        'on-error-container': '#ffdad6',
        
        // Text Colors
        'on-surface': '#e1e2ea',
        'on-surface-variant': '#d3c5ac',
        'inverse-surface': '#e1e2ea',
        'inverse-on-surface': '#2d3036',
        'on-background': '#e1e2ea',
        
        // Outline
        'outline': '#9b8f79',
        'outline-variant': '#4f4633',
        
        // Surface Tint
        'surface-tint': '#f6be16',
        'surface-variant': '#32353b',
        
        // Glow Colors
        'glow-teal': 'rgba(70, 241, 188, 0.15)',
        'glow-gold': 'rgba(240, 185, 11, 0.12)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      borderRadius: {
        'DEFAULT': '0.25rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
        'full': '9999px',
      },
      spacing: {
        'base': '4px',
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '48px',
      },
      backdropFilter: {
        'blur-md': 'blur(12px)',
      },
    },
  },
  plugins: [],
}

