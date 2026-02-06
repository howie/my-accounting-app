

import { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { AccountSelect } from '@/components/transactions/AccountSelect'
import { AmountInput } from '@/components/transactions/AmountInput'
import { useAccounts } from '@/lib/hooks/useAccounts'
import { useCreateInstallmentPlan } from '@/lib/hooks/useInstallments'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import type { AccountType } from '@/types'

interface InstallmentFormProps {
  onSuccess?: () => void
  onCancel?: () => void
}

// Installment plan creates transactions (usually EXPENSE logic)
// From: Source (Asset/Liab), To: Dest (Expense/Asset)
// Typically: Buying something large.
// From Credit Card (Liability) to Expense (Category) or Asset (Large Item).
// Or From Bank (Asset) to ...
const validFromTypes: AccountType[] = ['ASSET', 'LIABILITY']
const validToTypes: AccountType[] = ['EXPENSE', 'ASSET', 'LIABILITY']

export function InstallmentForm({ onSuccess, onCancel }: InstallmentFormProps) {
  const { t } = useTranslation() // We'll add installments section later
  const { currentLedger } = useLedgerContext()
  const ledgerId = currentLedger?.id || ''

  // Form state
  const [name, setName] = useState('')
  const [amountInput, setAmountInput] = useState('')
  const [totalAmount, setTotalAmount] = useState<number | null>(null)
  const [installmentCount, setInstallmentCount] = useState<string>('12')
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0])
  const [fromAccountId, setFromAccountId] = useState('')
  const [toAccountId, setToAccountId] = useState('')

  const [error, setError] = useState<string | null>(null)

  const { data: accountsData } = useAccounts(ledgerId)
  const createMutation = useCreateInstallmentPlan()

  const accounts = useMemo(() => accountsData || [], [accountsData])

  const handleAmountCalculated = (val: number) => {
    setTotalAmount(val)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError(t('validation.descriptionRequired'))
      return
    }

    if (totalAmount === null || totalAmount <= 0) {
      setError(t('validation.amountRequired'))
      return
    }

    const count = parseInt(installmentCount, 10)
    if (isNaN(count) || count <= 1) {
      setError('Installment count must be greater than 1') // TODO: i18n
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
      await createMutation.mutateAsync({
        name: name.trim(),
        total_amount: totalAmount,
        installment_count: count,
        start_date: startDate,
        source_account_id: fromAccountId,
        dest_account_id: toAccountId,
      })
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
          {t('recurring.table.name')} {/* Reusing Name label */}
        </label>
        <Input
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. New Laptop, Sofa"
          required
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Total Amount */}
        <div>
          <label htmlFor="amount" className="mb-2 block text-sm font-medium">
            Total Amount
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

        {/* Installment Count */}
        <div>
          <label htmlFor="count" className="mb-2 block text-sm font-medium">
            Installment Count (Months)
          </label>
          <Input
            id="count"
            type="number"
            min="2"
            value={installmentCount}
            onChange={(e) => setInstallmentCount(e.target.value)}
            required
          />
        </div>
      </div>

      {/* Start Date */}
      <div>
        <label htmlFor="startDate" className="mb-2 block text-sm font-medium">
          Start Date
        </label>
        <Input
          id="startDate"
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          required
        />
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
        <Button type="submit" disabled={createMutation.isPending}>
          {createMutation.isPending ? t('common.loading') : t('common.create')}
        </Button>
      </div>
    </form>
  )
}
