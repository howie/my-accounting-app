'use client'

import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { AccountForm } from '@/components/forms/AccountForm'
import { AccountList } from '@/components/tables/AccountList'
import { TransactionForm } from '@/components/forms/TransactionForm'
import { TransactionList } from '@/components/tables/TransactionList'
import { TransactionFiltersComponent } from '@/components/filters/TransactionFilters'
import { LedgerSwitcher } from '@/components/ui/LedgerSwitcher'
import { useLedger, useDeleteLedger } from '@/lib/hooks/useLedgers'
import { useAccounts, useAccountTree } from '@/lib/hooks/useAccounts'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { formatAmount, formatDate } from '@/lib/utils'
import type { TransactionFilters } from '@/lib/hooks/useTransactions'

export default function LedgerDetailPage() {
  const params = useParams()
  const router = useRouter()
  const ledgerId = params.id as string
  const t = useTranslations()

  const { data: ledger, isLoading: ledgerLoading, error: ledgerError } = useLedger(ledgerId)
  const { data: accounts, isLoading: accountsLoading } = useAccounts(ledgerId)
  const { data: accountTree, isLoading: accountTreeLoading } = useAccountTree(ledgerId)
  const deleteLedger = useDeleteLedger()
  const { setCurrentLedger } = useLedgerContext()

  const [showAccountForm, setShowAccountForm] = useState(false)
  const [showTransactionForm, setShowTransactionForm] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [transactionFilters, setTransactionFilters] = useState<TransactionFilters>({})
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  // Set current ledger in context when loaded and redirect to dashboard
  useEffect(() => {
    if (ledger) {
      setCurrentLedger(ledger)
      router.push('/')
    }
  }, [ledger, setCurrentLedger, router])

  const handleDelete = async () => {
    try {
      await deleteLedger.mutateAsync(ledgerId)
      setCurrentLedger(null)
      router.push('/ledgers')
    } catch (err) {
      console.error('Failed to delete ledger:', err)
    }
  }

  if (ledgerLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">{t('common.loading')}</p>
      </div>
    )
  }

  if (ledgerError || !ledger) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-destructive">
            {ledgerError ? `${t('common.error')}: ${ledgerError.message}` : t('ledgers.notFound')}
          </p>
          <Link href="/ledgers" className="mt-4 text-primary hover:underline">
            {t('ledgers.backToLedgers')}
          </Link>
        </div>
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
        <div className="mb-2">
          <Link href="/ledgers" className="text-sm text-muted-foreground hover:text-primary">
            &larr; {t('ledgers.backToLedgers')}
          </Link>
        </div>

      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{ledger.name}</h1>
          <p className="text-muted-foreground">
            {t('ledgers.initialBalance')}: ${formatAmount(ledger.initial_balance)}
          </p>
          <p className="text-sm text-muted-foreground">
            {t('ledgers.created')}: {formatDate(ledger.created_at)}
          </p>
        </div>
        <div className="flex gap-2">
          {deleteConfirm ? (
            <>
              <Button variant="destructive" onClick={handleDelete} disabled={deleteLedger.isPending}>
                {deleteLedger.isPending ? t('ledgers.deleting') : t('ledgers.confirmDelete')}
              </Button>
              <Button variant="outline" onClick={() => setDeleteConfirm(false)}>
                {t('common.cancel')}
              </Button>
            </>
          ) : (
            <Button variant="outline" onClick={() => setDeleteConfirm(true)}>
              {t('ledgers.deleteLedger')}
            </Button>
          )}
        </div>
      </div>

      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-semibold">{t('accounts.title')}</h2>
        <Button onClick={() => setShowAccountForm(true)}>{t('accounts.newAccount')}</Button>
      </div>

      {showAccountForm && (
        <div className="mb-6">
          <AccountForm
            ledgerId={ledgerId}
            onSuccess={() => setShowAccountForm(false)}
            onCancel={() => setShowAccountForm(false)}
          />
        </div>
      )}

      {accountTreeLoading ? (
        <p className="text-muted-foreground">{t('accounts.loadingAccounts')}</p>
      ) : accountTree && accountTree.length > 0 ? (
        <AccountList accounts={accountTree} ledgerId={ledgerId} />
      ) : (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            {t('accounts.noAccounts')}
          </p>
        </div>
      )}

      {/* Transactions Section */}
      <div className="mt-10 mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-semibold">{t('transactions.title')}</h2>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowFilters(!showFilters)}>
            {showFilters ? t('transactions.hideFilters') : t('transactions.showFilters')}
          </Button>
          <Button onClick={() => setShowTransactionForm(true)}>{t('transactions.newTransaction')}</Button>
        </div>
      </div>

      {showTransactionForm && (
        <div className="mb-6">
          <TransactionForm
            ledgerId={ledgerId}
            onSuccess={() => setShowTransactionForm(false)}
            onCancel={() => setShowTransactionForm(false)}
          />
        </div>
      )}

      {showFilters && accounts && (
        <TransactionFiltersComponent
          accounts={accounts}
          filters={transactionFilters}
          onFiltersChange={setTransactionFilters}
        />
      )}

      <TransactionList ledgerId={ledgerId} filters={transactionFilters} />
      </div>
    </div>
  )
}
