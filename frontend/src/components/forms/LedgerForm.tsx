'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCreateLedger } from '@/lib/hooks/useLedgers'

interface LedgerFormProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export function LedgerForm({ onSuccess, onCancel }: LedgerFormProps) {
  const [name, setName] = useState('')
  const [initialBalance, setInitialBalance] = useState('')
  const [error, setError] = useState<string | null>(null)

  const createLedger = useCreateLedger()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError('Name is required')
      return
    }

    const balance = initialBalance ? parseFloat(initialBalance) : 0
    if (isNaN(balance) || balance < 0) {
      setError('Initial balance must be a positive number')
      return
    }

    try {
      await createLedger.mutateAsync({
        name: name.trim(),
        initial_balance: balance,
      })
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create ledger')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-6">
      <h2 className="mb-4 text-xl font-semibold">Create New Ledger</h2>

      {error && (
        <div className="mb-4 rounded bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="mb-4">
        <label htmlFor="name" className="mb-2 block text-sm font-medium">
          Ledger Name
        </label>
        <Input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., 2024 Personal Finance"
          required
        />
      </div>

      <div className="mb-6">
        <label htmlFor="initialBalance" className="mb-2 block text-sm font-medium">
          Initial Balance (optional)
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
        <p className="mt-1 text-sm text-muted-foreground">
          This will be added to your Cash account
        </p>
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={createLedger.isPending}>
          {createLedger.isPending ? 'Creating...' : 'Create Ledger'}
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  )
}
