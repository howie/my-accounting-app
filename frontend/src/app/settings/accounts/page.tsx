'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Plus } from 'lucide-react'

import { useLedgerContext } from '@/lib/context/LedgerContext'
import { useAccountTree } from '@/lib/hooks/useAccounts'
import { AccountTree } from '@/components/settings/AccountTree'
import { AccountEditDialog } from '@/components/settings/AccountEditDialog'
import { AccountDeleteDialog } from '@/components/settings/AccountDeleteDialog'
import { AccountForm } from '@/components/forms/AccountForm'
import { Button } from '@/components/ui/button'
import type { AccountTreeNode } from '@/types'

/**
 * Account Management page.
 * Displays hierarchical account tree with CRUD operations.
 */
export default function AccountManagementPage() {
  const t = useTranslations('accountManagement')
  const tAccounts = useTranslations('accounts')
  const { currentLedger } = useLedgerContext()
  const ledgerId = currentLedger?.id || ''

  const { data: accounts, isLoading, error } = useAccountTree(ledgerId)

  // Dialog states
  const [showAddForm, setShowAddForm] = useState(false)
  const [editAccount, setEditAccount] = useState<AccountTreeNode | null>(null)
  const [deleteAccount, setDeleteAccount] = useState<AccountTreeNode | null>(null)

  if (!currentLedger) {
    return (
      <div className="flex h-64 items-center justify-center">
        <p className="text-muted-foreground">Select a ledger to manage accounts</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t('title')}</h1>
        <Button onClick={() => setShowAddForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t('addAccount')}
        </Button>
      </div>

      {/* Instructions */}
      <div className="rounded-lg border bg-muted/30 px-4 py-3">
        <p className="text-sm text-muted-foreground">{t('dragToReorder')}</p>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <span className="ml-3 text-muted-foreground">{tAccounts('loadingAccounts')}</span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3">
          <p className="text-sm text-destructive">Failed to load accounts. Please try again.</p>
        </div>
      )}

      {/* Account tree */}
      {accounts && accounts.length > 0 && (
        <AccountTree accounts={accounts} onEdit={setEditAccount} onDelete={setDeleteAccount} />
      )}

      {/* Empty state */}
      {accounts && accounts.length === 0 && !isLoading && (
        <div className="rounded-lg border bg-card p-8 text-center">
          <p className="text-muted-foreground">{tAccounts('noAccounts')}</p>
        </div>
      )}

      {/* Add Account Form Modal */}
      {showAddForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowAddForm(false)}
            aria-hidden="true"
          />
          <div className="relative z-10 mx-4 w-full max-w-lg rounded-lg border bg-background p-6 shadow-lg">
            <AccountForm ledgerId={ledgerId} onSuccess={() => setShowAddForm(false)} />
          </div>
        </div>
      )}

      {/* Edit Account Dialog */}
      <AccountEditDialog
        account={editAccount}
        ledgerId={ledgerId}
        isOpen={!!editAccount}
        onClose={() => setEditAccount(null)}
      />

      {/* Delete Account Dialog */}
      <AccountDeleteDialog
        account={deleteAccount}
        ledgerId={ledgerId}
        isOpen={!!deleteAccount}
        onClose={() => setDeleteAccount(null)}
      />
    </div>
  )
}
