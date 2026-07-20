/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // CSS Variable-based colors for dynamic theming
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          50: 'hsl(var(--primary) / 0.05)',
          100: 'hsl(var(--primary) / 0.1)',
          200: 'hsl(var(--primary) / 0.2)',
          300: 'hsl(var(--primary) / 0.3)',
          400: 'hsl(var(--primary) / 0.4)',
          500: 'hsl(var(--primary))',
          600: 'hsl(var(--primary))',
          700: 'hsl(var(--primary))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
          50: 'hsl(var(--success) / 0.05)',
          100: 'hsl(var(--success) / 0.1)',
          500: 'hsl(var(--success))',
          600: 'hsl(var(--success))',
          700: 'hsl(var(--success))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
          50: 'hsl(var(--warning) / 0.05)',
          100: 'hsl(var(--warning) / 0.1)',
          500: 'hsl(var(--warning))',
          600: 'hsl(var(--warning))',
          700: 'hsl(var(--warning))',
        },
        info: {
          DEFAULT: 'hsl(var(--info))',
          foreground: 'hsl(var(--info-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        // Sidebar colors
        sidebar: {
          DEFAULT: 'hsl(var(--sidebar-background))',
          background: 'hsl(var(--sidebar-background))',
          foreground: 'hsl(var(--sidebar-foreground))',
          primary: 'hsl(var(--sidebar-primary))',
          'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
          accent: 'hsl(var(--sidebar-accent))',
          'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
          border: 'hsl(var(--sidebar-border))',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
        heading: ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'display-xl': ['4.5rem', { lineHeight: '1.1', fontWeight: '700' }],
        'display-lg': ['3.75rem', { lineHeight: '1.1', fontWeight: '700' }],
        'display-md': ['3rem', { lineHeight: '1.2', fontWeight: '600' }],
        'display-sm': ['2.25rem', { lineHeight: '1.25', fontWeight: '600' }],
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        xl: 'calc(var(--radius) + 4px)',
        '2xl': 'calc(var(--radius) + 8px)',
        '3xl': 'calc(var(--radius) + 16px)',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
      height: {
        '18': '4.5rem',
      },
      transitionDuration: {
        '400': '400ms',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'fade-in-up': 'fadeInUp 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out forwards',
        'bounce-slow': 'bounce 2s infinite',
        'pulse-slow': 'pulseSlow 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'rotate-slow': 'rotateSlow 40s linear infinite',
        'twinkle': 'twinkle 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        pulseSlow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px hsl(var(--primary) / 0.3)' },
          '100%': { boxShadow: '0 0 40px hsl(var(--primary) / 0.6)' },
        },
        rotateSlow: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        twinkle: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.5', transform: 'scale(0.8)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      transitionTimingFunction: {
        'neo': 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        'cyber': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      backdropBlur: {
        xs: '2px',
        '2xl': '40px',
        '3xl': '64px',
      },
      boxShadow: {
        // Light mode neomorphic
        'neo': '8px 8px 16px hsl(220 13% 85%), -8px -8px 16px hsl(0 0% 100%)',
        'neo-inset': 'inset 4px 4px 8px hsl(220 13% 85%), inset -4px -4px 8px hsl(0 0% 100%)',
        // Dark mode neomorphic
        'neo-dark': '10px 10px 20px hsl(0 0% 3%), -10px -10px 20px hsl(0 0% 15%)',
        'neo-dark-inset': 'inset 5px 5px 10px hsl(0 0% 3%), inset -5px -5px 10px hsl(0 0% 15%)',
        // Glow shadows
        'glow': '0 0 30px -5px hsl(var(--primary) / 0.3)',
        'glow-lg': '0 0 40px -5px hsl(var(--primary) / 0.5)',
        'glow-xl': '0 0 60px -10px hsl(var(--primary) / 0.6)',
        'glow-primary': '0 0 30px -5px hsl(var(--primary) / 0.4)',
        'glow-secondary': '0 0 30px -5px hsl(var(--secondary) / 0.4)',
        'glow-accent': '0 0 30px -5px hsl(var(--accent) / 0.4)',
        'glow-success': '0 0 20px hsl(var(--success) / 0.3)',
        'glow-destructive': '0 0 20px hsl(var(--destructive) / 0.3)',
        // Neon shadows for universe mode
        'neon': '0 0 40px -6px hsl(275 95% 65% / 0.6)',
        'neon-cyan': '0 0 40px -6px hsl(200 95% 62% / 0.6)',
        'neon-pink': '0 0 40px -6px hsl(288 86% 60% / 0.6)',
        // Glass shadows
        'glass': '0 8px 32px hsl(0 0% 0% / 0.1)',
        'glass-lg': '0 25px 50px -12px hsl(0 0% 0% / 0.25)',
        'inner-lg': 'inset 0 2px 4px 0 hsl(0 0% 0% / 0.1)',
      },
      backgroundImage: {
        // Gradients
        'gradient-primary': 'linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.8) 100%)',
        'gradient-secondary': 'linear-gradient(135deg, hsl(var(--secondary)) 0%, hsl(var(--secondary) / 0.8) 100%)',
        'gradient-accent': 'linear-gradient(135deg, hsl(var(--accent)) 0%, hsl(var(--accent) / 0.8) 100%)',
        'gradient-card': 'linear-gradient(135deg, hsl(var(--card)) 0%, hsl(var(--card) / 0.5) 100%)',
        // Universe mode special gradients
        'gradient-cosmic': 'linear-gradient(135deg, hsl(275 95% 60%) 0%, hsl(288 86% 60%) 50%, hsl(200 95% 62%) 100%)',
        'gradient-aurora': 'linear-gradient(135deg, hsl(200 95% 62%) 0%, hsl(275 95% 60%) 50%, hsl(288 86% 60%) 100%)',
        // Shimmer
        'shimmer': 'linear-gradient(90deg, transparent 0%, hsl(var(--primary) / 0.1) 50%, transparent 100%)',
      },
    },
  },
  plugins: [
    // Custom plugin for additional utilities
    function({ addUtilities, addComponents }) {
      addUtilities({
        '.text-balance': {
          'text-wrap': 'balance',
        },
        '.glass': {
          'backdrop-filter': 'blur(16px) saturate(180%)',
          'background-color': 'hsl(var(--card) / 0.8)',
          'border': '1px solid hsl(var(--border) / 0.3)',
        },
        '.glass-heavy': {
          'backdrop-filter': 'blur(24px) saturate(200%)',
          'background-color': 'hsl(var(--card) / 0.9)',
          'border': '1px solid hsl(var(--border) / 0.5)',
        },
      });
      addComponents({
        '.btn-neo': {
          '@apply rounded-xl h-11 px-6 font-bold transition-all duration-300 active:scale-95': {},
          'background': 'linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary) / 0.9) 100%)',
          'color': 'hsl(var(--primary-foreground))',
          '&:hover': {
            'transform': 'scale(1.05)',
            'box-shadow': '0 0 30px -5px hsl(var(--primary) / 0.4)',
          },
        },
        '.card-neo': {
          '@apply rounded-2xl p-6 transition-all duration-400': {},
          'background': 'hsl(var(--card))',
          'border': '1px solid hsl(var(--border) / 0.3)',
          '&:hover': {
            'transform': 'scale(1.02)',
          },
        },
        '.input-neo': {
          '@apply h-12 rounded-xl border-2 px-4 transition-all duration-300': {},
          'border-color': 'hsl(var(--border))',
          'background': 'hsl(var(--background))',
          '&:focus': {
            'outline': 'none',
            'ring': '2px',
            'ring-color': 'hsl(var(--primary))',
            'border-color': 'hsl(var(--primary))',
          },
        },
      });
    },
  ],
}