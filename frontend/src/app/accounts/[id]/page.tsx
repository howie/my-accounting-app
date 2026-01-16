'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { AccountTransactionList } from '@/components/tables/AccountTransactionList'
import { TransactionModal } from '@/components/transactions/TransactionModal'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { useAccount } from '@/lib/hooks/useAccounts'
import { useRecentAccounts } from '@/lib/hooks/useRecentAccounts'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'

interface AccountPageProps {
  params: Promise<{ id: string }>
}

/**
 * Account transactions page.
 * Shows transactions for a specific account selected from sidebar.
 */
export default function AccountPage({ params }: AccountPageProps) {
  const { id } = use(params)
  const router = useRouter()
  const queryClient = useQueryClient()
  const { currentLedger, isLoading } = useLedgerContext()
  const { addRecent } = useRecentAccounts()

  // Fetch account data for pre-selection
  const { data: account } = useAccount(currentLedger?.id ?? '', id)

  // Update recent accounts when account data is loaded
  useEffect(() => {
    if (account) {
      addRecent({
        id: account.id,
        name: account.name,
        type: account.type,
      })
    }
  }, [account, addRecent])

  // Refresh transaction list after creating a new transaction
  const handleTransactionCreated = () => {
    queryClient.invalidateQueries({ queryKey: ['account-transactions', id] })
  }

  // Still loading ledger context
  if (isLoading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="mb-4 h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-64 animate-pulse rounded bg-muted/50" />
      </div>
    )
  }

  // No ledger selected
  if (!currentLedger) {
    return (
      <div className="p-6 lg:p-8">
        <div className="rounded-lg border p-8 text-center">
          <p className="text-muted-foreground">
            Please select a ledger to view account transactions.
          </p>
          <Button variant="outline" onClick={() => router.push('/ledgers')} className="mt-4">
            Select Ledger
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Back button */}
      <Button variant="ghost" size="sm" onClick={() => router.push('/')} className="-ml-2 mb-4">
        <ArrowLeft className="mr-1 h-4 w-4" />
        Back to Dashboard
      </Button>

      {/* Add Transaction button */}
      <div className="mb-4 flex justify-end">
        <TransactionModal
          ledgerId={currentLedger.id}
          preSelectedAccountId={account?.id}
          preSelectedAccountType={account?.type}
          onTransactionCreated={handleTransactionCreated}
        />
      </div>

      {/* Transaction list */}
      <AccountTransactionList accountId={id} />
    </div>
  )
}
