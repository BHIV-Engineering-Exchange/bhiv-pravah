"use client"

import { useState, useCallback } from "react"
import { toast as reactToastifyToast } from 'react-toastify'

// Direct toast function that can be imported and used anywhere
export const toast = ({ title, description, variant = "default", duration = 3000 }) => {
  const message = title + (description ? `: ${description}` : '')

  const options = {
    autoClose: duration,
    position: "top-right"
  }

  switch (variant) {
    case "destructive":
      return reactToastifyToast.error(message, options)
    case "success":
      return reactToastifyToast.success(message, options)
    case "warning":
      return reactToastifyToast.warning(message, options)
    case "info":
      return reactToastifyToast.info(message, options)
    default:
      return reactToastifyToast(message, options)
  }
}

// Hook version for components that need to manage toast state
export function useToast() {
  const [toasts, setToasts] = useState([])

  const toastFunction = useCallback(({ title, description, variant = "default", duration = 3000 }) => {
    return toast({ title, description, variant, duration })
  }, [])

  const dismiss = useCallback((id) => {
    reactToastifyToast.dismiss(id)
  }, [])

  return {
    toast: toastFunction,
    dismiss,
    toasts
  }
}
