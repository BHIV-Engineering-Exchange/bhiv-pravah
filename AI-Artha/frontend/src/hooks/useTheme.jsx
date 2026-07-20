import { useState, useEffect, createContext, useContext, useCallback } from 'react';

const ThemeContext = createContext();

// Available themes
export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  UNIVERSE: 'universe',
  SYSTEM: 'system',
};

// Theme display names and icons
export const THEME_CONFIG = {
  [THEMES.LIGHT]: {
    label: 'Light',
    description: 'Clean and bright interface',
    icon: 'Sun',
  },
  [THEMES.DARK]: {
    label: 'Dark',
    description: 'Easy on the eyes',
    icon: 'Moon',
  },
  [THEMES.UNIVERSE]: {
    label: 'Universe',
    description: 'Cosmic neon experience',
    icon: 'Sparkles',
  },
  [THEMES.SYSTEM]: {
    label: 'System',
    description: 'Match system preference',
    icon: 'Monitor',
  },
};

// Get system theme preference
const getSystemTheme = () => {
  if (typeof window === 'undefined') return THEMES.LIGHT;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? THEMES.DARK : THEMES.LIGHT;
};

// Apply theme class to document
const applyTheme = (theme) => {
  const root = window.document.documentElement;
  
  // Remove all theme classes
  root.classList.remove('light', 'dark', 'universe');
  
  // Apply the appropriate class
  if (theme === THEMES.SYSTEM) {
    const systemTheme = getSystemTheme();
    root.classList.add(systemTheme);
  } else {
    root.classList.add(theme);
  }
};

export const ThemeProvider = ({ children, defaultTheme = THEMES.SYSTEM, storageKey = 'artha-theme' }) => {
  const [theme, setTheme] = useState(() => {
    // Check localStorage first
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(storageKey);
      if (saved && Object.values(THEMES).includes(saved)) {
        return saved;
      }
    }
    return defaultTheme;
  });

  // Resolved theme (actual theme being displayed)
  const [resolvedTheme, setResolvedTheme] = useState(() => {
    if (theme === THEMES.SYSTEM) {
      return getSystemTheme();
    }
    return theme;
  });

  // Apply theme whenever it changes
  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(storageKey, theme);
    
    // Update resolved theme
    if (theme === THEMES.SYSTEM) {
      setResolvedTheme(getSystemTheme());
    } else {
      setResolvedTheme(theme);
    }
  }, [theme, storageKey]);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e) => {
      if (theme === THEMES.SYSTEM) {
        const newTheme = e.matches ? THEMES.DARK : THEMES.LIGHT;
        setResolvedTheme(newTheme);
        applyTheme(THEMES.SYSTEM);
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  // Set theme function
  const setThemeValue = useCallback((newTheme) => {
    if (Object.values(THEMES).includes(newTheme)) {
      setTheme(newTheme);
    }
  }, []);

  // Cycle through themes (light -> dark -> universe -> light)
  const cycleTheme = useCallback(() => {
    const themeOrder = [THEMES.LIGHT, THEMES.DARK, THEMES.UNIVERSE];
    const currentIndex = themeOrder.indexOf(resolvedTheme);
    const nextIndex = (currentIndex + 1) % themeOrder.length;
    setTheme(themeOrder[nextIndex]);
  }, [resolvedTheme]);

  // Toggle between light and dark only
  const toggleTheme = useCallback(() => {
    setTheme(prev => {
      if (prev === THEMES.LIGHT || (prev === THEMES.SYSTEM && resolvedTheme === THEMES.LIGHT)) {
        return THEMES.DARK;
      }
      return THEMES.LIGHT;
    });
  }, [resolvedTheme]);

  // Convenience booleans
  const isDarkMode = resolvedTheme === THEMES.DARK;
  const isLightMode = resolvedTheme === THEMES.LIGHT;
  const isUniverseMode = resolvedTheme === THEMES.UNIVERSE;
  const isSystemMode = theme === THEMES.SYSTEM;

  return (
    <ThemeContext.Provider 
      value={{ 
        theme,
        resolvedTheme,
        setTheme: setThemeValue,
        cycleTheme,
        toggleTheme,
        isDarkMode,
        isLightMode,
        isUniverseMode,
        isSystemMode,
        themes: THEMES,
        themeConfig: THEME_CONFIG,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default useTheme;
