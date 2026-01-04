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
  created_at: string
  updated_at: string
}

export interface AccountCreate {
  name: string
  type: AccountType
}

export interface AccountUpdate {
  name?: string
}

export interface AccountListItem {
  id: string
  name: string
  type: AccountType
  balance: string
  is_system: boolean
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
}

export interface TransactionUpdate {
  date: string
  description: string
  amount: number
  from_account_id: string
  to_account_id: string
  transaction_type: TransactionType
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
