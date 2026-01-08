'use client'

import { useState, useEffect, useCallback } from 'react'
import type { UserPreferences } from '@/types'

const STORAGE_KEY = 'myab_user_preferences'

const DEFAULT_PREFERENCES: UserPreferences = {
  language: 'zh-TW',
  theme: 'system',
}

/**
 * Hook for managing user preferences stored in localStorage.
 * Provides SSR-safe access to user preferences with persistence.
 */
export function useUserPreferences() {
  const [preferences, setPreferencesState] = useState<UserPreferences>(DEFAULT_PREFERENCES)
  const [isLoaded, setIsLoaded] = useState(false)

  // Load preferences from localStorage on mount (client-side only)
  useEffect(() => {
    if (typeof window === 'undefined') return

    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<UserPreferences>
        setPreferencesState({
          ...DEFAULT_PREFERENCES,
          ...parsed,
        })
      } else {
        // Initialize with browser language if no stored preference
        const browserLang = navigator.language
        const language = browserLang.startsWith('zh') ? 'zh-TW' : 'en'
        setPreferencesState({
          ...DEFAULT_PREFERENCES,
          language,
        })
      }
    } catch {
      // If parsing fails, use defaults
      setPreferencesState(DEFAULT_PREFERENCES)
    }
    setIsLoaded(true)
  }, [])

  // Save preferences to localStorage
  const setPreferences = useCallback((newPrefs: Partial<UserPreferences>) => {
    setPreferencesState((prev) => {
      const updated = { ...prev, ...newPrefs }
      if (typeof window !== 'undefined') {
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
        } catch {
          // Silently fail if localStorage is not available
        }
      }
      return updated
    })
  }, [])

  // Convenience setters
  const setLanguage = useCallback(
    (language: UserPreferences['language']) => {
      setPreferences({ language })
    },
    [setPreferences]
  )

  const setTheme = useCallback(
    (theme: UserPreferences['theme']) => {
      setPreferences({ theme })
    },
    [setPreferences]
  )

  return {
    preferences,
    isLoaded,
    setPreferences,
    setLanguage,
    setTheme,
  }
}
