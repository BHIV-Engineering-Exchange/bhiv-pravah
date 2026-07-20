import { Sun, Moon, Star } from "lucide-react"
import { Button } from "../components/ui/button"
import { useTheme } from "./theme-provider"

// Cycles themes: light -> dark -> universe -> light
export function SimpleModeToggle({ className = "" }) {
  const { theme, setTheme } = useTheme()

  const handleToggle = () => {
    if (theme === "light") setTheme("dark")
    else if (theme === "dark") setTheme("universe")
    else setTheme("light")
  }

  // Determine icon for current theme
  const Icon = theme === "dark" ? Moon : theme === "universe" ? Star : Sun

  const label = theme === 'universe' ? 'Universe theme' : theme === 'dark' ? 'Dark theme' : 'Light theme'

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={handleToggle}
      aria-label={`Toggle theme - ${label}`}
      className={className}
    >
      <Icon className="h-5 w-5 text-primary" />
    </Button>
  )
}
