'use client'

import { useState, useMemo } from 'react'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAccounts, useCreateAccount } from '@/lib/hooks/useAccounts'
import type { AccountType } from '@/types'

interface AccountFormProps {
  ledgerId: string
  onSuccess?: () => void
  onCancel?: () => void
}

const accountTypeKeys: AccountType[] = ['ASSET', 'LIABILITY', 'INCOME', 'EXPENSE']

export function AccountForm({ ledgerId, onSuccess, onCancel }: AccountFormProps) {
  const [name, setName] = useState('')
  const [type, setType] = useState<AccountType>('EXPENSE')
  const [parentId, setParentId] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const t = useTranslations()

  const { data: accounts } = useAccounts(ledgerId)
  const createAccount = useCreateAccount(ledgerId)

  const accountTypes = accountTypeKeys.map((value) => ({
    value,
    label: t(`accountTypes.${value}`),
    description: t(`accountTypes.${value.toLowerCase()}Desc`),
  }))

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
      setError(t('accountForm.nameRequired'))
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
      setError(err instanceof Error ? err.message : t('accountForm.failedToCreate'))
    }
  }

  // Reset parent when type changes
  const handleTypeChange = (newType: AccountType) => {
    setType(newType)
    setParentId('') // Clear parent selection when type changes
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-6">
      <h2 className="mb-4 text-xl font-semibold">{t('accountForm.title')}</h2>

      {error && (
        <div className="mb-4 rounded bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="mb-4">
        <label htmlFor="name" className="mb-2 block text-sm font-medium">
          {t('accountForm.nameLabel')}
        </label>
        <Input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t('accountForm.namePlaceholder')}
          required
        />
      </div>

      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium">{t('accountForm.typeLabel')}</label>
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
          {t('accountForm.parentLabel')}
        </label>
        <select
          id="parent"
          value={parentId}
          onChange={(e) => setParentId(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="">{t('accountForm.parentNone')}</option>
          {parentOptions.map((account) => (
            <option key={account.id} value={account.id}>
              {'─'.repeat(account.depth)} {account.name}
              {account.depth === 2 ? ` ${t('accountForm.maxDepth')}` : ''}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-muted-foreground">
          {t('accountForm.parentNote')}
        </p>
      </div>

      <div className="flex gap-2">
        <Button type="submit" disabled={createAccount.isPending}>
          {createAccount.isPending ? t('accountForm.creating') : t('accountForm.createAccount')}
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
