

import { useState, useMemo, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { AccountSelect } from '@/components/transactions/AccountSelect'
import { AmountInput } from '@/components/transactions/AmountInput'
import { useAccounts } from '@/lib/hooks/useAccounts'
import { useCreateRecurringTransaction, useUpdateRecurringTransaction } from '@/lib/hooks/useRecurring'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { Frequency, type RecurringTransaction } from '@/services/recurring'
import type { TransactionType, AccountType } from '@/types'

interface RecurringFormProps {
  initialData?: RecurringTransaction
  onSuccess?: () => void
  onCancel?: () => void
}

const transactionTypeKeys: TransactionType[] = ['EXPENSE', 'INCOME', 'TRANSFER']
const frequencyKeys: Frequency[] = [Frequency.DAILY, Frequency.WEEKLY, Frequency.MONTHLY, Frequency.YEARLY]

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

export function RecurringForm({ initialData, onSuccess, onCancel }: RecurringFormProps) {
  const { t } = useTranslation()
  const { currentLedger } = useLedgerContext()
  const ledgerId = currentLedger?.id || ''

  // Form state
  const [name, setName] = useState(initialData?.name || '')
  const [transactionType, setTransactionType] = useState<TransactionType>(
    (initialData?.transaction_type as TransactionType) || 'EXPENSE'
  )
  const [frequency, setFrequency] = useState<Frequency>(initialData?.frequency || Frequency.MONTHLY)
  const [startDate, setStartDate] = useState(
    initialData?.start_date || new Date().toISOString().split('T')[0]
  )
  const [endDate, setEndDate] = useState(initialData?.end_date || '')
  const [amountInput, setAmountInput] = useState(initialData?.amount.toString() || '')
  const [amount, setAmount] = useState<number | null>(initialData?.amount || null)
  const [fromAccountId, setFromAccountId] = useState(initialData?.source_account_id || '')
  const [toAccountId, setToAccountId] = useState(initialData?.dest_account_id || '')

  const [error, setError] = useState<string | null>(null)

  const { data: accountsData } = useAccounts(ledgerId)
  const createMutation = useCreateRecurringTransaction()
  const updateMutation = useUpdateRecurringTransaction()

  const accounts = useMemo(() => accountsData || [], [accountsData])
  const isEditing = !!initialData
  const isPending = createMutation.isPending || updateMutation.isPending

  const transactionTypes = transactionTypeKeys.map((value) => ({
    value,
    label: t(`transactionTypes.${value}`),
  }))

  const validFromTypes = getValidFromAccounts(transactionType)
  const validToTypes = getValidToAccounts(transactionType)

  const handleAmountCalculated = (val: number) => {
    setAmount(val)
  }

  // Handle type change logic (clearing accounts if invalid)
  const handleTypeChange = (type: TransactionType) => {
    setTransactionType(type)
    // In a real app, we should check if current selection is still valid,
    // but for simplicity we'll just keep them and let the user change if needed,
    // or clear them. TransactionForm clears them.
    setFromAccountId('')
    setToAccountId('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError(t('validation.descriptionRequired')) // Reusing description required message
      return
    }

    if (amount === null || amount <= 0) {
      setError(t('validation.amountRequired'))
      return
    }

    if (!fromAccountId || !toAccountId) {
      setError(t('transactionForm.accountsRequired'))
      return
    }

    if (fromAccountId === toAccountId) {
      setError(t('validation.sameAccountError'))
      return
    }

    try {
      const data = {
        name: name.trim(),
        amount,
        transaction_type: transactionType,
        frequency,
        start_date: startDate,
        end_date: endDate || undefined,
        source_account_id: fromAccountId,
        dest_account_id: toAccountId,
      }

      if (isEditing && initialData) {
        await updateMutation.mutateAsync({ id: initialData.id, data })
      } else {
        await createMutation.mutateAsync(data)
      }
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('common.error'))
    }
  }

  if (!ledgerId) {
    return <div>{t('common.error')}: No ledger selected</div>
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      {/* Name */}
      <div>
        <label htmlFor="name" className="mb-2 block text-sm font-medium">
          {t('recurring.table.name')}
        </label>
        <Input
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t('transactionForm.descriptionPlaceholder')}
          required
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Transaction Type */}
        <div>
          <label className="mb-2 block text-sm font-medium">{t('transactionForm.typeLabel')}</label>
          <select
            value={transactionType}
            onChange={(e) => handleTypeChange(e.target.value as TransactionType)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {transactionTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Frequency */}
        <div>
          <label className="mb-2 block text-sm font-medium">{t('recurring.frequency')}</label>
          <select
            value={frequency}
            onChange={(e) => setFrequency(e.target.value as Frequency)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {frequencyKeys.map((freq) => (
              <option key={freq} value={freq}>
                {t(`recurring.frequencies.${freq}`)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Amount */}
      <div>
        <label htmlFor="amount" className="mb-2 block text-sm font-medium">
          {t('recurring.amount')}
        </label>
        <AmountInput
          id="amount"
          value={amountInput}
          onChange={setAmountInput}
          onAmountCalculated={handleAmountCalculated}
          placeholder="0.00"
          required
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Start Date */}
        <div>
          <label htmlFor="startDate" className="mb-2 block text-sm font-medium">
            {t('filters.fromDate')} {/* Reusing "From Date" */}
          </label>
          <Input
            id="startDate"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
          />
        </div>

        {/* End Date */}
        <div>
          <label htmlFor="endDate" className="mb-2 block text-sm font-medium">
            {t('filters.toDate')} (Optional)
          </label>
          <Input
            id="endDate"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* From Account */}
        <div>
          <label htmlFor="fromAccount" className="mb-2 block text-sm font-medium">
            {t('transactionForm.fromAccountLabel')}
          </label>
          <AccountSelect
            id="fromAccount"
            accounts={accounts}
            value={fromAccountId}
            onChange={setFromAccountId}
            allowedTypes={validFromTypes}
            excludeAccountId={toAccountId}
            required
          />
        </div>

        {/* To Account */}
        <div>
          <label htmlFor="toAccount" className="mb-2 block text-sm font-medium">
            {t('transactionForm.toAccountLabel')}
          </label>
          <AccountSelect
            id="toAccount"
            accounts={accounts}
            value={toAccountId}
            onChange={setToAccountId}
            allowedTypes={validToTypes}
            excludeAccountId={fromAccountId}
            required
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            {t('common.cancel')}
          </Button>
        )}
        <Button type="submit" disabled={isPending}>
          {isPending
            ? isEditing
              ? t('tags.form.updating') // Reusing updating text
              : t('tags.form.creating')
            : isEditing
              ? t('tags.form.update')
              : t('tags.form.create')}
        </Button>
      </div>
    </form>
  )
}
