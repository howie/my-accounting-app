export interface ReportEntry {
  account_id: string | null
  name: string
  amount: string // Decimal as string
  level: number
  children: ReportEntry[]
}

export interface BalanceSheet {
  date: string
  assets: ReportEntry[]
  liabilities: ReportEntry[]
  equity: ReportEntry[]
  total_assets: string
  total_liabilities: string
  total_equity: string
}

export interface IncomeStatement {
  start_date: string
  end_date: string
  income: ReportEntry[]
  expenses: ReportEntry[]
  total_income: string
  total_expenses: string
  net_income: string
}
