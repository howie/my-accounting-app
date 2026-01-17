'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronDown, ChevronRight, Wallet, CreditCard, TrendingUp, Receipt } from 'lucide-react'
import type { SidebarCategory, SidebarAccountItem, AccountType } from '@/types/dashboard'
import { cn } from '@/lib/utils'
import { aggregateBalance, hasChildren } from '@/lib/utils/aggregateBalance'
import { useExpandedAccounts } from '@/lib/hooks/useExpandedAccounts'

const iconMap: Record<AccountType, React.ComponentType<{ className?: string }>> = {
  ASSET: Wallet,
  LIABILITY: CreditCard,
  INCOME: TrendingUp,
  EXPENSE: Receipt,
}

interface SidebarItemProps {
  category: SidebarCategory
  isExpanded: boolean
  onToggle: () => void
  selectedAccountId?: string
  iconOnly?: boolean
}

/**
 * Expandable sidebar category item with nested account links.
 * Supports collapsible 3-level account hierarchy with aggregated balances.
 *
 * T137-T142 [US6a] - Updated for collapsible accounts with aggregated balances
 */
export function SidebarItem({
  category,
  isExpanded,
  onToggle,
  selectedAccountId,
  iconOnly = false,
}: SidebarItemProps) {
  const Icon = iconMap[category.type]
  const pathname = usePathname()
  const { isExpanded: isAccountExpanded, toggleExpanded } = useExpandedAccounts()

  if (iconOnly) {
    return <Icon className="h-4 w-4" />
  }

  return (
    <div className="mb-1">
      {/* Category Header */}
      <button
        onClick={onToggle}
        className={cn(
          'flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-medium',
          'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
          'transition-colors duration-150'
        )}
        aria-expanded={isExpanded}
        aria-controls={`category-${category.type}`}
      >
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" />
          <span>{category.label}</span>
          {category.accounts.length > 0 && (
            <span className="ml-1 text-xs text-sidebar-foreground/50">
              ({category.accounts.length})
            </span>
          )}
        </div>
        {category.accounts.length > 0 && (
          <span className="text-sidebar-foreground/50">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </span>
        )}
      </button>

      {/* Account List */}
      {isExpanded && category.accounts.length > 0 && (
        <div
          id={`category-${category.type}`}
          className="ml-4 mt-1 space-y-0.5"
          role="group"
          aria-label={`${category.label} accounts`}
        >
          {category.accounts.map((account) => (
            <AccountRow
              key={account.id}
              account={account}
              isSelected={
                selectedAccountId === account.id || pathname === `/accounts/${account.id}`
              }
              selectedAccountId={selectedAccountId}
              pathname={pathname}
              isAccountExpanded={isAccountExpanded}
              toggleAccountExpanded={toggleExpanded}
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {isExpanded && category.accounts.length === 0 && (
        <div className="ml-6 mt-1 py-2 text-xs text-sidebar-foreground/40">No accounts</div>
      )}
    </div>
  )
}

interface AccountRowProps {
  account: SidebarAccountItem
  isSelected: boolean
  selectedAccountId?: string
  pathname: string | null
  isAccountExpanded: (id: string) => boolean
  toggleAccountExpanded: (id: string) => void
}

/**
 * Individual account row with support for hierarchical expand/collapse.
 * Shows aggregated balance for parent accounts and chevron toggle.
 */
function AccountRow({
  account,
  isSelected,
  selectedAccountId,
  pathname,
  isAccountExpanded,
  toggleAccountExpanded,
}: AccountRowProps) {
  const isParent = hasChildren(account)
  const isExpanded = isAccountExpanded(account.id)

  // Calculate aggregated balance (includes children)
  const displayBalance = aggregateBalance(account)

  // Calculate left padding based on depth (depth 1 = root, depth 2 = child, etc.)
  const paddingLeft = `${(account.depth - 1) * 12 + 12}px`

  return (
    <>
      <div className="flex items-center">
        {/* Expand/Collapse button for parent accounts */}
        {isParent && (
          <button
            onClick={() => toggleAccountExpanded(account.id)}
            className="mr-1 flex h-5 w-5 items-center justify-center rounded text-sidebar-foreground/50 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground"
            aria-expanded={isExpanded}
            aria-label={isExpanded ? `Collapse ${account.name}` : `Expand ${account.name}`}
            data-testid="chevron"
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </button>
        )}

        {/* Spacer for leaf accounts to align with parents */}
        {!isParent && <div className="mr-1 h-5 w-5" />}

        {/* Account link */}
        <Link
          href={`/accounts/${account.id}`}
          style={{ paddingLeft }}
          className={cn(
            'flex flex-1 items-center justify-between rounded-md py-1.5 pr-3 text-sm',
            'transition-colors duration-150',
            isSelected
              ? 'bg-sidebar-accent font-medium text-sidebar-accent-foreground'
              : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground'
          )}
          title={account.name}
        >
          <span className="max-w-[120px] truncate">{account.name}</span>
          <span className="ml-2 flex items-center text-xs text-sidebar-foreground/50">
            {formatBalance(displayBalance)}
            {isParent && <span className="ml-1">(total)</span>}
          </span>
        </Link>
      </div>

      {/* Render children only when expanded */}
      {isParent &&
        isExpanded &&
        account.children?.map((child) => (
          <AccountRow
            key={child.id}
            account={child}
            isSelected={selectedAccountId === child.id || pathname === `/accounts/${child.id}`}
            selectedAccountId={selectedAccountId}
            pathname={pathname}
            isAccountExpanded={isAccountExpanded}
            toggleAccountExpanded={toggleAccountExpanded}
          />
        ))}
    </>
  )
}

function formatBalance(amount: number): string {
  const absAmount = Math.abs(amount)
  if (absAmount >= 1000000) {
    return `${(amount / 1000000).toFixed(1)}M`
  }
  if (absAmount >= 1000) {
    return `${(amount / 1000).toFixed(1)}K`
  }
  return amount.toLocaleString()
}
