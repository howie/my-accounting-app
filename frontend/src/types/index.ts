/**
 * TypeScript types matching backend models.
 */

// Enums
export type AccountType = 'ASSET' | 'LIABILITY' | 'INCOME' | 'EXPENSE'
export type TransactionType = 'EXPENSE' | 'INCOME' | 'TRANSFER'

// User
export interface User {
  id: string
  email: string
  created_at: string
}

export interface UserSetup {
  email: string
}

// Ledger
export interface Ledger {
  id: string
  user_id: string
  name: string
  initial_balance: string
  created_at: string
}

export interface LedgerCreate {
  name: string
  initial_balance?: number
}

export interface LedgerUpdate {
  name?: string
}

// Account
export interface Account {
  id: string
  ledger_id: string
  name: string
  type: AccountType
  balance: string
  is_system: boolean
  parent_id: string | null
  depth: number
  sort_order: number
  has_children: boolean
  created_at: string
  updated_at: string
}

export interface AccountCreate {
  name: string
  type: AccountType
  parent_id?: string | null
}

export interface AccountUpdate {
  name?: string
  parent_id?: string | null
}

export interface AccountListItem {
  id: string
  name: string
  type: AccountType
  balance: string
  is_system: boolean
  parent_id: string | null
  depth: number
  sort_order: number
  has_children: boolean
}

export interface AccountTreeNode {
  id: string
  name: string
  type: AccountType
  balance: string
  is_system: boolean
  parent_id: string | null
  depth: number
  sort_order: number
  children: AccountTreeNode[]
}

// Transaction
export interface Transaction {
  id: string
  ledger_id: string
  date: string
  description: string
  amount: string
  from_account_id: string
  to_account_id: string
  transaction_type: TransactionType
  notes: string | null
  amount_expression: string | null
  created_at: string
  updated_at: string
}

export interface TransactionCreate {
  date: string
  description: string
  amount: number
  from_account_id: string
  to_account_id: string
  transaction_type: TransactionType
  notes?: string | null
  amount_expression?: string | null
}

export interface TransactionUpdate {
  date: string
  description: string
  amount: number
  from_account_id: string
  to_account_id: string
  transaction_type: TransactionType
  notes?: string | null
  amount_expression?: string | null
}

export interface AccountSummary {
  id: string
  name: string
  type: AccountType
}

export interface TransactionListItem {
  id: string
  date: string
  description: string
  amount: string
  from_account: AccountSummary
  to_account: AccountSummary
  transaction_type: TransactionType
}

// Pagination
export interface PaginatedResponse<T> {
  data: T[]
  cursor: string | null
  has_more: boolean
}

// User Preferences (stored in localStorage)
export interface UserPreferences {
  language: 'zh-TW' | 'en'
  theme: 'light' | 'dark' | 'system'
}

// Can Delete Response
export interface CanDeleteResponse {
  can_delete: boolean
  has_children: boolean
  has_transactions: boolean
  transaction_count: number
  child_count: number
}

// Reassign Response
export interface ReassignResponse {
  transactions_moved: number
  deleted_account_id: string
}

// Account Reorder Request
export interface AccountReorderRequest {
  parent_id: string | null
  account_ids: string[]
}

// Transaction Template
export interface TransactionTemplate {
  id: string
  ledger_id: string
  name: string
  transaction_type: TransactionType
  from_account_id: string
  to_account_id: string
  amount: string
  description: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface TransactionTemplateCreate {
  name: string
  transaction_type: TransactionType
  from_account_id: string
  to_account_id: string
  amount: number
  description: string
}

export interface TransactionTemplateUpdate {
  name?: string
  transaction_type?: TransactionType
  from_account_id?: string
  to_account_id?: string
  amount?: number
  description?: string
}

export interface TransactionTemplateListItem {
  id: string
  name: string
  transaction_type: TransactionType
  from_account_id: string
  to_account_id: string
  amount: string
  description: string
  sort_order: number
}

export interface TransactionTemplateList {
  data: TransactionTemplateListItem[]
  total: number
}

export interface ApplyTemplateRequest {
  date?: string
  notes?: string
}

export interface ReorderTemplatesRequest {
  template_ids: string[]
}

// API Token
export interface ApiToken {
  id: string
  user_id: string
  name: string
  token_prefix: string
  created_at: string
  last_used_at: string | null
  is_active: boolean
}

export interface ApiTokenCreate {
  name: string
}

export interface ApiTokenCreateResponse {
  id: string
  name: string
  token: string
  token_prefix: string
  created_at: string
}

export interface ApiTokenList {
  data: ApiToken[]
  total: number
}
