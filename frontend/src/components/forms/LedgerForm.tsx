import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCreateLedger, useLedgers } from '@/lib/hooks/useLedgers'

interface LedgerFormProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export function LedgerForm({ onSuccess, onCancel }: LedgerFormProps) {
  const [name, setName] = useState('')
  const [initialBalance, setInitialBalance] = useState('')
  const [templateLedgerId, setTemplateLedgerId] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const { t } = useTranslation()

  const createLedger = useCreateLedger()
  const { data: ledgers } = useLedgers()

  const hasTemplate = templateLedgerId !== ''

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError(t('ledgerForm.nameRequired'))
      return
    }

    if (!hasTemplate) {
      const balance = initialBalance ? parseFloat(initialBalance) : 0
      if (isNaN(balance) || balance < 0) {
        setError(t('ledgerForm.invalidBalance'))
        return
      }
    }

    try {
      const balance = hasTemplate ? undefined : initialBalance ? parseFloat(initialBalance) : 0
      await createLedger.mutateAsync({
        name: name.trim(),
        ...(hasTemplate ? { template_ledger_id: templateLedgerId } : { initial_balance: balance }),
      })
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('ledgerForm.failedToCreate'))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-6">
      <h2 className="mb-4 text-xl font-semibold">{t('ledgerForm.title')}</h2>

      {error && (
        <div className="mb-4 rounded bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      <div className="mb-4">
        <label htmlFor="name" className="mb-2 block text-sm font-medium">
          {t('ledgerForm.nameLabel')}
        </label>
        <Input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t('ledgerForm.namePlaceholder')}
          required
        />
      </div>

      {ledgers && ledgers.length > 0 && (
        <div className="mb-4">
          <label htmlFor="templateLedger" className="mb-2 block text-sm font-medium">
            {t('ledgerForm.templateLedgerLabel')}
          </label>
          <select
            id="templateLedger"
            value={templateLedgerId}
            onChange={(e) => setTemplateLedgerId(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">{t('ledgerForm.noTemplate')}</option>
            {ledgers.map((ledger) => (
              <option key={ledger.id} value={ledger.id}>
                {ledger.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {!hasTemplate && (
        <div className="mb-6">
          <label htmlFor="initialBalance" className="mb-2 block text-sm font-medium">
            {t('ledgerForm.initialBalanceLabel')}
          </label>
          <Input
            id="initialBalance"
            type="number"
            step="0.01"
            min="0"
            value={initialBalance}
            onChange={(e) => setInitialBalance(e.target.value)}
            placeholder="0.00"
          />
          <p className="mt-1 text-sm text-muted-foreground">{t('ledgerForm.initialBalanceNote')}</p>
        </div>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={createLedger.isPending}>
          {createLedger.isPending ? t('ledgerForm.creating') : t('ledgerForm.createLedger')}
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
