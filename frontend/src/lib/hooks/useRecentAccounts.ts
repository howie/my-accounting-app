'use client'

import { useState, useEffect } from 'react'
import type { AccountType } from '@/types/dashboard'

const STORAGE_KEY = 'ledgerone-recent-accounts'
const MAX_RECENT = 5

export interface RecentAccount {
  id: string
  name: string
  type: AccountType
}

export function useRecentAccounts() {
  const [recents, setRecents] = useState<RecentAccount[]>([])
  const [isHydrated, setIsHydrated] = useState(false)

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        setRecents(JSON.parse(stored))
      }
    } catch {}
    setIsHydrated(true)
  }, [])

  const addRecent = (account: RecentAccount) => {
    setRecents(prev => {
      // Remove existing entry for this account if any
      const filtered = prev.filter(a => a.id !== account.id)
      // Add to top
      const newRecents = [account, ...filtered].slice(0, MAX_RECENT)

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newRecents))
      } catch {}

      return newRecents
    })
  }

  return { recents, addRecent, isHydrated }
}
