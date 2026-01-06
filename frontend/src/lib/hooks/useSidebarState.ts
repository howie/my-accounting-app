'use client'

import { useState, useEffect, useCallback } from 'react'
import type { AccountType } from '@/types/dashboard'

const STORAGE_KEY = 'ledgerone-sidebar-state'

interface SidebarState {
  expandedCategories: AccountType[]
  isCollapsed: boolean
}

const defaultState: SidebarState = {
  expandedCategories: [],
  isCollapsed: false,
}

/**
 * Hook for persisting sidebar state in session storage.
 */
export function useSidebarState() {
  const [state, setState] = useState<SidebarState>(defaultState)
  const [isHydrated, setIsHydrated] = useState(false)

  // Load from session storage on mount
  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      if (stored) {
        setState(JSON.parse(stored))
      }
    } catch {
      // Ignore errors (SSR, storage unavailable)
    }
    setIsHydrated(true)
  }, [])

  // Save to session storage on change
  useEffect(() => {
    if (isHydrated) {
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
      } catch {
        // Ignore errors
      }
    }
  }, [state, isHydrated])

  const toggleCategory = useCallback((type: AccountType) => {
    setState((prev) => {
      const isExpanded = prev.expandedCategories.includes(type)
      return {
        ...prev,
        expandedCategories: isExpanded
          ? prev.expandedCategories.filter((t) => t !== type)
          : [...prev.expandedCategories, type],
      }
    })
  }, [])

  const isCategoryExpanded = useCallback(
    (type: AccountType) => {
      return state.expandedCategories.includes(type)
    },
    [state.expandedCategories]
  )

  const toggleCollapsed = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isCollapsed: !prev.isCollapsed,
    }))
  }, [])

  const setCollapsed = useCallback((collapsed: boolean) => {
    setState((prev) => ({
      ...prev,
      isCollapsed: collapsed,
    }))
  }, [])

  return {
    isCollapsed: state.isCollapsed,
    toggleCollapsed,
    setCollapsed,
    toggleCategory,
    isCategoryExpanded,
    isHydrated,
  }
}
