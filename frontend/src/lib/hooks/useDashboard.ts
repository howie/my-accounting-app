'use client'

import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'
import type {
  DashboardResponse,
  DashboardSummary,
} from '@/types/dashboard'
import { useLedgerContext } from '@/lib/context/LedgerContext'

/**
 * Hook to fetch dashboard summary data for the current ledger.
 */
export function useDashboard() {
  const { currentLedger } = useLedgerContext()
  const ledgerId = currentLedger?.id

  return useQuery<DashboardSummary>({
    queryKey: ['dashboard', ledgerId],
    queryFn: async () => {
      if (!ledgerId) {
        throw new Error('No ledger selected')
      }
      const response = await apiGet<DashboardResponse>(
        `/ledgers/${ledgerId}/dashboard`
      )
      return transformDashboardResponse(response)
    },
    enabled: !!ledgerId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  })
}

/**
 * Transform API response to frontend model.
 * Re-exported from types for convenience.
 */
function transformDashboardResponse(response: DashboardResponse): DashboardSummary {
  return {
    totalAssets: response.total_assets,
    currentMonth: {
      income: response.current_month.income,
      expenses: response.current_month.expenses,
      netCashFlow: response.current_month.net_cash_flow,
    },
    trends: response.trends.map((t) => ({
      month: t.month,
      year: t.year,
      income: t.income,
      expenses: t.expenses,
    })),
  }
}
