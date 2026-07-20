"use client"

import React from 'react'
import { useTheme } from './theme-provider'

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="theme-select" className="sr-only">Theme</label>
      <select
        id="theme-select"
        value={theme}
        onChange={(e) => setTheme(e.target.value)}
        className="rounded-md border px-2 py-1 text-sm bg-transparent"
      >
        <option value="light">Light</option>
        <option value="dark">Dark</option>
        <option value="universe">Universe</option>
        <option value="system">System</option>
      </select>
    </div>
  )
}
