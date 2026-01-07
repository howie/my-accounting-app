'use client'

import { use } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { AccountTransactionList } from '@/components/tables/AccountTransactionList'
import { useLedgerContext } from '@/lib/context/LedgerContext'

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
  const { currentLedger, isLoading } = useLedgerContext()

  // Still loading ledger context
  if (isLoading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="h-8 w-48 bg-muted animate-pulse rounded mb-4" />
        <div className="h-64 bg-muted/50 animate-pulse rounded" />
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
          <Button
            variant="outline"
            onClick={() => router.push('/ledgers')}
            className="mt-4"
          >
            Select Ledger
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push('/')}
        className="mb-4 -ml-2"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to Dashboard
      </Button>

      {/* Transaction list */}
      <AccountTransactionList accountId={id} />
    </div>
  )
}
