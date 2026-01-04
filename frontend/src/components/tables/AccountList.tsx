'use client'

import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { useDeleteAccount } from '@/lib/hooks/useAccounts'
import { formatAmount } from '@/lib/utils'
import type { AccountTreeNode, AccountType } from '@/types'

interface AccountListProps {
  accounts: AccountTreeNode[]
  ledgerId: string
}

const accountTypeColors: Record<AccountType, string> = {
  ASSET: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  LIABILITY: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  INCOME: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  EXPENSE: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
}

interface AccountRowProps {
  account: AccountTreeNode
  ledgerId: string
  depth: number
  expandedIds: Set<string>
  toggleExpand: (id: string) => void
  deletingId: string | null
  setDeletingId: (id: string | null) => void
  onDelete: (id: string) => Promise<void>
  isDeleting: boolean
}

function AccountRow({
  account,
  ledgerId,
  depth,
  expandedIds,
  toggleExpand,
  deletingId,
  setDeletingId,
  onDelete,
  isDeleting,
}: AccountRowProps) {
  const hasChildren = account.children && account.children.length > 0
  const isExpanded = expandedIds.has(account.id)
  const indentPx = depth * 24

  return (
    <>
      <div className="flex items-center justify-between px-4 py-3 border-b last:border-b-0">
        <div className="flex items-center gap-3" style={{ paddingLeft: `${indentPx}px` }}>
          {/* Expand/collapse button */}
          {hasChildren ? (
            <button
              type="button"
              onClick={() => toggleExpand(account.id)}
              className="flex h-6 w-6 items-center justify-center rounded hover:bg-accent"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              <span className="text-sm">{isExpanded ? '▼' : '▶'}</span>
            </button>
          ) : (
            <span className="w-6" /> /* Spacer for alignment */
          )}

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
          {hasChildren && (
            <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {account.children.length} sub-accounts
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
            {hasChildren && (
              <span className="text-xs text-muted-foreground ml-1">(total)</span>
            )}
          </span>
          {!account.is_system && !hasChildren && (
            <>
              {deletingId === account.id ? (
                <div className="flex gap-2">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDelete(account.id)}
                    disabled={isDeleting}
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
          {hasChildren && (
            <span className="text-xs text-muted-foreground">
              (has children)
            </span>
          )}
        </div>
      </div>

      {/* Render children if expanded */}
      {hasChildren && isExpanded && account.children.map((child) => (
        <AccountRow
          key={child.id}
          account={child}
          ledgerId={ledgerId}
          depth={depth + 1}
          expandedIds={expandedIds}
          toggleExpand={toggleExpand}
          deletingId={deletingId}
          setDeletingId={setDeletingId}
          onDelete={onDelete}
          isDeleting={isDeleting}
        />
      ))}
    </>
  )
}

export function AccountList({ accounts, ledgerId }: AccountListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const deleteAccount = useDeleteAccount(ledgerId)

  const handleDelete = async (id: string) => {
    try {
      await deleteAccount.mutateAsync(id)
      setDeletingId(null)
    } catch (err) {
      console.error('Failed to delete account:', err)
    }
  }

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  // Group accounts by type (already tree structured from backend)
  const groupedAccounts = accounts.reduce(
    (groups, account) => {
      const type = account.type
      if (!groups[type]) {
        groups[type] = []
      }
      groups[type].push(account)
      return groups
    },
    {} as Record<AccountType, AccountTreeNode[]>
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
            <div>
              {typeAccounts.map((account) => (
                <AccountRow
                  key={account.id}
                  account={account}
                  ledgerId={ledgerId}
                  depth={0}
                  expandedIds={expandedIds}
                  toggleExpand={toggleExpand}
                  deletingId={deletingId}
                  setDeletingId={setDeletingId}
                  onDelete={handleDelete}
                  isDeleting={deleteAccount.isPending}
                />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
