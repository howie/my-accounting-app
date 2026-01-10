import { apiGet } from '../api'

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
}

export const accountsApi = {
    list: async (ledgerId: string) => {
        return apiGet<{ data: AccountListItem[] }>(`/ledgers/${ledgerId}/accounts`)
    },
}
