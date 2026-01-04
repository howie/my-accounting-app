'use client'

import { useState, useMemo } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAccounts, useCreateAccount } from '@/lib/hooks/useAccounts'
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
  const [parentId, setParentId] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const { data: accounts } = useAccounts(ledgerId)
  const createAccount = useCreateAccount(ledgerId)

  // Filter potential parent accounts: same type and depth < 3
  const parentOptions = useMemo(() => {
    if (!accounts) return []
    return accounts.filter((account) => {
      return account.type === type && account.depth < 3 && !account.is_system
    })
  }, [accounts, type])

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
        parent_id: parentId || null,
      })
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create account')
    }
  }

  // Reset parent when type changes
  const handleTypeChange = (newType: AccountType) => {
    setType(newType)
    setParentId('') // Clear parent selection when type changes
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

      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium">Account Type</label>
        <div className="grid gap-2 sm:grid-cols-2">
          {accountTypes.map((accountType) => (
            <button
              key={accountType.value}
              type="button"
              onClick={() => handleTypeChange(accountType.value)}
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

      {/* Parent Account Selector */}
      <div className="mb-6">
        <label htmlFor="parent" className="mb-2 block text-sm font-medium">
          Parent Account (Optional)
        </label>
        <select
          id="parent"
          value={parentId}
          onChange={(e) => setParentId(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="">None (Root Level)</option>
          {parentOptions.map((account) => (
            <option key={account.id} value={account.id}>
              {'─'.repeat(account.depth)} {account.name}
              {account.depth === 2 ? ' (max depth)' : ''}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-muted-foreground">
          Create as a sub-account under an existing account (max 3 levels deep)
        </p>
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
