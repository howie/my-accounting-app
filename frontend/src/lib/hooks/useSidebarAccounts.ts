'use client'

import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api'
import type {
  AccountsByCategoryResponse,
  SidebarCategory,
} from '@/types/dashboard'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { CATEGORY_CONFIG, type AccountType } from '@/types/dashboard'

/**
 * Hook to fetch accounts grouped by category for sidebar navigation.
 */
export function useSidebarAccounts() {
  const { currentLedger } = useLedgerContext()
  const ledgerId = currentLedger?.id

  return useQuery<SidebarCategory[]>({
    queryKey: ['sidebar-accounts', ledgerId],
    queryFn: async () => {
      if (!ledgerId) {
        throw new Error('No ledger selected')
      }
      const response = await apiGet<AccountsByCategoryResponse>(
        `/ledgers/${ledgerId}/accounts/by-category`
      )
      return transformResponse(response)
    },
    enabled: !!ledgerId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  })
}

/**
 * Transform API response to frontend model.
 */
function transformResponse(response: AccountsByCategoryResponse): SidebarCategory[] {
  const categoryOrder: AccountType[] = ['ASSET', 'LIABILITY', 'INCOME', 'EXPENSE']

  return categoryOrder.map((type) => {
    const category = response.categories.find((c) => c.type === type)
    return {
      type,
      label: CATEGORY_CONFIG[type].label,
      accounts: (category?.accounts ?? []).map((a) => ({
        id: a.id,
        name: a.name,
        type,
        balance: a.balance,
      })),
      isExpanded: false,
    }
  })
}
