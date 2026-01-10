'use client'

import { useMemo } from 'react'
import { useTranslations } from 'next-intl'

import type { Account, AccountType } from '@/types'

interface AccountSelectProps {
  /** All available accounts */
  accounts: Account[]
  /** Currently selected account ID */
  value: string
  /** Callback when selection changes */
  onChange: (accountId: string) => void
  /** Filter accounts to only these types */
  allowedTypes: AccountType[]
  /** Account ID to exclude from options (e.g., already selected as other account) */
  excludeAccountId?: string
  /** Placeholder text when no selection */
  placeholder?: string
  /** HTML id attribute */
  id?: string
  /** Whether the field is required */
  required?: boolean
  /** Whether the select is disabled */
  disabled?: boolean
  /** Test ID for testing */
  'data-testid'?: string
}

/** Order for account type groups */
const TYPE_ORDER: AccountType[] = ['ASSET', 'LIABILITY', 'INCOME', 'EXPENSE']

/**
 * AccountSelect - A hierarchical account dropdown
 *
 * Features:
 * - Groups accounts by type with headers
 * - Shows hierarchy through indentation (based on depth)
 * - Filters accounts by allowed types
 * - Excludes specific accounts (e.g., the other account in a transaction)
 * - Only shows leaf accounts (accounts without children) for transaction entry
 */
export function AccountSelect({
  accounts,
  value,
  onChange,
  allowedTypes,
  excludeAccountId,
  placeholder,
  id,
  required,
  disabled,
  'data-testid': testId,
}: AccountSelectProps) {
  const t = useTranslations()

  // Filter and group accounts
  const groupedAccounts = useMemo(() => {
    // Filter by allowed types, exclude specific account, and only show leaf accounts
    const filtered = accounts.filter(
      (account) =>
        allowedTypes.includes(account.type) &&
        account.id !== excludeAccountId &&
        !account.has_children
    )

    // Group by type
    const groups = new Map<AccountType, Account[]>()
    for (const type of TYPE_ORDER) {
      if (allowedTypes.includes(type)) {
        groups.set(type, [])
      }
    }

    // Sort accounts by sort_order within each type
    filtered
      .sort((a, b) => a.sort_order - b.sort_order)
      .forEach((account) => {
        const group = groups.get(account.type)
        if (group) {
          group.push(account)
        }
      })

    return groups
  }, [accounts, allowedTypes, excludeAccountId])

  // Check if there are any accounts to show
  const hasAccounts = useMemo(() => {
    for (const accounts of groupedAccounts.values()) {
      if (accounts.length > 0) return true
    }
    return false
  }, [groupedAccounts])

  const defaultPlaceholder = t('transactionForm.selectAccount')

  return (
    <select
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required={required}
      disabled={disabled}
      data-testid={testId}
      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
    >
      <option value="">{placeholder || defaultPlaceholder}</option>
      {hasAccounts &&
        TYPE_ORDER.filter((type) => allowedTypes.includes(type)).map((type) => {
          const typeAccounts = groupedAccounts.get(type)
          if (!typeAccounts || typeAccounts.length === 0) return null

          return (
            <optgroup key={type} label={t(`accountTypes.${type}`)}>
              {typeAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {/* Indent based on depth using em-spaces */}
                  {account.depth > 0 ? '\u2003'.repeat(account.depth) : ''}
                  {account.name}
                </option>
              ))}
            </optgroup>
          )
        })}
    </select>
  )
}
