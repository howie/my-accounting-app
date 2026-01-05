'use client'

import { useState, useMemo } from 'react'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAccounts } from '@/lib/hooks/useAccounts'
import { useCreateTransaction } from '@/lib/hooks/useTransactions'
import type { TransactionType, AccountType } from '@/types'

interface TransactionFormProps {
  ledgerId: string
  onSuccess?: () => void
  onCancel?: () => void
}

const transactionTypeKeys: TransactionType[] = ['EXPENSE', 'INCOME', 'TRANSFER']

function getValidFromAccounts(type: TransactionType): AccountType[] {
  switch (type) {
    case 'EXPENSE':
      return ['ASSET', 'LIABILITY']
    case 'INCOME':
      return ['INCOME']
    case 'TRANSFER':
      return ['ASSET', 'LIABILITY']
  }
}

function getValidToAccounts(type: TransactionType): AccountType[] {
  switch (type) {
    case 'EXPENSE':
      return ['EXPENSE']
    case 'INCOME':
      return ['ASSET', 'LIABILITY']
    case 'TRANSFER':
      return ['ASSET', 'LIABILITY']
  }
}

export function TransactionForm({ ledgerId, onSuccess, onCancel }: TransactionFormProps) {
  const [transactionType, setTransactionType] = useState<TransactionType>('EXPENSE')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [fromAccountId, setFromAccountId] = useState('')
  const [toAccountId, setToAccountId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const t = useTranslations()

  const { data: accountsData } = useAccounts(ledgerId)
  const createTransaction = useCreateTransaction(ledgerId)

  const accounts = accountsData || []

  const transactionTypes = transactionTypeKeys.map((value) => ({
    value,
    label: t(`transactionTypes.${value}`),
    description: t(`transactionTypes.${value.toLowerCase()}Desc`),
  }))

  const validFromTypes = getValidFromAccounts(transactionType)
  const validToTypes = getValidToAccounts(transactionType)

  const fromAccounts = useMemo(
    () => accounts.filter((a) => validFromTypes.includes(a.type)),
    [accounts, validFromTypes]
  )

  const toAccounts = useMemo(
    () => accounts.filter((a) => validToTypes.includes(a.type) && a.id !== fromAccountId),
    [accounts, validToTypes, fromAccountId]
  )

  // Reset account selections when transaction type changes
  const handleTypeChange = (type: TransactionType) => {
    setTransactionType(type)
    setFromAccountId('')
    setToAccountId('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!description.trim()) {
      setError(t('transactionForm.descriptionRequired'))
      return
    }

    const amountNum = parseFloat(amount)
    if (isNaN(amountNum) || amountNum <= 0) {
      setError(t('transactionForm.invalidAmount'))
      return
    }

    if (!fromAccountId || !toAccountId) {
      setError(t('transactionForm.accountsRequired'))
      return
    }

    try {
      await createTransaction.mutateAsync({
        date,
        description: description.trim(),
        amount: amountNum,
        from_account_id: fromAccountId,
        to_account_id: toAccountId,
        transaction_type: transactionType,
      })
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('transactionForm.failedToCreate'))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-6">
      <h2 className="mb-4 text-xl font-semibold">{t('transactionForm.title')}</h2>

      {error && (
        <div className="mb-4 rounded bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Transaction Type */}
      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium">{t('transactionForm.typeLabel')}</label>
        <div className="grid gap-2 sm:grid-cols-3">
          {transactionTypes.map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => handleTypeChange(type.value)}
              className={`rounded-lg border p-3 text-left transition-colors ${
                transactionType === type.value
                  ? 'border-primary bg-primary/10'
                  : 'hover:bg-accent'
              }`}
            >
              <div className="font-medium">{type.label}</div>
              <div className="text-xs text-muted-foreground">{type.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Date */}
      <div className="mb-4">
        <label htmlFor="date" className="mb-2 block text-sm font-medium">
          {t('transactionForm.dateLabel')}
        </label>
        <Input
          id="date"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
      </div>

      {/* Description */}
      <div className="mb-4">
        <label htmlFor="description" className="mb-2 block text-sm font-medium">
          {t('transactionForm.descriptionLabel')}
        </label>
        <Input
          id="description"
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder={t('transactionForm.descriptionPlaceholder')}
          required
        />
      </div>

      {/* Amount */}
      <div className="mb-4">
        <label htmlFor="amount" className="mb-2 block text-sm font-medium">
          {t('transactionForm.amountLabel')}
        </label>
        <Input
          id="amount"
          type="number"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.00"
          required
        />
      </div>

      {/* From Account */}
      <div className="mb-4">
        <label htmlFor="fromAccount" className="mb-2 block text-sm font-medium">
          {t('transactionForm.fromAccountLabel')}
        </label>
        <select
          id="fromAccount"
          value={fromAccountId}
          onChange={(e) => setFromAccountId(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          required
        >
          <option value="">{t('transactionForm.selectAccount')}</option>
          {fromAccounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({t(`accountTypes.${account.type}`)})
            </option>
          ))}
        </select>
      </div>

      {/* To Account */}
      <div className="mb-6">
        <label htmlFor="toAccount" className="mb-2 block text-sm font-medium">
          {t('transactionForm.toAccountLabel')}
        </label>
        <select
          id="toAccount"
          value={toAccountId}
          onChange={(e) => setToAccountId(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          required
        >
          <option value="">{t('transactionForm.selectAccount')}</option>
          {toAccounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({t(`accountTypes.${account.type}`)})
            </option>
          ))}
        </select>
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={createTransaction.isPending}>
          {createTransaction.isPending ? t('transactionForm.saving') : t('transactionForm.saveTransaction')}
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            {t('common.cancel')}
          </Button>
        )}
      </div>
    </form>
  )
}
