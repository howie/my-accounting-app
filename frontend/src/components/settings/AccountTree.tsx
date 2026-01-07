'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { ChevronDown, ChevronRight, Pencil, Trash2, GripVertical } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { formatAmount } from '@/lib/utils'
import type { AccountTreeNode, AccountType } from '@/types'

interface AccountTreeProps {
  accounts: AccountTreeNode[]
  onEdit: (account: AccountTreeNode) => void
  onDelete: (account: AccountTreeNode) => void
}

const accountTypeColors: Record<AccountType, string> = {
  ASSET: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  LIABILITY: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  INCOME: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  EXPENSE: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
}

interface AccountNodeProps {
  account: AccountTreeNode
  depth: number
  expandedIds: Set<string>
  toggleExpand: (id: string) => void
  onEdit: (account: AccountTreeNode) => void
  onDelete: (account: AccountTreeNode) => void
}

function AccountNode({
  account,
  depth,
  expandedIds,
  toggleExpand,
  onEdit,
  onDelete,
}: AccountNodeProps) {
  const t = useTranslations()
  const hasChildren = account.children && account.children.length > 0
  const isExpanded = expandedIds.has(account.id)
  const indentPx = depth * 24

  return (
    <div className="group">
      <div
        className={cn(
          'flex items-center justify-between px-3 py-2.5 border-b',
          'hover:bg-muted/50 transition-colors'
        )}
      >
        <div
          className="flex items-center gap-2 flex-1 min-w-0"
          style={{ paddingLeft: `${indentPx}px` }}
        >
          {/* Drag handle (for future drag-and-drop) */}
          {!account.is_system && (
            <GripVertical className="h-4 w-4 text-muted-foreground/50 cursor-grab flex-shrink-0" />
          )}
          {account.is_system && <span className="w-4 flex-shrink-0" />}

          {/* Expand/collapse button */}
          {hasChildren ? (
            <button
              type="button"
              onClick={() => toggleExpand(account.id)}
              className="flex h-6 w-6 items-center justify-center rounded hover:bg-accent flex-shrink-0"
              aria-label={isExpanded ? t('accounts.collapse') : t('accounts.expand')}
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
          ) : (
            <span className="w-6 flex-shrink-0" />
          )}

          {/* Account name */}
          <span className="font-medium truncate">{account.name}</span>

          {/* System badge */}
          {account.is_system && (
            <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground flex-shrink-0">
              {t('common.system')}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          {/* Balance */}
          <span
            className={cn(
              'font-mono text-sm',
              parseFloat(account.balance) < 0 ? 'text-destructive' : 'text-muted-foreground'
            )}
          >
            ${formatAmount(account.balance)}
            {hasChildren && (
              <span className="text-xs text-muted-foreground ml-1">
                {t('accounts.total')}
              </span>
            )}
          </span>

          {/* Actions */}
          {!account.is_system && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onEdit(account)}
                title={t('accountManagement.editAccount')}
              >
                <Pencil className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive hover:text-destructive"
                onClick={() => onDelete(account)}
                title={t('accountManagement.deleteAccount')}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Render children if expanded */}
      {hasChildren && isExpanded && (
        <div>
          {account.children.map((child) => (
            <AccountNode
              key={child.id}
              account={child}
              depth={depth + 1}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function AccountTree({ accounts, onEdit, onDelete }: AccountTreeProps) {
  const t = useTranslations()
  const [expandedIds, setExpandedIds] = useState<Set<string>>(() => {
    // Expand all by default
    const ids = new Set<string>()
    const collectIds = (nodes: AccountTreeNode[]) => {
      for (const node of nodes) {
        if (node.children && node.children.length > 0) {
          ids.add(node.id)
          collectIds(node.children)
        }
      }
    }
    collectIds(accounts)
    return ids
  })

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
    {} as Record<AccountType, AccountTreeNode[]>
  )

  const typeOrder: AccountType[] = ['ASSET', 'LIABILITY', 'INCOME', 'EXPENSE']

  return (
    <div className="space-y-6">
      {typeOrder.map((type) => {
        const typeAccounts = groupedAccounts[type]
        if (!typeAccounts || typeAccounts.length === 0) {
          return (
            <div key={type} className="rounded-lg border">
              <div
                className={cn(
                  'px-4 py-2 rounded-t-lg',
                  accountTypeColors[type].replace('text-', 'border-l-4 border-')
                )}
              >
                <h3 className="font-semibold">{t(`accountTypes.${type}`)}</h3>
              </div>
              <div className="px-4 py-8 text-center text-muted-foreground text-sm">
                {t('accountManagement.noAccounts')}
              </div>
            </div>
          )
        }

        return (
          <div key={type} className="rounded-lg border overflow-hidden">
            <div
              className={cn(
                'px-4 py-2 border-b',
                accountTypeColors[type].replace('text-', 'border-l-4 border-')
              )}
            >
              <h3 className="font-semibold">{t(`accountTypes.${type}`)}</h3>
            </div>
            <div>
              {typeAccounts.map((account) => (
                <AccountNode
                  key={account.id}
                  account={account}
                  depth={0}
                  expandedIds={expandedIds}
                  toggleExpand={toggleExpand}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
