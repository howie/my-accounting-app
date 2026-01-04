'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCreateAccount } from '@/lib/hooks/useAccounts'
import type { AccountType } from '@/types'

interface AccountFormProps {
  ledgerId: string
  onSuccess?: () => void
  onCancel?: () => void
}

const accountTypes: { value: AccountType; label: string; description: string }[] = [
  { value: 'ASSET', label: 'Asset', description: 'Things you own (cash, bank accounts, property)' },
  { value: 'LIABILITY', label: 'Liability', description: 'Things you owe (credit cards, loans)' },
  { value: 'INCOME', label: 'Income', description: 'Money you receive (salary, interest)' },
  { value: 'EXPENSE', label: 'Expense', description: 'Money you spend (food, rent, utilities)' },
]

export function AccountForm({ ledgerId, onSuccess, onCancel }: AccountFormProps) {
  const [name, setName] = useState('')
  const [type, setType] = useState<AccountType>('EXPENSE')
  const [error, setError] = useState<string | null>(null)

  const createAccount = useCreateAccount(ledgerId)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError('Name is required')
      return
    }

    try {
      await createAccount.mutateAsync({
        name: name.trim(),
        type,
      })
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create account')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-6">
      <h2 className="mb-4 text-xl font-semibold">Create New Account</h2>

      {error && (
        <div className="mb-4 rounded bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="mb-4">
        <label htmlFor="name" className="mb-2 block text-sm font-medium">
          Account Name
        </label>
        <Input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Groceries, Savings Account, Rent"
          required
        />
      </div>

      <div className="mb-6">
        <label className="mb-2 block text-sm font-medium">Account Type</label>
        <div className="grid gap-2 sm:grid-cols-2">
          {accountTypes.map((accountType) => (
            <button
              key={accountType.value}
              type="button"
              onClick={() => setType(accountType.value)}
              className={`rounded-lg border p-3 text-left transition-colors ${
                type === accountType.value
                  ? 'border-primary bg-primary/10'
                  : 'hover:bg-accent'
              }`}
            >
              <div className="font-medium">{accountType.label}</div>
              <div className="text-sm text-muted-foreground">{accountType.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={createAccount.isPending}>
          {createAccount.isPending ? 'Creating...' : 'Create Account'}
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
