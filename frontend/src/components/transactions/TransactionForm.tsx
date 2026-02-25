import { useState, useMemo, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { AccountSelect } from '@/components/transactions/AccountSelect'
import { AmountInput } from '@/components/transactions/AmountInput'
import { TagSelect } from '@/components/transactions/TagSelect'
import { SaveTemplateDialog } from '@/components/templates/SaveTemplateDialog'
import { useAccounts } from '@/lib/hooks/useAccounts'
import {
  useCreateTransaction,
  useUpdateTransaction,
  useTransactionSuggestions,
} from '@/lib/hooks/useTransactions'
import type {
  TransactionType,
  AccountType,
  TransactionCreate,
  TransactionUpdate,
  Transaction,
} from '@/types'

export interface TransactionFormProps {
  ledgerId: string
  /** Pre-selected account (from account page) */
  preSelectedAccountId?: string
  /** Pre-selected account type (to determine from/to placement) */
  preSelectedAccountType?: AccountType
  /** Existing transaction data for edit mode */
  editTransaction?: Transaction
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

/** Suggest transaction type based on account type */
function suggestTransactionType(accountType: AccountType): TransactionType {
  switch (accountType) {
    case 'ASSET':
    case 'LIABILITY':
      return 'EXPENSE' // Most common for payment accounts
    case 'INCOME':
      return 'INCOME'
    case 'EXPENSE':
      return 'EXPENSE'
    default:
      return 'EXPENSE'
  }
}

/** Determine if account should be "from" or "to" based on type and transaction type */
function getAccountPlacement(
  accountType: AccountType,
  transactionType: TransactionType
): 'from' | 'to' {
  if (transactionType === 'EXPENSE') {
    return accountType === 'EXPENSE' ? 'to' : 'from'
  }
  if (transactionType === 'INCOME') {
    return accountType === 'INCOME' ? 'from' : 'to'
  }
  // Transfer: ASSET/LIABILITY can be either, default to 'from'
  return 'from'
}

function getFromLabel(type: TransactionType, t: (key: string) => string): string {
  switch (type) {
    case 'EXPENSE':
      return t('transactionForm.paymentAccount')
    case 'INCOME':
      return t('transactionForm.incomeSource')
    case 'TRANSFER':
      return t('transactionForm.transferFrom')
  }
}

function getToLabel(type: TransactionType, t: (key: string) => string): string {
  switch (type) {
    case 'EXPENSE':
      return t('transactionForm.expenseCategory')
    case 'INCOME':
      return t('transactionForm.depositAccount')
    case 'TRANSFER':
      return t('transactionForm.transferTo')
  }
}

export function TransactionForm({
  ledgerId,
  preSelectedAccountId,
  preSelectedAccountType,
  editTransaction,
  onSuccess,
  onCancel,
}: TransactionFormProps) {
  const { t } = useTranslation()
  const isEditMode = !!editTransaction

  // Form state - initialize from editTransaction if in edit mode
  const [transactionType, setTransactionType] = useState<TransactionType>(() => {
    if (editTransaction) return editTransaction.transaction_type
    if (preSelectedAccountType) return suggestTransactionType(preSelectedAccountType)
    return 'EXPENSE'
  })
  const [date, setDate] = useState(() =>
    editTransaction ? editTransaction.date : new Date().toISOString().split('T')[0]
  )
  const [description, setDescription] = useState(() =>
    editTransaction ? editTransaction.description : ''
  )
  const [amountInput, setAmountInput] = useState(() =>
    editTransaction ? editTransaction.amount : ''
  )
  const [calculatedAmount, setCalculatedAmount] = useState<number | null>(() =>
    editTransaction ? parseFloat(editTransaction.amount) : null
  )
  const [amountExpression, setAmountExpression] = useState<string | null>(() =>
    editTransaction ? editTransaction.amount_expression : null
  )
  const [fromAccountId, setFromAccountId] = useState(() =>
    editTransaction ? editTransaction.from_account_id : ''
  )
  const [toAccountId, setToAccountId] = useState(() =>
    editTransaction ? editTransaction.to_account_id : ''
  )
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>(() =>
    editTransaction?.tags ? editTransaction.tags.map((tag) => tag.id) : []
  )
  const [notes, setNotes] = useState(() => (editTransaction ? editTransaction.notes || '' : ''))
  const [error, setError] = useState<string | null>(null)
  const [showZeroAmountConfirm, setShowZeroAmountConfirm] = useState(false)
  const [showSaveTemplateDialog, setShowSaveTemplateDialog] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)

  const { data: accountsData } = useAccounts(ledgerId)
  const createTransaction = useCreateTransaction(ledgerId)
  const updateTransaction = useUpdateTransaction(ledgerId)
  const { data: suggestions = [] } = useTransactionSuggestions(isEditMode ? '' : ledgerId)

  const accounts = useMemo(() => accountsData || [], [accountsData])

  const filteredSuggestions = useMemo(() => {
    if (isEditMode) return []
    if (!description.trim()) return suggestions.slice(0, 8)
    return suggestions
      .filter((s) => s.description.toLowerCase().includes(description.toLowerCase()))
      .slice(0, 8)
  }, [isEditMode, description, suggestions])

  const transactionTypes = transactionTypeKeys.map((value) => ({
    value,
    label: t(`transactionTypes.${value}`),
    description: t(`transactionTypes.${value.toLowerCase()}Desc`),
  }))

  const validFromTypes = getValidFromAccounts(transactionType)
  const validToTypes = getValidToAccounts(transactionType)

  // Handle pre-selection on mount (only for create mode)
  useEffect(() => {
    if (isEditMode) return
    if (preSelectedAccountId && preSelectedAccountType && accounts.length > 0) {
      const placement = getAccountPlacement(preSelectedAccountType, transactionType)
      if (placement === 'from' && validFromTypes.includes(preSelectedAccountType)) {
        setFromAccountId(preSelectedAccountId)
      } else if (placement === 'to' && validToTypes.includes(preSelectedAccountType)) {
        setToAccountId(preSelectedAccountId)
      }
    }
  }, [
    isEditMode,
    preSelectedAccountId,
    preSelectedAccountType,
    accounts,
    transactionType,
    validFromTypes,
    validToTypes,
  ])

  // Reset account selections when transaction type changes
  const handleTypeChange = (type: TransactionType) => {
    setTransactionType(type)

    // In edit mode, keep current account selections
    if (isEditMode) return

    // Preserve pre-selected account if still valid
    if (preSelectedAccountId && preSelectedAccountType) {
      const newFromTypes = getValidFromAccounts(type)
      const newToTypes = getValidToAccounts(type)
      const placement = getAccountPlacement(preSelectedAccountType, type)

      if (placement === 'from' && newFromTypes.includes(preSelectedAccountType)) {
        setFromAccountId(preSelectedAccountId)
        setToAccountId('')
      } else if (placement === 'to' && newToTypes.includes(preSelectedAccountType)) {
        setToAccountId(preSelectedAccountId)
        setFromAccountId('')
      } else {
        setFromAccountId('')
        setToAccountId('')
      }
    } else {
      setFromAccountId('')
      setToAccountId('')
    }
  }

  const handleAmountCalculated = useCallback((amount: number, expression: string | null) => {
    setCalculatedAmount(amount)
    setAmountExpression(expression)
    setError(null)
  }, [])

  // Perform the actual transaction submission
  const submitTransaction = async (amount: number) => {
    try {
      if (isEditMode && editTransaction) {
        const updateData: TransactionUpdate = {
          date,
          description: description.trim(),
          amount,
          from_account_id: fromAccountId,
          to_account_id: toAccountId,
          transaction_type: transactionType,
          notes: notes.trim() || null,
          amount_expression: amountExpression,
          tag_ids: selectedTagIds,
        }
        await updateTransaction.mutateAsync({
          transactionId: editTransaction.id,
          data: updateData,
        })
      } else {
        const transactionData: TransactionCreate = {
          date,
          description: description.trim(),
          amount,
          from_account_id: fromAccountId,
          to_account_id: toAccountId,
          transaction_type: transactionType,
          notes: notes.trim() || null,
          amount_expression: amountExpression,
          tag_ids: selectedTagIds,
        }
        await createTransaction.mutateAsync(transactionData)
      }
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('transactionForm.failedToCreate'))
    }
  }

  // Handle zero amount confirmation
  const handleZeroAmountConfirm = async () => {
    setShowZeroAmountConfirm(false)
    await submitTransaction(0)
  }

  const handleZeroAmountCancel = () => {
    setShowZeroAmountConfirm(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!description.trim()) {
      setError(t('validation.descriptionRequired'))
      return
    }

    if (description.length > 200) {
      setError(t('validation.descriptionTooLong'))
      return
    }

    if (calculatedAmount === null) {
      setError(t('validation.amountRequired'))
      return
    }

    if (calculatedAmount < 0) {
      setError(t('transactionForm.invalidAmount'))
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

    if (notes.length > 500) {
      setError(t('validation.notesTooLong'))
      return
    }

    // DI-004: Show confirmation for zero-amount transactions
    if (calculatedAmount === 0) {
      setShowZeroAmountConfirm(true)
      return
    }

    await submitTransaction(calculatedAmount)
  }

  const isPending = isEditMode ? updateTransaction.isPending : createTransaction.isPending

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div
          className="rounded bg-destructive/10 p-3 text-sm text-destructive"
          role="alert"
          data-testid="form-error"
        >
          {error}
        </div>
      )}

      {/* Transaction Type */}
      <div>
        <label className="mb-2 block text-sm font-medium">{t('transactionForm.typeLabel')}</label>
        <div className="grid gap-2 sm:grid-cols-3">
          {transactionTypes.map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => handleTypeChange(type.value)}
              data-testid={`type-${type.value.toLowerCase()}`}
              className={`rounded-lg border p-3 text-left transition-colors ${
                transactionType === type.value ? 'border-primary bg-primary/10' : 'hover:bg-accent'
              }`}
            >
              <div className="font-medium">{type.label}</div>
              <div className="text-xs text-muted-foreground">{type.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Date */}
      <div>
        <label htmlFor="date" className="mb-2 block text-sm font-medium">
          {t('transactionForm.dateLabel')}
        </label>
        <Input
          id="date"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
          data-testid="date-input"
        />
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="mb-2 block text-sm font-medium">
          {t('transactionForm.descriptionLabel')}
        </label>
        <div className="relative">
          <Input
            id="description"
            type="text"
            value={description}
            onChange={(e) => {
              setDescription(e.target.value)
              if (!isEditMode) setShowSuggestions(true)
            }}
            onFocus={() => {
              if (!isEditMode) setShowSuggestions(true)
            }}
            onBlur={() => {
              setTimeout(() => setShowSuggestions(false), 200)
            }}
            placeholder={t('transactionForm.descriptionPlaceholder')}
            maxLength={200}
            required
            autoComplete="off"
            data-testid="description-input"
          />
          {showSuggestions && filteredSuggestions.length > 0 && (
            <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-md">
              {filteredSuggestions.map((suggestion, index) => (
                <button
                  key={index}
                  type="button"
                  className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    setDescription(suggestion.description)
                    if (suggestion.type === transactionType) {
                      setFromAccountId(suggestion.fromAccountId)
                      setToAccountId(suggestion.toAccountId)
                    }
                    setShowSuggestions(false)
                  }}
                >
                  <span className="truncate">{suggestion.description}</span>
                  <span className="ml-2 text-xs text-muted-foreground">
                    {suggestion.count > 1 ? `\u00D7${suggestion.count}` : ''}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Amount */}
      <div>
        <label htmlFor="amount" className="mb-2 block text-sm font-medium">
          {t('transactionForm.amountLabel')}
        </label>
        <AmountInput
          id="amount"
          value={amountInput}
          onChange={setAmountInput}
          onAmountCalculated={handleAmountCalculated}
          placeholder="0.00"
          required
          data-testid="amount-input"
        />
      </div>

      {/* From Account */}
      <div>
        <label htmlFor="fromAccount" className="mb-2 block text-sm font-medium">
          {getFromLabel(transactionType, t)}
        </label>
        <AccountSelect
          id="fromAccount"
          accounts={accounts}
          value={fromAccountId}
          onChange={setFromAccountId}
          allowedTypes={validFromTypes}
          excludeAccountId={toAccountId}
          required
          data-testid="from-account-select"
        />
      </div>

      {/* To Account */}
      <div>
        <label htmlFor="toAccount" className="mb-2 block text-sm font-medium">
          {getToLabel(transactionType, t)}
        </label>
        <AccountSelect
          id="toAccount"
          accounts={accounts}
          value={toAccountId}
          onChange={setToAccountId}
          allowedTypes={validToTypes}
          excludeAccountId={fromAccountId}
          required
          data-testid="to-account-select"
        />
      </div>

      {/* Notes (optional) */}
      <div>
        <label htmlFor="notes" className="mb-2 block text-sm font-medium">
          {t('transactionEntry.notes')}
        </label>
        <textarea
          id="notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={t('transactionEntry.notesPlaceholder')}
          maxLength={500}
          rows={3}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          data-testid="notes-input"
        />
        <div className="mt-1 text-xs text-muted-foreground">{notes.length}/500</div>
      </div>

      {/* Tags */}
      <div>
        <label className="mb-2 block text-sm font-medium">{t('tags.title')}</label>
        <TagSelect selectedTagIds={selectedTagIds} onChange={setSelectedTagIds} />
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-2 pt-2">
        <Button type="submit" disabled={isPending} data-testid="submit-button">
          {isPending
            ? isEditMode
              ? t('transactions.updating')
              : t('transactionForm.saving')
            : isEditMode
              ? t('transactions.updateTransaction')
              : t('transactionForm.saveTransaction')}
        </Button>
        {!isEditMode && (
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowSaveTemplateDialog(true)}
            disabled={
              !description.trim() || calculatedAmount === null || !fromAccountId || !toAccountId
            }
            data-testid="save-as-template-button"
          >
            {t('transactionEntry.saveAsTemplate')}
          </Button>
        )}
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} data-testid="cancel-button">
            {t('common.cancel')}
          </Button>
        )}
      </div>

      {/* Save as Template Dialog */}
      {!isEditMode && (
        <SaveTemplateDialog
          ledgerId={ledgerId}
          open={showSaveTemplateDialog}
          onOpenChange={setShowSaveTemplateDialog}
          templateData={{
            transaction_type: transactionType,
            from_account_id: fromAccountId,
            to_account_id: toAccountId,
            amount: calculatedAmount || 0,
            description: description.trim(),
          }}
        />
      )}

      {/* Zero Amount Confirmation Dialog (DI-004) */}
      {showZeroAmountConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          role="dialog"
          aria-modal="true"
          aria-labelledby="zero-amount-dialog-title"
          data-testid="zero-amount-dialog"
        >
          <div className="absolute inset-0 bg-black/50" aria-hidden="true" />
          <div className="relative z-10 mx-4 w-full max-w-sm rounded-lg border bg-background p-6 shadow-lg">
            <h3 id="zero-amount-dialog-title" className="mb-2 text-lg font-semibold">
              {t('validation.zeroAmountWarning')}
            </h3>
            <p className="mb-4 text-sm text-muted-foreground">
              {t('validation.zeroAmountConfirm')}
            </p>
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleZeroAmountCancel}
                data-testid="zero-amount-cancel"
              >
                {t('common.cancel')}
              </Button>
              <Button
                type="button"
                onClick={handleZeroAmountConfirm}
                data-testid="zero-amount-confirm"
              >
                {t('common.confirm')}
              </Button>
            </div>
          </div>
        </div>
      )}
    </form>
  )
}
