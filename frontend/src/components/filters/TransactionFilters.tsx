'use client'

import { useState, useCallback } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { TransactionFilters } from '@/lib/hooks/useTransactions'
import type { AccountListItem, TransactionType } from '@/types'

interface TransactionFiltersProps {
  accounts: AccountListItem[]
  filters: TransactionFilters
  onFiltersChange: (filters: TransactionFilters) => void
}

const transactionTypes: { value: TransactionType | ''; label: string }[] = [
  { value: '', label: 'All Types' },
  { value: 'EXPENSE', label: 'Expense' },
  { value: 'INCOME', label: 'Income' },
  { value: 'TRANSFER', label: 'Transfer' },
]

export function TransactionFiltersComponent({
  accounts,
  filters,
  onFiltersChange,
}: TransactionFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search || '')

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
    filters.transactionType

  return (
    <div className="mb-6 rounded-lg border p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-medium">Filters</h3>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={handleClearFilters}>
            Clear All
          </Button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <Input
            type="text"
            placeholder="Search description..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" variant="secondary" size="sm">
            Search
          </Button>
        </form>

        {/* From Date */}
        <div>
          <label htmlFor="fromDate" className="mb-1 block text-xs text-muted-foreground">
            From Date
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
            To Date
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
            Account
          </label>
          <select
            id="account"
            value={filters.accountId || ''}
            onChange={handleAccountChange}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">All Accounts</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.type})
              </option>
            ))}
          </select>
        </div>

        {/* Transaction Type Filter */}
        <div>
          <label htmlFor="type" className="mb-1 block text-xs text-muted-foreground">
            Type
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
      </div>
    </div>
  )
}
