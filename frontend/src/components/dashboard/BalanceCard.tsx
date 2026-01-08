'use client'

import { Card } from '@tremor/react'
import { Wallet } from 'lucide-react'

interface BalanceCardProps {
  totalAssets: number
  isLoading?: boolean
}

/**
 * Large balance overview card displaying total assets.
 * Mirauve-style with prominent typography.
 */
export function BalanceCard({ totalAssets, isLoading }: BalanceCardProps) {
  const formattedAmount = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(totalAssets)

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse">
          <div className="mb-4 h-4 w-24 rounded bg-gray-200" />
          <div className="h-10 w-48 rounded bg-gray-200" />
        </div>
      </Card>
    )
  }

  return (
    <Card className="bg-gradient-to-br from-emerald-50 to-white p-6 dark:from-emerald-950 dark:to-gray-900">
      <div className="mb-2 flex items-center gap-2 text-gray-500 dark:text-gray-400">
        <Wallet className="h-5 w-5" />
        <span className="text-sm font-medium">Total Assets</span>
      </div>
      <p className="text-4xl font-bold text-gray-900 dark:text-white">{formattedAmount}</p>
      <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
        Combined balance across all asset accounts
      </p>
    </Card>
  )
}
