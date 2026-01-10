'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Home, Menu, X, BookOpen, Settings, Upload } from 'lucide-react'
import { useSidebarAccounts } from '@/lib/hooks/useSidebarAccounts'
import { useSidebarState } from '@/lib/hooks/useSidebarState'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { SidebarItem } from './SidebarItem'
import { cn } from '@/lib/utils'

/**
 * Dark-themed sidebar with expandable account categories.
 * Responsive: collapsible on mobile with hamburger menu.
 */
export function Sidebar() {
  const pathname = usePathname()
  const { currentLedger } = useLedgerContext()
  const { data: categories, isLoading, error } = useSidebarAccounts()
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
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-sidebar',
          'transform transition-transform duration-200 ease-in-out',
          'lg:relative lg:translate-x-0',
          isCollapsed ? '-translate-x-full' : 'translate-x-0'
        )}
      >
        {/* Header/Branding */}
        <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-4">
          <BookOpen className="h-6 w-6 text-sidebar-accent" />
          <span className="text-lg font-semibold text-sidebar-foreground">LedgerOne</span>
        </div>

        {/* Current Ledger */}
        {currentLedger && (
          <div className="border-b border-sidebar-border px-4 py-3">
            <p className="text-xs uppercase tracking-wider text-sidebar-foreground/50">
              {t('currentLedger')}
            </p>
            <p className="truncate text-sm font-medium text-sidebar-foreground">
              {currentLedger.name}
            </p>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-2 py-4">
          {/* Dashboard Link */}
          <Link
            href="/"
            className={cn(
              'mb-4 flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
              'transition-colors duration-150',
              pathname === '/'
                ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground'
            )}
          >
            <Home className="h-4 w-4" />
            <span>{t('dashboard')}</span>
          </Link>

          {/* Category Divider */}
          <div className="mb-2 px-3">
            <p className="text-xs uppercase tracking-wider text-sidebar-foreground/50">
              {t('accounts')}
            </p>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="space-y-3 px-3 py-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-8 rounded-md bg-sidebar-accent/20" />
                </div>
              ))}
            </div>
          )}

          {/* Error State */}
          {error && <div className="px-3 py-4 text-sm text-red-400">{t('failedToLoad')}</div>}

          {/* Categories */}
          {categories &&
            categories.map((category) => (
              <SidebarItem
                key={category.type}
                category={category}
                isExpanded={isCategoryExpanded(category.type)}
                onToggle={() => toggleCategory(category.type)}
              />
            ))}

          {/* No Ledger State */}
          {!currentLedger && !isLoading && (
            <div className="px-3 py-4 text-sm text-sidebar-foreground/50">
              {t('selectLedgerToView')}
            </div>
          )}
        </nav>

        {/* Import Link */}
        {currentLedger && (
          <div className="px-2 pb-2">
            <Link
              href={`/ledgers/${currentLedger.id}/import`}
              className={cn(
                'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                'transition-colors duration-150',
                pathname.includes('/import')
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                  : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground'
              )}
            >
              <Upload className="h-4 w-4" />
              <span>{t('import')}</span>
            </Link>
          </div>
        )}

        {/* Settings Link */}
        <div className="mt-auto px-2 pb-2">
          <Link
            href="/settings"
            className={cn(
              'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
              'transition-colors duration-150',
              pathname.startsWith('/settings')
                ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/10 hover:text-sidebar-foreground'
            )}
          >
            <Settings className="h-4 w-4" />
            <span>{t('settings')}</span>
          </Link>
        </div>

        {/* Footer */}
        <div className="border-t border-sidebar-border px-4 py-3">
          <Link
            href="/ledgers"
            className="text-xs text-sidebar-foreground/50 transition-colors hover:text-sidebar-foreground"
          >
            {t('switchLedger')}
          </Link>
        </div>
      </aside>
    </>
  )
}
