import { useTranslation } from 'react-i18next'
import { Card } from '@tremor/react'
import { Wallet, TrendingUp, TrendingDown, CreditCard, Scale } from 'lucide-react'

interface SummaryCardsProps {
  totalAssets: number
  totalLiabilities: number
  income: number
  expenses: number
  isLoading?: boolean
}

export function SummaryCards({
  totalAssets,
  totalLiabilities,
  income,
  expenses,
  isLoading,
}: SummaryCardsProps) {
  const { t, i18n } = useTranslation()

  const formatCurrency = (value: number) => {
    const isZhTW = i18n.language === 'zh-TW'
    return new Intl.NumberFormat(isZhTW ? 'zh-TW' : 'en-US', {
      style: 'currency',
      currency: isZhTW ? 'TWD' : 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const netIncome = income - expenses

  // Helper to render skeleton
  const SkeletonCard = () => (
    <Card className="p-4">
      <div className="flex animate-pulse items-center gap-4">
        <div className="h-10 w-10 rounded-full bg-gray-200 dark:bg-gray-800" />
        <div className="space-y-2">
          <div className="h-4 w-20 rounded bg-gray-200 dark:bg-gray-800" />
          <div className="h-6 w-32 rounded bg-gray-200 dark:bg-gray-800" />
        </div>
      </div>
    </Card>
  )

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
      {/* Total Assets */}
      <Card className="flex items-center gap-4 border-l-4 border-l-indigo-400 p-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400">
          <Wallet className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t('dashboard.totalAssets')}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(totalAssets)}
          </p>
        </div>
      </Card>

      {/* Total Liabilities */}
      <Card className="flex items-center gap-4 border-l-4 border-l-orange-400 p-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400">
          <CreditCard className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t('dashboard.totalLiabilities')}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(totalLiabilities)}
          </p>
        </div>
      </Card>

      {/* Monthly Income */}
      <Card className="flex items-center gap-4 border-l-4 border-l-emerald-400 p-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400">
          <TrendingUp className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t('dashboard.monthlyIncome')}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(income)}
          </p>
        </div>
      </Card>

      {/* Monthly Expenses */}
      <Card className="flex items-center gap-4 border-l-4 border-l-rose-400 p-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400">
          <TrendingDown className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t('dashboard.monthlyExpenses')}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(expenses)}
          </p>
        </div>
      </Card>

      {/* Net Income */}
      <Card
        className={`flex items-center gap-4 border-l-4 p-4 ${netIncome >= 0 ? 'border-l-emerald-400' : 'border-l-rose-400'}`}
      >
        <div
          className={`flex h-12 w-12 items-center justify-center rounded-full ${netIncome >= 0 ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400'}`}
        >
          <Scale className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {t('dashboard.netIncome')}
          </p>
          <p
            className={`text-2xl font-bold ${netIncome >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}
          >
            {formatCurrency(netIncome)}
          </p>
        </div>
      </Card>
    </div>
  )
}
