import { useState, useRef, useEffect } from 'react';
import { Sun, Moon, Sparkles, Monitor, ChevronDown, Check } from 'lucide-react';
import { useTheme, THEMES, THEME_CONFIG } from '../../hooks/useTheme.jsx';
import clsx from 'clsx';

// Icon mapping
const IconMap = {
  Sun,
  Moon,
  Sparkles,
  Monitor,
};

// Get icon component for theme
const getThemeIcon = (theme, className = 'w-5 h-5') => {
  const config = THEME_CONFIG[theme];
  const Icon = IconMap[config?.icon] || Sun;
  return <Icon className={className} />;
};

// Simple Toggle Button (cycles through themes)
export const ThemeToggleButton = ({ className = '' }) => {
  const { resolvedTheme, cycleTheme } = useTheme();
  
  return (
    <button
      onClick={cycleTheme}
      className={clsx(
        'relative p-2.5 rounded-xl transition-all duration-300',
        'bg-muted hover:bg-muted/80',
        'hover:shadow-lg hover:shadow-primary/20',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        'active:scale-95',
        className
      )}
      title={`Current theme: ${THEME_CONFIG[resolvedTheme]?.label}`}
      aria-label="Toggle theme"
    >
      <div className="relative w-5 h-5">
        {/* Sun - Light mode */}
        <Sun 
          className={clsx(
            'absolute inset-0 w-5 h-5 transition-all duration-300',
            resolvedTheme === THEMES.LIGHT 
              ? 'opacity-100 rotate-0 scale-100 text-amber-500' 
              : 'opacity-0 rotate-90 scale-0'
          )} 
        />
        {/* Moon - Dark mode */}
        <Moon 
          className={clsx(
            'absolute inset-0 w-5 h-5 transition-all duration-300',
            resolvedTheme === THEMES.DARK 
              ? 'opacity-100 rotate-0 scale-100 text-blue-400' 
              : 'opacity-0 -rotate-90 scale-0'
          )} 
        />
        {/* Sparkles - Universe mode */}
        <Sparkles 
          className={clsx(
            'absolute inset-0 w-5 h-5 transition-all duration-300',
            resolvedTheme === THEMES.UNIVERSE 
              ? 'opacity-100 rotate-0 scale-100 text-purple-400' 
              : 'opacity-0 rotate-90 scale-0'
          )} 
        />
      </div>
    </button>
  );
};

// Dropdown Theme Selector
export const ThemeDropdown = ({ className = '' }) => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  const handleSelect = (selectedTheme) => {
    setTheme(selectedTheme);
    setIsOpen(false);
  };

  return (
    <div className={clsx('relative', className)} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-300',
          'bg-muted hover:bg-muted/80 border border-border/50',
          'hover:shadow-lg hover:shadow-primary/10',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        )}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        {getThemeIcon(resolvedTheme, 'w-4 h-4')}
        <span className="text-sm font-medium">{THEME_CONFIG[theme]?.label}</span>
        <ChevronDown className={clsx(
          'w-4 h-4 transition-transform duration-200',
          isOpen && 'rotate-180'
        )} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown Menu */}
          <div className={clsx(
            'absolute right-0 mt-2 w-56 z-50',
            'bg-card border border-border/50 rounded-xl shadow-xl',
            'animate-fade-in',
            'overflow-hidden'
          )}>
            <div className="p-1">
              {Object.values(THEMES).map((themeOption) => {
                const config = THEME_CONFIG[themeOption];
                const isSelected = theme === themeOption;
                
                return (
                  <button
                    key={themeOption}
                    onClick={() => handleSelect(themeOption)}
                    className={clsx(
                      'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg',
                      'transition-all duration-200',
                      isSelected 
                        ? 'bg-primary/10 text-primary' 
                        : 'hover:bg-muted text-foreground',
                    )}
                    role="option"
                    aria-selected={isSelected}
                  >
                    <span className={clsx(
                      'flex items-center justify-center w-8 h-8 rounded-lg',
                      isSelected ? 'bg-primary/20' : 'bg-muted'
                    )}>
                      {getThemeIcon(themeOption, 'w-4 h-4')}
                    </span>
                    <div className="flex-1 text-left">
                      <div className="text-sm font-medium">{config.label}</div>
                      <div className="text-xs text-muted-foreground">{config.description}</div>
                    </div>
                    {isSelected && (
                      <Check className="w-4 h-4 text-primary" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Segmented Theme Control
export const ThemeSegmented = ({ className = '' }) => {
  const { theme, setTheme } = useTheme();
  
  const themes = [THEMES.LIGHT, THEMES.DARK, THEMES.UNIVERSE];
  
  return (
    <div className={clsx(
      'inline-flex p-1 bg-muted rounded-xl',
      className
    )}>
      {themes.map((themeOption) => {
        const isSelected = theme === themeOption;
        
        return (
          <button
            key={themeOption}
            onClick={() => setTheme(themeOption)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300',
              isSelected 
                ? 'bg-card shadow-md text-foreground' 
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {getThemeIcon(themeOption, 'w-4 h-4')}
            <span className="text-sm font-medium hidden sm:inline">
              {THEME_CONFIG[themeOption].label}
            </span>
          </button>
        );
      })}
    </div>
  );
};

// Default export
export default ThemeToggleButton;
