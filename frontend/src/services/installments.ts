import { apiPost } from '@/lib/api'

export interface InstallmentPlan {
  id: string
  name: string
  total_amount: number
  installment_count: number
  source_account_id: string
  dest_account_id: string
  start_date: string
  created_at: string
}

export interface InstallmentPlanCreate {
  name: string
  total_amount: number
  installment_count: number
  source_account_id: string
  dest_account_id: string
  start_date: string
}

export const installmentService = {
  create: async (data: InstallmentPlanCreate): Promise<InstallmentPlan> => {
    return apiPost<InstallmentPlan, InstallmentPlanCreate>('/installments', data)
  },
}
