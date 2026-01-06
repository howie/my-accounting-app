'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import type { Ledger } from '@/types'

const STORAGE_KEY = 'ledgerone_current_ledger'

interface LedgerContextType {
  currentLedger: Ledger | null
  setCurrentLedger: (ledger: Ledger | null) => void
  isLoading: boolean
}

const LedgerContext = createContext<LedgerContextType | undefined>(undefined)

export function LedgerProvider({ children }: { children: ReactNode }) {
  const [currentLedger, setCurrentLedgerState] = useState<Ledger | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setCurrentLedgerState(parsed)
      } catch (e) {
        console.error('Failed to parse stored ledger:', e)
        localStorage.removeItem(STORAGE_KEY)
      }
    }
    setIsLoading(false)
  }, [])

  // Save to localStorage when ledger changes
  const setCurrentLedger = (ledger: Ledger | null) => {
    setCurrentLedgerState(ledger)
    if (ledger) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(ledger))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  return (
    <LedgerContext.Provider value={{ currentLedger, setCurrentLedger, isLoading }}>
      {children}
    </LedgerContext.Provider>
  )
}

export function useLedgerContext() {
  const context = useContext(LedgerContext)
  if (context === undefined) {
    throw new Error('useLedgerContext must be used within a LedgerProvider')
  }
  return context
}
