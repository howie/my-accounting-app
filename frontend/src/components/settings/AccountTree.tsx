import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import {
  Archive,
  ArchiveRestore,
  ChevronDown,
  ChevronRight,
  Pencil,
  Trash2,
  GripVertical,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { formatAmount } from '@/lib/utils'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { useReorderAccounts } from '@/lib/hooks/useAccounts'
import type { AccountTreeNode, AccountType } from '@/types'

interface AccountTreeProps {
  accounts: AccountTreeNode[]
  onEdit: (account: AccountTreeNode) => void
  onDelete: (account: AccountTreeNode) => void
  onArchive: (account: AccountTreeNode) => void
  onUnarchive: (account: AccountTreeNode) => void
  showArchived: boolean
  onToggleShowArchived: () => void
}

const accountTypeColors: Record<AccountType, string> = {
  ASSET: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  LIABILITY: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  INCOME: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  EXPENSE: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
}

interface SortableAccountNodeProps {
  account: AccountTreeNode
  depth: number
  expandedIds: Set<string>
  toggleExpand: (id: string) => void
  onEdit: (account: AccountTreeNode) => void
  onDelete: (account: AccountTreeNode) => void
  onArchive: (account: AccountTreeNode) => void
  onUnarchive: (account: AccountTreeNode) => void
}

function SortableAccountNode({
  account,
  depth,
  expandedIds,
  toggleExpand,
  onEdit,
  onDelete,
  onArchive,
  onUnarchive,
}: SortableAccountNodeProps) {
  const { t } = useTranslation()
  const hasChildren = account.children && account.children.length > 0
  const isExpanded = expandedIds.has(account.id)
  const indentPx = depth * 24

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: account.id,
    disabled: account.is_system,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} className="group">
      <div
        className={cn(
          'flex items-center justify-between border-b px-3 py-2.5',
          'transition-colors hover:bg-muted/50',
          isDragging && 'bg-muted/70 shadow-md'
        )}
      >
        <div
          className="flex min-w-0 flex-1 items-center gap-2"
          style={{ paddingLeft: `${indentPx}px` }}
        >
          {/* Drag handle */}
          {!account.is_system ? (
            <button
              type="button"
              className="cursor-grab touch-none active:cursor-grabbing"
              {...attributes}
              {...listeners}
            >
              <GripVertical className="h-4 w-4 flex-shrink-0 text-muted-foreground/50 hover:text-muted-foreground" />
            </button>
          ) : (
            <span className="w-4 flex-shrink-0" />
          )}

          {/* Expand/collapse button */}
          {hasChildren ? (
            <button
              type="button"
              onClick={() => toggleExpand(account.id)}
              className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded hover:bg-accent"
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
          <span
            className={cn('truncate font-medium', account.is_archived && 'text-muted-foreground')}
          >
            {account.name}
          </span>

          {/* System badge */}
          {account.is_system && (
            <span className="flex-shrink-0 rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
              {t('common.system')}
            </span>
          )}

          {/* Archived badge */}
          {account.is_archived && (
            <span className="flex-shrink-0 rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
              {t('accountManagement.archivedSection')}
            </span>
          )}
        </div>

        <div className="flex flex-shrink-0 items-center gap-3">
          {/* Balance */}
          <span
            className={cn(
              'font-mono text-sm',
              parseFloat(account.balance) < 0 ? 'text-destructive' : 'text-muted-foreground'
            )}
          >
            ${formatAmount(account.balance)}
            {hasChildren && (
              <span className="ml-1 text-xs text-muted-foreground">{t('accounts.total')}</span>
            )}
          </span>

          {/* Actions */}
          {!account.is_system && (
            <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              {!account.is_archived && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onEdit(account)}
                  title={t('accountManagement.editAccount')}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
              )}
              {account.is_archived ? (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onUnarchive(account)}
                  title={t('accountManagement.unarchiveAccount')}
                >
                  <ArchiveRestore className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onArchive(account)}
                  title={t('accountManagement.archiveAccount')}
                >
                  <Archive className="h-4 w-4" />
                </Button>
              )}
              {!account.is_archived && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={() => onDelete(account)}
                  title={t('accountManagement.deleteAccount')}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Render children if expanded */}
      {hasChildren && isExpanded && (
        <SortableAccountList
          accounts={account.children}
          parentId={account.id}
          depth={depth + 1}
          expandedIds={expandedIds}
          toggleExpand={toggleExpand}
          onEdit={onEdit}
          onDelete={onDelete}
          onArchive={onArchive}
          onUnarchive={onUnarchive}
        />
      )}
    </div>
  )
}

interface SortableAccountListProps {
  accounts: AccountTreeNode[]
  parentId: string | null
  depth: number
  expandedIds: Set<string>
  toggleExpand: (id: string) => void
  onEdit: (account: AccountTreeNode) => void
  onDelete: (account: AccountTreeNode) => void
  onArchive: (account: AccountTreeNode) => void
  onUnarchive: (account: AccountTreeNode) => void
}

function SortableAccountList({
  accounts,
  parentId,
  depth,
  expandedIds,
  toggleExpand,
  onEdit,
  onDelete,
  onArchive,
  onUnarchive,
}: SortableAccountListProps) {
  const { currentLedger } = useLedgerContext()
  const reorderMutation = useReorderAccounts(currentLedger?.id || '')

  const [localAccounts, setLocalAccounts] = useState(accounts)

  // Sync local state when accounts prop changes
  useEffect(() => {
    setLocalAccounts(accounts)
  }, [accounts])

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = localAccounts.findIndex((a) => a.id === active.id)
      const newIndex = localAccounts.findIndex((a) => a.id === over.id)

      const newOrder = arrayMove(localAccounts, oldIndex, newIndex)
      setLocalAccounts(newOrder)

      // Send reorder request to backend
      reorderMutation.mutate({
        parent_id: parentId,
        account_ids: newOrder.map((a) => a.id),
      })
    }
  }

  const accountIds = localAccounts.map((a) => a.id)

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={accountIds} strategy={verticalListSortingStrategy}>
        <div>
          {localAccounts.map((account) => (
            <SortableAccountNode
              key={account.id}
              account={account}
              depth={depth}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
              onEdit={onEdit}
              onDelete={onDelete}
              onArchive={onArchive}
              onUnarchive={onUnarchive}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  )
}

export function AccountTree({
  accounts,
  onEdit,
  onDelete,
  onArchive,
  onUnarchive,
  showArchived,
  onToggleShowArchived,
}: AccountTreeProps) {
  const { t } = useTranslation()
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
      <div className="flex items-center justify-end">
        <label className="flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={onToggleShowArchived}
            className="rounded border-input"
          />
          {showArchived ? t('accountManagement.hideArchived') : t('accountManagement.showArchived')}
        </label>
      </div>
      {typeOrder.map((type) => {
        const typeAccounts = groupedAccounts[type]
        if (!typeAccounts || typeAccounts.length === 0) {
          return (
            <div key={type} className="rounded-lg border">
              <div
                className={cn(
                  'rounded-t-lg px-4 py-2',
                  accountTypeColors[type].replace('text-', 'border- border-l-4')
                )}
              >
                <h3 className="font-semibold">{t(`accountTypes.${type}`)}</h3>
              </div>
              <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                {t('accountManagement.noAccounts')}
              </div>
            </div>
          )
        }

        return (
          <div key={type} className="overflow-hidden rounded-lg border">
            <div
              className={cn(
                'border-b px-4 py-2',
                accountTypeColors[type].replace('text-', 'border- border-l-4')
              )}
            >
              <h3 className="font-semibold">{t(`accountTypes.${type}`)}</h3>
            </div>
            <SortableAccountList
              accounts={typeAccounts}
              parentId={null}
              depth={0}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
              onEdit={onEdit}
              onDelete={onDelete}
              onArchive={onArchive}
              onUnarchive={onUnarchive}
            />
          </div>
        )
      })}
    </div>
  )
}
