'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'
import { X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useUpdateAccount } from '@/lib/hooks/useAccounts'
import type { AccountTreeNode } from '@/types'

interface AccountEditDialogProps {
  account: AccountTreeNode | null
  ledgerId: string
  isOpen: boolean
  onClose: () => void
}

export function AccountEditDialog({ account, ledgerId, isOpen, onClose }: AccountEditDialogProps) {
  const t = useTranslations()
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const updateAccount = useUpdateAccount(ledgerId)

  // Reset form when account changes
  useEffect(() => {
    if (account) {
      setName(account.name)
      setError(null)
    }
  }, [account])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError(t('accountForm.nameRequired'))
      return
    }

    if (!account) return

    try {
      await updateAccount.mutateAsync({
        id: account.id,
        data: { name: name.trim() },
      })
      onClose()
    } catch (err) {
      setError(t('accountManagement.editAccount') + ' failed')
      console.error('Failed to update account:', err)
    }
  }

  if (!isOpen || !account) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden="true" />

      {/* Dialog */}
      <div className="relative z-10 mx-4 w-full max-w-md rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">{t('accountManagement.editAccount')}</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 p-6">
          <div className="space-y-2">
            <label htmlFor="account-name" className="text-sm font-medium">
              {t('accountForm.nameLabel')}
            </label>
            <Input
              id="account-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('accountForm.namePlaceholder')}
              autoFocus
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={updateAccount.isPending}
            >
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={updateAccount.isPending || !name.trim()}>
              {updateAccount.isPending ? t('common.loading') : t('common.save')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
