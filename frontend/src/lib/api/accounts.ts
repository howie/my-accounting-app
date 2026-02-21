import { apiGet, apiPost } from '../api'

export interface AccountListItem {
  id: string
  name: string
  type: string
  balance: number
  is_system: boolean
  parent_id: string | null
  depth: number
  sort_order: number
  has_children: boolean
  is_archived: boolean
}

export const accountsApi = {
  list: async (ledgerId: string) => {
    return apiGet<{ data: AccountListItem[] }>(`/ledgers/${ledgerId}/accounts`)
  },
}

export async function archiveAccount(ledgerId: string, accountId: string) {
  return apiPost(`/ledgers/${ledgerId}/accounts/${accountId}/archive`, {})
}

export async function unarchiveAccount(ledgerId: string, accountId: string) {
  return apiPost(`/ledgers/${ledgerId}/accounts/${accountId}/unarchive`, {})
}
