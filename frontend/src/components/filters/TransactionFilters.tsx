

import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useTags } from '@/lib/hooks/useTags'
import type { TransactionFilters } from '@/lib/hooks/useTransactions'
import type { AccountListItem, TransactionType } from '@/types'

interface TransactionFiltersProps {
  accounts: AccountListItem[]
  filters: TransactionFilters
  onFiltersChange: (filters: TransactionFilters) => void
}

const transactionTypeKeys: (TransactionType | '')[] = ['', 'EXPENSE', 'INCOME', 'TRANSFER']

export function TransactionFiltersComponent({
  accounts,
  filters,
  onFiltersChange,
}: TransactionFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search || '')
  const { data: tags = [] } = useTags()
  const { t } = useTranslation()

  const transactionTypes = transactionTypeKeys.map((value) => ({
    value,
    label: value === '' ? t('filters.allTypes') : t(`transactionTypes.${value}`),
  }))

  const handleSearchSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      onFiltersChange({ ...filters, search: searchInput || undefined })
    },
    [filters, searchInput, onFiltersChange]
  )

  const handleFromDateChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFiltersChange({ ...filters, fromDate: e.target.value || undefined })
    },
    [filters, onFiltersChange]
  )

  const handleToDateChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFiltersChange({ ...filters, toDate: e.target.value || undefined })
    },
    [filters, onFiltersChange]
  )

  const handleAccountChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onFiltersChange({ ...filters, accountId: e.target.value || undefined })
    },
    [filters, onFiltersChange]
  )

  const handleTagChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onFiltersChange({ ...filters, tagId: e.target.value || undefined })
    },
    [filters, onFiltersChange]
  )

  const handleTypeChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const value = e.target.value as TransactionType | ''
      onFiltersChange({
        ...filters,
        transactionType: value || undefined,
      })
    },
    [filters, onFiltersChange]
  )

  const handleClearFilters = useCallback(() => {
    setSearchInput('')
    onFiltersChange({})
  }, [onFiltersChange])

  const hasActiveFilters =
    filters.search ||
    filters.fromDate ||
    filters.toDate ||
    filters.accountId ||
    filters.transactionType ||
    filters.tagId

  return (
    <div className="mb-6 rounded-lg border p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-medium">{t('filters.title')}</h3>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={handleClearFilters}>
            {t('common.clearAll')}
          </Button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <Input
            type="text"
            placeholder={t('filters.searchPlaceholder')}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" variant="secondary" size="sm">
            {t('common.search')}
          </Button>
        </form>

        {/* From Date */}
        <div>
          <label htmlFor="fromDate" className="mb-1 block text-xs text-muted-foreground">
            {t('filters.fromDate')}
          </label>
          <Input
            id="fromDate"
            type="date"
            value={filters.fromDate || ''}
            onChange={handleFromDateChange}
          />
        </div>

        {/* To Date */}
        <div>
          <label htmlFor="toDate" className="mb-1 block text-xs text-muted-foreground">
            {t('filters.toDate')}
          </label>
          <Input
            id="toDate"
            type="date"
            value={filters.toDate || ''}
            onChange={handleToDateChange}
          />
        </div>

        {/* Account Filter */}
        <div>
          <label htmlFor="account" className="mb-1 block text-xs text-muted-foreground">
            {t('filters.account')}
          </label>
          <select
            id="account"
            value={filters.accountId || ''}
            onChange={handleAccountChange}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">{t('filters.allAccounts')}</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name} ({t(`accountTypes.${account.type}`)})
              </option>
            ))}
          </select>
        </div>

        {/* Transaction Type Filter */}
        <div>
          <label htmlFor="type" className="mb-1 block text-xs text-muted-foreground">
            {t('filters.type')}
          </label>
          <select
            id="type"
            value={filters.transactionType || ''}
            onChange={handleTypeChange}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {transactionTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Tag Filter */}
        <div>
          <label htmlFor="tag" className="mb-1 block text-xs text-muted-foreground">
            {t('tags.title')}
          </label>
          <select
            id="tag"
            value={filters.tagId || ''}
            onChange={handleTagChange}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">{t('filters.allTags')}</option>
            {tags.map((tag) => (
              <option key={tag.id} value={tag.id}>
                {tag.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
