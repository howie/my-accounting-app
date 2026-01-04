'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { useDeleteAccount } from '@/lib/hooks/useAccounts'
import { formatAmount } from '@/lib/utils'
import type { Account, AccountType } from '@/types'

interface AccountListProps {
  accounts: Account[]
  ledgerId: string
}

const accountTypeColors: Record<AccountType, string> = {
  ASSET: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  LIABILITY: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  INCOME: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  EXPENSE: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
}

export function AccountList({ accounts, ledgerId }: AccountListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const deleteAccount = useDeleteAccount(ledgerId)

  const handleDelete = async (id: string) => {
    try {
      await deleteAccount.mutateAsync(id)
      setDeletingId(null)
    } catch (err) {
      console.error('Failed to delete account:', err)
    }
  }

  // Group accounts by type
  const groupedAccounts = accounts.reduce(
    (groups, account) => {
      const type = account.type
      if (!groups[type]) {
        groups[type] = []
      }
      groups[type].push(account)
      return groups
    },
    {} as Record<AccountType, Account[]>
  )

  const typeOrder: AccountType[] = ['ASSET', 'LIABILITY', 'INCOME', 'EXPENSE']

  return (
    <div className="space-y-6">
      {typeOrder.map((type) => {
        const typeAccounts = groupedAccounts[type]
        if (!typeAccounts || typeAccounts.length === 0) return null

        return (
          <div key={type} className="rounded-lg border">
            <div className="border-b bg-muted/50 px-4 py-2">
              <h3 className="font-semibold">{type}</h3>
            </div>
            <div className="divide-y">
              {typeAccounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center justify-between px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`rounded px-2 py-1 text-xs font-medium ${accountTypeColors[account.type]}`}
                    >
                      {account.type}
                    </span>
                    <span className="font-medium">{account.name}</span>
                    {account.is_system && (
                      <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                        System
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <span
                      className={`flex items-center gap-1 font-mono ${
                        parseFloat(account.balance) < 0 ? 'text-destructive' : ''
                      }`}
                    >
                      {parseFloat(account.balance) < 0 && (
                        <span title="Negative balance">⚠️</span>
                      )}
                      ${formatAmount(account.balance)}
                    </span>
                    {!account.is_system && (
                      <>
                        {deletingId === account.id ? (
                          <div className="flex gap-2">
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDelete(account.id)}
                              disabled={deleteAccount.isPending}
                            >
                              Confirm
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setDeletingId(null)}
                            >
                              Cancel
                            </Button>
                          </div>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeletingId(account.id)}
                          >
                            Delete
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
