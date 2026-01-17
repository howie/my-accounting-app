'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Home, Menu, X, BookOpen, Settings, Upload, MessageCircle, PanelLeftClose, PanelLeftOpen, Library, Clock, Wallet, CreditCard, TrendingUp, Receipt, Download, BarChart3, PieChart } from 'lucide-react'
import { useSidebarAccounts } from '@/lib/hooks/useSidebarAccounts'
import { useSidebarState } from '@/lib/hooks/useSidebarState'
import { useRecentAccounts } from '@/lib/hooks/useRecentAccounts'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { useChatContext } from '@/lib/context/ChatContext'
import { SidebarItem } from './SidebarItem'
import { ExportModal } from '@/components/export/ExportModal'
import { cn } from '@/lib/utils'
import type { AccountType } from '@/types/dashboard'

const iconMap: Record<AccountType, React.ComponentType<{ className?: string }>> = {
  ASSET: Wallet,
  LIABILITY: CreditCard,
  INCOME: TrendingUp,
  EXPENSE: Receipt,
}

/**
 * Dark-themed sidebar with expandable account categories.
 * Responsive: collapsible on mobile with hamburger menu.
 * Desktop: Collapsible to icon-only mode.
 */
export function Sidebar() {
  const pathname = usePathname()
  const { currentLedger } = useLedgerContext()
  const { openChat } = useChatContext()
  const { data: categories, isLoading, error } = useSidebarAccounts()
  const { recents, isHydrated: recentsHydrated } = useRecentAccounts()
  const t = useTranslations('sidebar')
  const {
    isCollapsed,
    toggleCollapsed,
    setCollapsed,
    toggleCategory,
    isCategoryExpanded,
    isHydrated,
  } = useSidebarState()

  // Close mobile sidebar on navigation
  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      setCollapsed(true)
    }
  }, [pathname, setCollapsed])

  // Don't render until hydrated to avoid layout shift
  if (!isHydrated) {
    return <aside className="hidden bg-sidebar lg:flex lg:w-64 lg:flex-col" />
  }

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={toggleCollapsed}
        className={cn(
          'fixed left-4 top-4 z-50 rounded-md p-2 lg:hidden',
          'bg-sidebar text-sidebar-foreground',
          'transition-colors hover:bg-sidebar-accent/20'
        )}
        aria-label={isCollapsed ? 'Open menu' : 'Close menu'}
        aria-expanded={!isCollapsed}
      >
        {isCollapsed ? <Menu className="h-5 w-5" /> : <X className="h-5 w-5" />}
      </button>

      {/* Mobile overlay */}
      {!isCollapsed && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setCollapsed(true)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex flex-col bg-sidebar',
          'transform transition-all duration-200 ease-in-out',
          'lg:relative lg:translate-x-0',
          // Mobile: hidden (translated) or shown
          isCollapsed ? '-translate-x-full lg:translate-x-0' : 'translate-x-0',
          // Desktop: Width transition
          isCollapsed ? 'lg:w-16' : 'lg:w-64'
        )}
      >
        {/* Header/Branding */}
        <div className={cn(
            "flex h-16 items-center border-b border-sidebar-border px-4 transition-all overflow-hidden",
            isCollapsed ? "justify-center px-2" : "gap-2"
        )}>
          <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap">
             <BookOpen className="h-6 w-6 flex-shrink-0 text-sidebar-accent" />
             <span className={cn(
                 "text-lg font-semibold text-sidebar-foreground transition-opacity duration-200",
                 isCollapsed ? "opacity-0 w-0 hidden" : "opacity-100"
             )}>
               LedgerOne
             </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2 py-4">

          {/* Switch Ledger (Moved to top) */}
          <Link
            href="/ledgers"
            title={t('switchLedger')}
            className={cn(
              'mb-2 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
              'transition-colors duration-150',
              'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
              isCollapsed && 'justify-center px-0'
            )}
          >
            <Library className="h-4 w-4 flex-shrink-0" />
            <span className={cn(isCollapsed && 'hidden')}>{t('switchLedger')}</span>
          </Link>

          {/* Dashboard Link */}
          <Link
            href="/"
            title={t('dashboard')}
            className={cn(
              'mb-2 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
              'transition-colors duration-150',
              pathname === '/'
                ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
              isCollapsed && 'justify-center px-0'
            )}
          >
            <Home className="h-4 w-4 flex-shrink-0" />
            <span className={cn(isCollapsed && 'hidden')}>{t('dashboard')}</span>
          </Link>

          {/* Reports */}
          {currentLedger && (
            <>
              {!isCollapsed && (
                <div className="mb-2 px-3 mt-2">
                  <p className="text-xs uppercase tracking-wider text-sidebar-foreground/50">
                    Reports
                  </p>
                </div>
              )}
              {isCollapsed && (
                <div className="my-2 h-px bg-sidebar-border w-full" />
              )}

              <Link
                href="/reports/balance-sheet"
                title="Balance Sheet"
                className={cn(
                  'mb-1 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                  'transition-colors duration-150',
                  pathname === '/reports/balance-sheet'
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
                  isCollapsed && 'justify-center px-0'
                )}
              >
                <PieChart className="h-4 w-4 flex-shrink-0" />
                <span className={cn(isCollapsed && 'hidden')}>Balance Sheet</span>
              </Link>

              <Link
                href="/reports/income-statement"
                title="Income Statement"
                className={cn(
                  'mb-4 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                  'transition-colors duration-150',
                  pathname === '/reports/income-statement'
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
                  isCollapsed && 'justify-center px-0'
                )}
              >
                <BarChart3 className="h-4 w-4 flex-shrink-0" />
                <span className={cn(isCollapsed && 'hidden')}>Income Statement</span>
              </Link>
            </>
          )}

          {/* Quick Actions (Import, Chat, Settings) */}
          {currentLedger && (
            <>
              <Link
                href={`/ledgers/${currentLedger.id}/import`}
                title={t('import')}
                className={cn(
                  'mb-1 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                  'transition-colors duration-150',
                  (pathname ?? '').includes('/import')
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
                  isCollapsed && 'justify-center px-0'
                )}
              >
                <Upload className="h-4 w-4 flex-shrink-0" />
                <span className={cn(isCollapsed && 'hidden')}>{t('import')}</span>
              </Link>

              {/* Export - Using Modal */}
              <ExportModal>
                <button
                    title="Export"
                    className={cn(
                    'mb-1 flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                    'transition-colors duration-150',
                    'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
                    isCollapsed && 'justify-center px-0'
                    )}
                >
                    <Download className="h-4 w-4 flex-shrink-0" />
                    <span className={cn(isCollapsed && 'hidden')}>Export</span>
                </button>
              </ExportModal>
            </>
          )}

          <button
            onClick={openChat}
            title={t('chat')}
            className={cn(
              'mb-1 flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
              'transition-colors duration-150',
              'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
              isCollapsed && 'justify-center px-0'
            )}
          >
            <MessageCircle className="h-4 w-4 flex-shrink-0" />
            <span className={cn(isCollapsed && 'hidden')}>{t('chat')}</span>
          </button>

          <Link
            href="/settings"
            title={t('settings')}
            className={cn(
              'mb-4 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
              'transition-colors duration-150',
              (pathname ?? '').startsWith('/settings')
                ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
              isCollapsed && 'justify-center px-0'
            )}
          >
            <Settings className="h-4 w-4 flex-shrink-0" />
            <span className={cn(isCollapsed && 'hidden')}>{t('settings')}</span>
          </Link>

          {/* Recent Accounts */}
          {recentsHydrated && recents.length > 0 && (
             <>
                {!isCollapsed && (
                     <div className="mb-2 px-3 mt-4">
                        <p className="text-xs uppercase tracking-wider text-sidebar-foreground/50 flex items-center gap-1">
                            <Clock className="h-3 w-3" /> Recent
                        </p>
                    </div>
                )}
                 {isCollapsed && (
                    <div className="my-2 h-px bg-sidebar-border w-full" />
                )}

                {recents.map(account => {
                    const Icon = iconMap[account.type] || Home
                    return (
                        <Link
                            key={account.id}
                            href={`/accounts/${account.id}`}
                            title={account.name}
                            className={cn(
                              'mb-1 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                              'transition-colors duration-150',
                              pathname === `/accounts/${account.id}`
                                ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                                : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground',
                              isCollapsed && 'justify-center px-0'
                            )}
                        >
                            <Icon className="h-4 w-4 flex-shrink-0" />
                            <span className={cn(isCollapsed && 'hidden', "truncate")}>{account.name}</span>
                        </Link>
                    )
                })}
             </>
          )}

          {/* Category Divider */}
          {!isCollapsed && (
             <div className="mb-2 px-3 mt-4 fade-in duration-300">
                <p className="text-xs uppercase tracking-wider text-sidebar-foreground/50">
                {t('accounts')}
                </p>
            </div>
          )}
          {isCollapsed && (
              <div className="my-2 h-px bg-sidebar-border w-full" />
          )}

          {/* Loading State */}
          {isLoading && !isCollapsed && (
            <div className="space-y-3 px-3 py-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-8 rounded-md bg-sidebar-accent/20" />
                </div>
              ))}
            </div>
          )}

          {/* Error State */}
          {error && !isCollapsed && <div className="px-3 py-4 text-sm text-red-400">{t('failedToLoad')}</div>}

          {/* Categories */}
          {/* In collapsed mode, we only show icons for categories if we wanted to support navigation to category summary.
              But for now, let's just hide the list in collapsed mode to keep it clean or implement popovers later.
              Actually, hiding it makes the sidebar useless for accounts.
              Let's show Category Icons. Clicking them expands the sidebar?
          */}
          {categories &&
            categories.map((category) => (
                isCollapsed ? (
                    <button
                        key={category.type}
                        title={category.label}
                        onClick={() => setCollapsed(false)}
                        className={cn(
                            'mb-1 flex w-full justify-center rounded-md py-2',
                            'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground'
                        )}
                    >
                        <SidebarItem
                            category={category}
                            isExpanded={false}
                            onToggle={() => {}}
                            selectedAccountId={undefined}
                            iconOnly={true} // Need to update SidebarItem to handle this or just pass dummy
                        />
                         {/* Or just render the icon directly here to avoid updating SidebarItem prop interface yet */}
                    </button>
                ) : (
                    <SidebarItem
                        key={category.type}
                        category={category}
                        isExpanded={isCategoryExpanded(category.type)}
                        onToggle={() => toggleCategory(category.type)}
                    />
                )
            ))}

          {/* No Ledger State */}
          {!currentLedger && !isLoading && !isCollapsed && (
            <div className="px-3 py-4 text-sm text-sidebar-foreground/50">
              {t('selectLedgerToView')}
            </div>
          )}
        </nav>

        {/* Desktop Toggle Button */}
        <div className="hidden lg:flex border-t border-sidebar-border p-3 justify-end">
            <button
                onClick={toggleCollapsed}
                className="p-2 text-sidebar-foreground/50 hover:text-sidebar-foreground hover:bg-sidebar-accent/10 rounded-md transition-colors"
                title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            >
                {isCollapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
            </button>
        </div>
      </aside>
    </>
  )
}
