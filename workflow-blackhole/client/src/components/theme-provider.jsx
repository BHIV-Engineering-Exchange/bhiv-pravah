"use client"

import { createContext, useContext, useEffect, useState } from "react"

const ThemeContext = createContext({
  theme: "system",
  setTheme: () => null,
})

export function ThemeProvider({ children, defaultTheme = "light", storageKey = "vite-ui-theme", ...props }) {
  const [theme, setTheme] = useState(() => {
    const storedTheme = localStorage.getItem(storageKey)
    return storedTheme || defaultTheme
  })

  useEffect(() => {
    const root = window.document.documentElement

    // Compute which class to apply: 'light' | 'dark' | 'universe'
    let themeClass
    if (theme === 'system') {
      themeClass = window.matchMedia("(prefers-color-scheme: dark)").matches ? 'dark' : 'light'
    } else {
      themeClass = theme // 'light' | 'dark' | 'universe'
    }

    // Remove any of the theme classes then add the one we want
    root.classList.remove('light', 'dark', 'universe')
    root.classList.add(themeClass)

    // If using system, listen for changes and update between light/dark (not universe)
    if (theme === 'system') {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
      const handleChange = () => {
        root.classList.remove('light', 'dark', 'universe')
        root.classList.add(mediaQuery.matches ? 'dark' : 'light')
      }

      mediaQuery.addEventListener('change', handleChange)
      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme])

  const value = {
    theme,
    setTheme: (newTheme) => {
      localStorage.setItem(storageKey, newTheme)
      setTheme(newTheme)
    },
  }

  return (
    <ThemeContext.Provider {...props} value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider")
  }
  return context
}
