'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'

const STORAGE_KEY = 'ledgerone-expanded-accounts'

/**
 * Hook for managing which accounts are expanded in the sidebar hierarchy.
 *
 * This is separate from useSidebarState which manages category expansion.
 * This hook manages individual account expand/collapse state for the
 * 3-level account hierarchy within each category.
 *
 * State is persisted to sessionStorage so it survives page refreshes
 * but not browser sessions.
 *
 * T136 [US6a] - Implementation
 */
export function useExpandedAccounts() {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [isHydrated, setIsHydrated] = useState(false)

  // Load from sessionStorage on mount
  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed)) {
          setExpandedIds(new Set(parsed))
        }
      }
    } catch {
      // Ignore errors (SSR, storage unavailable, invalid JSON)
    }
    setIsHydrated(true)
  }, [])

  // Save to sessionStorage when state changes
  useEffect(() => {
    if (isHydrated) {
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...expandedIds]))
      } catch {
        // Ignore errors
      }
    }
  }, [expandedIds, isHydrated])

  /**
   * Check if a specific account is expanded.
   */
  const isExpanded = useCallback(
    (accountId: string): boolean => {
      return expandedIds.has(accountId)
    },
    [expandedIds]
  )

  /**
   * Toggle the expanded state of an account.
   */
  const toggleExpanded = useCallback((accountId: string): void => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(accountId)) {
        next.delete(accountId)
      } else {
        next.add(accountId)
      }
      return next
    })
  }, [])

  /**
   * Explicitly set the expanded state of an account.
   */
  const setExpanded = useCallback((accountId: string, expanded: boolean): void => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (expanded) {
        next.add(accountId)
      } else {
        next.delete(accountId)
      }
      return next
    })
  }, [])

  /**
   * Expand all accounts in the provided list.
   */
  const expandAll = useCallback((accountIds: string[]): void => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      accountIds.forEach((id) => next.add(id))
      return next
    })
  }, [])

  /**
   * Collapse all accounts (reset to default state).
   */
  const collapseAll = useCallback((): void => {
    setExpandedIds(new Set())
  }, [])

  // Memoize the set to avoid creating new references
  const expandedAccountIds = useMemo(() => expandedIds, [expandedIds])

  return {
    expandedAccountIds,
    isExpanded,
    toggleExpanded,
    setExpanded,
    expandAll,
    collapseAll,
    isHydrated,
  }
}
