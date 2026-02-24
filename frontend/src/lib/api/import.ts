import { apiGet, apiPost, apiPostMultipart } from '../api'

export enum ImportType {
  MYAB_CSV = 'MYAB_CSV',
  CREDIT_CARD = 'CREDIT_CARD',
}

export interface BankConfig {
  code: string
  name: string
  encoding?: string
}

export interface ImportPreviewResponse {
  session_id: string
  total_count: number
  date_range: { start: string; end: string }
  transactions: any[]
  duplicates: any[]
  account_mappings: any[]
  validation_errors: any[]
  is_valid: boolean
}

export interface TransactionOverride {
  date?: string
  amount?: number
  description?: string
  from_account_id?: string
  to_account_id?: string
}

export interface ImportExecuteRequest {
  session_id: string
  account_mappings: any[]
  skip_duplicate_rows: number[]
  transaction_overrides?: Record<number, TransactionOverride>
}

export interface ImportResult {
  success: boolean
  imported_count: number
  skipped_count: number
  created_accounts: any[]
}

export const importApi = {
  createPreview: async (
    ledgerId: string,
    file: File,
    importType: ImportType,
    bankCode?: string,
    referenceLedgerId?: string
  ) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('import_type', importType)
    if (bankCode) {
      formData.append('bank_code', bankCode)
    }
    if (referenceLedgerId) {
      formData.append('reference_ledger_id', referenceLedgerId)
    }
    return apiPostMultipart<ImportPreviewResponse>(`/ledgers/${ledgerId}/import/preview`, formData)
  },

  execute: async (ledgerId: string, data: ImportExecuteRequest) => {
    return apiPost<ImportResult>(`/ledgers/${ledgerId}/import/execute`, data)
  },

  getHistory: async (ledgerId: string, limit = 20, offset = 0) => {
    return apiGet<any>(`/ledgers/${ledgerId}/import/history?limit=${limit}&offset=${offset}`)
  },

  getJobStatus: async (jobId: string) => {
    return apiGet<any>(`/import/jobs/${jobId}`)
  },

  getBanks: async () => {
    return apiGet<{ banks: BankConfig[] }>(`/import/banks`)
  },
}
