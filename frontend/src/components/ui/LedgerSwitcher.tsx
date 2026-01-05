'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { useLedgers } from '@/lib/hooks/useLedgers'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import type { Ledger } from '@/types'

export function LedgerSwitcher() {
  const [isOpen, setIsOpen] = useState(false)
  const { currentLedger, setCurrentLedger } = useLedgerContext()
  const { data: ledgersData } = useLedgers()
  const ledgers = ledgersData || []
  const t = useTranslations()

  const handleSelect = (ledger: Ledger) => {
    setCurrentLedger(ledger)
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className="min-w-[200px] justify-between"
      >
        <span className="truncate">
          {currentLedger ? currentLedger.name : t('ledgerSwitcher.selectLedger')}
        </span>
        <svg
          className={`ml-2 h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </Button>

      {isOpen && (
        <div className="absolute left-0 top-full z-50 mt-1 w-full min-w-[200px] rounded-md border bg-background shadow-lg">
          <div className="max-h-60 overflow-y-auto py-1">
            {ledgers.length === 0 ? (
              <div className="px-3 py-2 text-sm text-muted-foreground">
                {t('ledgerSwitcher.noLedgers')}
              </div>
            ) : (
              ledgers.map((ledger) => (
                <button
                  key={ledger.id}
                  onClick={() => handleSelect(ledger)}
                  className={`w-full px-3 py-2 text-left text-sm hover:bg-muted ${
                    currentLedger?.id === ledger.id ? 'bg-muted font-medium' : ''
                  }`}
                >
                  {ledger.name}
                </button>
              ))
            )}
          </div>
          <div className="border-t px-3 py-2">
            <Link
              href="/ledgers"
              className="block text-sm text-primary hover:underline"
              onClick={() => setIsOpen(false)}
            >
              {t('ledgerSwitcher.manageLedgers')}
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
