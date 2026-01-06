/**
 * Dashboard view models and API response types.
 * Based on data-model.md for feature 002-ui-layout-dashboard.
 */

// Account types from existing model
export type AccountType = 'ASSET' | 'LIABILITY' | 'INCOME' | 'EXPENSE'
export type TransactionType = 'EXPENSE' | 'INCOME' | 'TRANSFER'

/**
 * Sidebar account item for navigation.
 */
export interface SidebarAccountItem {
  id: string
  name: string
  type: AccountType
  balance: number
}

/**
 * Category grouping for sidebar display.
 */
export interface SidebarCategory {
  type: AccountType
  label: string
  accounts: SidebarAccountItem[]
  isExpanded: boolean
}

/**
 * Monthly trend data for charts.
 */
export interface MonthlyTrend {
  month: string
  year: number
  income: number
  expenses: number
}

/**
 * Current month income/expense summary.
 */
export interface CurrentMonthSummary {
  income: number
  expenses: number
  netCashFlow: number
}

/**
 * Main dashboard summary data.
 */
export interface DashboardSummary {
  totalAssets: number
  currentMonth: CurrentMonthSummary
  trends: MonthlyTrend[]
}

/**
 * API response for dashboard endpoint.
 */
export interface DashboardResponse {
  total_assets: number
  current_month: {
    income: number
    expenses: number
    net_cash_flow: number
  }
  trends: Array<{
    month: string
    year: number
    income: number
    expenses: number
  }>
}

/**
 * API response for accounts by category.
 */
export interface AccountsByCategoryResponse {
  categories: Array<{
    type: AccountType
    accounts: Array<{
      id: string
      name: string
      balance: number
    }>
  }>
}

/**
 * Transaction list item for account view.
 */
export interface TransactionListItem {
  id: string
  date: string
  description: string
  amount: number
  type: TransactionType
  otherAccountName: string
}

/**
 * API response for account transactions.
 */
export interface AccountTransactionsResponse {
  account_id: string
  account_name: string
  transactions: Array<{
    id: string
    date: string
    description: string
    amount: number
    type: TransactionType
    other_account_name: string
  }>
  total_count: number
  page: number
  page_size: number
  has_more: boolean
}

/**
 * Category display configuration.
 */
export const CATEGORY_CONFIG: Record<
  AccountType,
  { label: string; icon: string }
> = {
  ASSET: { label: 'Assets', icon: 'Wallet' },
  LIABILITY: { label: 'Loans', icon: 'CreditCard' },
  INCOME: { label: 'Income', icon: 'TrendingUp' },
  EXPENSE: { label: 'Expenses', icon: 'Receipt' },
}

/**
 * Transform API response to frontend DashboardSummary.
 */
export function transformDashboardResponse(
  response: DashboardResponse
): DashboardSummary {
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

/**
 * Transform API response to frontend SidebarCategory array.
 */
export function transformAccountsByCategoryResponse(
  response: AccountsByCategoryResponse
): SidebarCategory[] {
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

/**
 * Transform API transaction response to frontend TransactionListItem array.
 */
export function transformTransactionsResponse(
  response: AccountTransactionsResponse
): TransactionListItem[] {
  return response.transactions.map((t) => ({
    id: t.id,
    date: t.date,
    description: t.description,
    amount: t.amount,
    type: t.type,
    otherAccountName: t.other_account_name,
  }))
}
