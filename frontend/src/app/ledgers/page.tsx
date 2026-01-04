'use client'

import Link from 'next/link'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { LedgerForm } from '@/components/forms/LedgerForm'
import { LedgerSwitcher } from '@/components/ui/LedgerSwitcher'
import { useLedgers } from '@/lib/hooks/useLedgers'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { formatAmount, formatDate } from '@/lib/utils'

export default function LedgersPage() {
  const { data: ledgers, isLoading, error } = useLedgers()
  const { setCurrentLedger } = useLedgerContext()
  const [showForm, setShowForm] = useState(false)

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading ledgers...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-destructive">Error loading ledgers: {error.message}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Navigation Header */}
      <header className="border-b">
        <div className="container mx-auto flex items-center justify-between px-4 py-4">
          <Link href="/" className="text-xl font-bold">
            LedgerOne
          </Link>
          <LedgerSwitcher />
        </div>
      </header>

      <div className="container mx-auto py-8">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold">Ledgers</h1>
          <Button onClick={() => setShowForm(true)}>New Ledger</Button>
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
          <p className="text-muted-foreground">No ledgers yet. Create your first ledger to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {ledgers?.map((ledger) => (
            <Link
              key={ledger.id}
              href={`/ledgers/${ledger.id}`}
              onClick={() => setCurrentLedger(ledger)}
              className="block rounded-lg border p-6 transition-colors hover:bg-accent"
            >
              <h2 className="mb-2 text-xl font-semibold">{ledger.name}</h2>
              <p className="text-sm text-muted-foreground">
                Initial Balance: ${formatAmount(ledger.initial_balance)}
              </p>
              <p className="text-sm text-muted-foreground">
                Created: {formatDate(ledger.created_at)}
              </p>
            </Link>
          ))}
        </div>
      )}
      </div>
    </div>
  )
}
