import { useState, useEffect, useRef, useCallback } from 'react'

export interface AutocompleteSuggestion {
  id: string
  [key: string]: unknown
}

export const EMPTY_OPTION_ID = '__empty__'

export interface AutocompleteSearchProps<T extends AutocompleteSuggestion> {
  value: string
  onChange: (value: string) => void
  onSelect?: (item: T) => void
  fetchSuggestions: (q: string) => Promise<T[]>
  /** How to show each suggestion in the dropdown (e.g. name, title, or "title - department") */
  getSuggestionLabel: (item: T) => string
  placeholder?: string
  className?: string
  inputClassName?: string
  minLength?: number
  debounceMs?: number
  maxSuggestions?: number
  /** If true, clearing input or selecting a suggestion runs onSelect(undefined) or keeps selection in value */
  clearOnSelect?: boolean
  /** When no suggestions match, show this option (e.g. "No matching skills"). Selecting it clears the field and calls onEmptySelect. */
  emptyOptionLabel?: string
  /** Called when user selects the empty-option (no matching results). */
  onEmptySelect?: () => void
}

export default function AutocompleteSearch<T extends AutocompleteSuggestion>({
  value,
  onChange,
  onSelect,
  fetchSuggestions,
  getSuggestionLabel,
  placeholder = 'Search...',
  className = '',
  inputClassName = '',
  minLength = 1,
  debounceMs = 250,
  maxSuggestions = 10,
  clearOnSelect = false,
  emptyOptionLabel,
  onEmptySelect,
}: AutocompleteSearchProps<T>) {
  const [suggestions, setSuggestions] = useState<T[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(-1)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const load = useCallback(
    async (q: string) => {
      if (q.length < minLength) {
        setSuggestions([])
        setOpen(false)
        return
      }
      setLoading(true)
      try {
        const list = await fetchSuggestions(q)
        const slice = (list || []).slice(0, maxSuggestions)
        if (slice.length === 0 && emptyOptionLabel) {
          setSuggestions([{ id: EMPTY_OPTION_ID, label: emptyOptionLabel } as unknown as T])
        } else {
          setSuggestions(slice)
        }
        setHighlightIndex(-1)
        setOpen(true)
      } catch {
        setSuggestions(emptyOptionLabel ? [{ id: EMPTY_OPTION_ID, label: emptyOptionLabel } as unknown as T] : [])
        setOpen(!!emptyOptionLabel)
      } finally {
        setLoading(false)
      }
    },
    [fetchSuggestions, minLength, maxSuggestions]
  )

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!value.trim()) {
      setSuggestions([])
      setOpen(false)
      return
    }
    debounceRef.current = setTimeout(() => load(value), debounceMs)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [value, debounceMs, load])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open || suggestions.length === 0) {
      if (e.key === 'Escape') setOpen(false)
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightIndex((i) => (i < suggestions.length - 1 ? i + 1 : 0))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightIndex((i) => (i > 0 ? i - 1 : suggestions.length - 1))
    } else if (e.key === 'Enter' && highlightIndex >= 0 && suggestions[highlightIndex]) {
      e.preventDefault()
      const sel = suggestions[highlightIndex]
      if (sel.id === EMPTY_OPTION_ID) {
        onChange('')
        onEmptySelect?.()
        setOpen(false)
        return
      }
      onChange(clearOnSelect ? '' : getSuggestionLabel(sel))
      onSelect?.(sel)
      setOpen(false)
    } else if (e.key === 'Escape') {
      setOpen(false)
      setHighlightIndex(-1)
    }
  }

  const handleSelect = (item: T) => {
    if (item.id === EMPTY_OPTION_ID) {
      onChange('')
      onEmptySelect?.()
      setOpen(false)
      setSuggestions([])
      return
    }
    onChange(clearOnSelect ? '' : getSuggestionLabel(item))
    onSelect?.(item)
    setOpen(false)
    setSuggestions([])
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => value.trim().length >= minLength && suggestions.length > 0 && setOpen(true)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className={inputClassName || 'w-full px-4 py-2 pl-10 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent'}
        autoComplete="off"
        aria-autocomplete="list"
        aria-expanded={open && suggestions.length > 0}
      />
      {loading && (
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </span>
      )}
      {open && suggestions.length > 0 && (
        <ul
          className="absolute z-50 w-full mt-1 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto"
          role="listbox"
        >
          {suggestions.map((item, i) => (
            <li
              key={item.id}
              role="option"
              aria-selected={i === highlightIndex}
              onMouseDown={() => handleSelect(item)}
              className={`px-4 py-2 cursor-pointer text-sm ${
                item.id === EMPTY_OPTION_ID
                  ? 'text-gray-500 dark:text-gray-400 italic'
                  : 'text-gray-700 dark:text-gray-300'
              } ${
                i === highlightIndex ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200' : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {item.id === EMPTY_OPTION_ID ? (item as { label?: string }).label : getSuggestionLabel(item)}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
