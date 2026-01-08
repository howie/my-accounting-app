'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { LedgerForm } from '@/components/forms/LedgerForm'
import { LedgerSwitcher } from '@/components/ui/LedgerSwitcher'
import { useLedgers } from '@/lib/hooks/useLedgers'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { formatAmount, formatDate } from '@/lib/utils'
import type { Ledger } from '@/types'

export default function LedgersPage() {
  const router = useRouter()
  const { data: ledgers, isLoading, error } = useLedgers()
  const { setCurrentLedger } = useLedgerContext()
  const [showForm, setShowForm] = useState(false)
  const t = useTranslations()

  const handleSelectLedger = (ledger: Ledger) => {
    setCurrentLedger(ledger)
    router.push('/')
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">{t('ledgers.loadingLedgers')}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-destructive">{t('ledgers.errorLoading')}: {error.message}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Navigation Header */}
      <header className="border-b">
        <div className="container mx-auto flex items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold">
            {t('common.appName')}
          </Link>
          <LedgerSwitcher />
        </div>
      </header>

      <div className="container mx-auto py-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold">{t('ledgers.title')}</h1>
          <Button onClick={() => setShowForm(true)}>{t('ledgers.newLedger')}</Button>
        </div>

      {showForm && (
        <div className="mb-8">
          <LedgerForm
            onSuccess={() => setShowForm(false)}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {ledgers && ledgers.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">{t('ledgers.noLedgers')}</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {ledgers?.map((ledger) => (
            <button
              key={ledger.id}
              onClick={() => handleSelectLedger(ledger)}
              className="block rounded-lg border p-6 text-left transition-colors hover:bg-accent"
            >
              <h2 className="mb-2 text-xl font-semibold">{ledger.name}</h2>
              <p className="text-sm text-muted-foreground">
                {t('ledgers.initialBalance')}: ${formatAmount(ledger.initial_balance)}
              </p>
              <p className="text-sm text-muted-foreground">
                {t('ledgers.created')}: {formatDate(ledger.created_at)}
              </p>
            </button>
          ))}
        </div>
      )}
      </div>
    </div>
  )
}
