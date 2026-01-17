import { apiGet, apiPost } from '@/lib/api'
import { Transaction } from '@/types' // Assuming type exists or I need to define it

// Define interfaces if not available centrally
export enum Frequency {
  DAILY = 'DAILY',
  WEEKLY = 'WEEKLY',
  MONTHLY = 'MONTHLY',
  YEARLY = 'YEARLY',
}

export interface RecurringTransaction {
  id: string
  name: string
  amount: number
  transaction_type: string
  frequency: Frequency
  start_date: string
  end_date?: string
  last_generated_date?: string
  source_account_id: string
  dest_account_id: string
}

export interface RecurringTransactionCreate {
  name: string
  amount: number
  transaction_type: string
  frequency: Frequency
  start_date: string
  end_date?: string
  source_account_id: string
  dest_account_id: string
}

export interface RecurringTransactionDue {
  id: string
  name: string
  amount: number
  due_date: string
}

export const recurringService = {
  create: async (data: RecurringTransactionCreate): Promise<RecurringTransaction> => {
    return apiPost<RecurringTransaction, RecurringTransactionCreate>('/recurring', data)
  },

  getDue: async (checkDate?: string): Promise<RecurringTransactionDue[]> => {
    const query = checkDate ? `?check_date=${checkDate}` : ''
    return apiGet<RecurringTransactionDue[]>(`/recurring/due${query}`)
  },

  approve: async (id: string, date: string): Promise<any> => { // Returns Transaction
    return apiPost<any, { date: string }>(`/recurring/${id}/approve`, { date })
  },
}
