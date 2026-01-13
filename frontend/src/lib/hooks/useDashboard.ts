'use client'

import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'
import type { DashboardResponse, DashboardSummary } from '@/types/dashboard'
import { useLedgerContext } from '@/lib/context/LedgerContext'

/**
 * Hook to fetch dashboard summary data for the current ledger.
 */
import { format } from 'date-fns'

interface DateRange {
  startDate?: Date
  endDate?: Date
}

/**
 * Hook to fetch dashboard summary data for the current ledger.
 */
export function useDashboard(dateRange?: DateRange) {
  const { currentLedger } = useLedgerContext()
  const ledgerId = currentLedger?.id

  return useQuery<DashboardSummary>({
    queryKey: ['dashboard', ledgerId, dateRange?.startDate, dateRange?.endDate],
    queryFn: async () => {
      if (!ledgerId) {
        throw new Error('No ledger selected')
      }

      const searchParams = new URLSearchParams()
      if (dateRange?.startDate) {
        searchParams.append('start_date', format(dateRange.startDate, 'yyyy-MM-dd'))
      }
      if (dateRange?.endDate) {
        searchParams.append('end_date', format(dateRange.endDate, 'yyyy-MM-dd'))
      }

      const queryString = searchParams.toString()
      const url = `/ledgers/${ledgerId}/dashboard${queryString ? `?${queryString}` : ''}`

      const response = await apiGet<DashboardResponse>(url)
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
