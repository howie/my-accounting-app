'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronDown, ChevronRight, Wallet, CreditCard, TrendingUp, Receipt } from 'lucide-react'
import type { SidebarCategory, SidebarAccountItem, AccountType } from '@/types/dashboard'
import { cn } from '@/lib/utils'

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
}

/**
 * Expandable sidebar category item with nested account links.
 */
export function SidebarItem({
  category,
  isExpanded,
  onToggle,
  selectedAccountId,
}: SidebarItemProps) {
  const Icon = iconMap[category.type]
  const pathname = usePathname()

  return (
    <div className="mb-1">
      {/* Category Header */}
      <button
        onClick={onToggle}
        className={cn(
          'flex w-full items-center justify-between px-3 py-2 text-sm font-medium rounded-md',
          'text-sidebar-foreground/80 hover:text-sidebar-foreground hover:bg-sidebar-accent/10',
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
          className="mt-1 ml-4 space-y-0.5"
          role="group"
          aria-label={`${category.label} accounts`}
        >
          {category.accounts.map((account) => (
            <AccountLink
              key={account.id}
              account={account}
              isSelected={
                selectedAccountId === account.id ||
                pathname === `/accounts/${account.id}`
              }
              selectedAccountId={selectedAccountId}
              pathname={pathname}
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {isExpanded && category.accounts.length === 0 && (
        <div className="mt-1 ml-6 py-2 text-xs text-sidebar-foreground/40">
          No accounts
        </div>
      )}
    </div>
  )
}

interface AccountLinkProps {
  account: SidebarAccountItem
  isSelected: boolean
  selectedAccountId?: string
  pathname: string
}

function AccountLink({ account, isSelected, selectedAccountId, pathname }: AccountLinkProps) {
  // Calculate left padding based on depth (depth 1 = root, depth 2 = child, etc.)
  const paddingLeft = `${(account.depth - 1) * 12 + 12}px`

  return (
    <>
      <Link
        href={`/accounts/${account.id}`}
        style={{ paddingLeft }}
        className={cn(
          'flex items-center justify-between pr-3 py-1.5 text-sm rounded-md',
          'transition-colors duration-150',
          isSelected
            ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
            : 'text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent/10'
        )}
        title={account.name}
      >
        <span className="truncate max-w-[140px]">{account.name}</span>
        <span className="text-xs text-sidebar-foreground/50 ml-2">
          {formatBalance(account.balance)}
        </span>
      </Link>
      {/* Recursively render child accounts */}
      {account.children?.map((child) => (
        <AccountLink
          key={child.id}
          account={child}
          isSelected={selectedAccountId === child.id || pathname === `/accounts/${child.id}`}
          selectedAccountId={selectedAccountId}
          pathname={pathname}
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
