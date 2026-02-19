import { apiDelete, apiGet, apiPost, apiPut } from '../api'

// Enums
export enum GmailConnectionStatus {
  CONNECTED = 'CONNECTED',
  EXPIRED = 'EXPIRED',
  DISCONNECTED = 'DISCONNECTED',
}

export enum ScanJobStatus {
  PENDING = 'PENDING',
  SCANNING = 'SCANNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

export enum ScanTriggerType {
  MANUAL = 'MANUAL',
  SCHEDULED = 'SCHEDULED',
}

export enum StatementParseStatus {
  PENDING = 'PENDING',
  PARSED = 'PARSED',
  PARSE_FAILED = 'PARSE_FAILED',
  LLM_PARSED = 'LLM_PARSED',
}

export enum StatementImportStatus {
  NOT_IMPORTED = 'NOT_IMPORTED',
  IMPORTED = 'IMPORTED',
  SKIPPED = 'SKIPPED',
}

export enum ScheduleFrequency {
  DAILY = 'DAILY',
  WEEKLY = 'WEEKLY',
}

// Response Types
export interface GmailConnectionResponse {
  id: string
  email_address: string
  status: GmailConnectionStatus
  last_scan_at: string | null
  scan_start_date: string
  created_at: string
}

export interface GmailBankInfo {
  code: string
  name: string
  email_query: string
  password_hint: string
}

export interface UserBankSettingResponse {
  bank_code: string
  bank_name: string
  is_enabled: boolean
  has_password: boolean
  credit_card_account_id: string | null
  credit_card_account_name: string | null
}

export interface ScanJobResponse {
  id: string
  trigger_type: ScanTriggerType
  status: ScanJobStatus
  banks_scanned: string[]
  statements_found: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
}

export interface DiscoveredStatementResponse {
  id: string
  bank_code: string
  bank_name: string
  billing_period_start: string | null
  billing_period_end: string | null
  email_subject: string
  email_date: string
  pdf_filename: string
  parse_status: StatementParseStatus
  parse_confidence: number | null
  transaction_count: number
  total_amount: number | null
  import_status: StatementImportStatus
}

export interface StatementTransaction {
  index: number
  date: string
  merchant_name: string
  amount: number
  currency: string
  suggested_category: string | null
  category_confidence: number
  is_foreign: boolean
  original_description: string
}

export interface DuplicateWarning {
  transaction_index: number
  existing_transaction_ids: string[]
  reason: string
}

export interface StatementPreviewResponse {
  statement_id: string
  bank_name: string
  billing_period: { start: string; end: string }
  transactions: StatementTransaction[]
  total_amount: number
  duplicate_warnings: DuplicateWarning[]
  parse_confidence: number
}

export interface ImportStatementResponse {
  success: boolean
  import_session_id: string
  imported_count: number
  skipped_count: number
  created_accounts: Array<{ id: string; name: string; type: string }>
}

export interface ScheduleSettingsResponse {
  frequency: ScheduleFrequency | null
  hour: number | null
  day_of_week: number | null
  next_scan_at: string | null
}

// Request Types
export interface UpdateBankSettingsRequest {
  bank_code: string
  is_enabled?: boolean
  pdf_password?: string | null
  credit_card_account_id?: string | null
}

export interface TriggerScanRequest {
  bank_codes?: string[]
}

export interface ImportStatementRequest {
  statement_id: string
  category_overrides?: Array<{
    transaction_index: number
    category_name: string
    account_id?: string | null
  }>
  skip_transaction_indices?: number[]
}

export interface UpdateScheduleRequest {
  frequency: ScheduleFrequency | null
  hour?: number
  day_of_week?: number
}

// API Client
export const gmailImportApi = {
  // OAuth2 Connection
  initiateConnect: async (ledgerId: string) => {
    return apiPost<{ auth_url: string }>(`/gmail/auth/connect?ledger_id=${ledgerId}`, {})
  },

  getConnection: async (ledgerId: string) => {
    return apiGet<GmailConnectionResponse>(`/gmail/connection?ledger_id=${ledgerId}`)
  },

  disconnect: async (ledgerId: string) => {
    return apiDelete<{ message: string }>(`/gmail/connection?ledger_id=${ledgerId}`)
  },

  // Bank Settings
  getBanks: async () => {
    return apiGet<{ banks: GmailBankInfo[] }>('/gmail/banks')
  },

  getBankSettings: async (ledgerId: string) => {
    return apiGet<{ settings: UserBankSettingResponse[] }>(
      `/gmail/banks/settings?ledger_id=${ledgerId}`
    )
  },

  updateBankSettings: async (ledgerId: string, data: UpdateBankSettingsRequest) => {
    return apiPut<UserBankSettingResponse>(`/gmail/banks/settings?ledger_id=${ledgerId}`, data)
  },

  // Scanning
  triggerScan: async (ledgerId: string, data?: TriggerScanRequest) => {
    return apiPost<ScanJobResponse>(`/ledgers/${ledgerId}/gmail/scan`, data || {})
  },

  getScanStatus: async (scanJobId: string) => {
    return apiGet<ScanJobResponse>(`/gmail/scan/${scanJobId}`)
  },

  getStatements: async (scanJobId: string) => {
    return apiGet<{ statements: DiscoveredStatementResponse[] }>(
      `/gmail/scan/${scanJobId}/statements`
    )
  },

  // Preview & Import
  getStatementPreview: async (statementId: string, ledgerId: string) => {
    return apiGet<StatementPreviewResponse>(
      `/gmail/statements/${statementId}/preview?ledger_id=${ledgerId}`
    )
  },

  importStatement: async (ledgerId: string, statementId: string, data: ImportStatementRequest) => {
    return apiPost<ImportStatementResponse>(
      `/ledgers/${ledgerId}/gmail/statements/${statementId}/import`,
      data
    )
  },

  // History
  getScanHistory: async (ledgerId: string, limit = 20, offset = 0) => {
    return apiGet<{ items: ScanJobResponse[]; total: number }>(
      `/gmail/scan/history?ledger_id=${ledgerId}&limit=${limit}&offset=${offset}`
    )
  },

  // Schedule
  getSchedule: async (ledgerId: string) => {
    return apiGet<ScheduleSettingsResponse>(`/gmail/schedule?ledger_id=${ledgerId}`)
  },

  updateSchedule: async (ledgerId: string, data: UpdateScheduleRequest) => {
    return apiPut<ScheduleSettingsResponse>(`/gmail/schedule?ledger_id=${ledgerId}`, data)
  },
}
