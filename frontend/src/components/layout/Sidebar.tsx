'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Menu, X, BookOpen, Settings } from 'lucide-react'
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
    return (
      <aside className="hidden lg:flex lg:w-64 lg:flex-col bg-sidebar" />
    )
  }

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={toggleCollapsed}
        className={cn(
          'fixed top-4 left-4 z-50 p-2 rounded-md lg:hidden',
          'bg-sidebar text-sidebar-foreground',
          'hover:bg-sidebar-accent/20 transition-colors'
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
        <div className="flex h-16 items-center gap-2 px-4 border-b border-sidebar-border">
          <BookOpen className="h-6 w-6 text-sidebar-accent" />
          <span className="text-lg font-semibold text-sidebar-foreground">
            LedgerOne
          </span>
        </div>

        {/* Current Ledger */}
        {currentLedger && (
          <div className="px-4 py-3 border-b border-sidebar-border">
            <p className="text-xs text-sidebar-foreground/50 uppercase tracking-wider">
              Current Ledger
            </p>
            <p className="text-sm font-medium text-sidebar-foreground truncate">
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
              'flex items-center gap-2 px-3 py-2 mb-4 text-sm font-medium rounded-md',
              'transition-colors duration-150',
              pathname === '/'
                ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                : 'text-sidebar-foreground/80 hover:text-sidebar-foreground hover:bg-sidebar-accent/10'
            )}
          >
            <Home className="h-4 w-4" />
            <span>Dashboard</span>
          </Link>

          {/* Category Divider */}
          <div className="px-3 mb-2">
            <p className="text-xs text-sidebar-foreground/50 uppercase tracking-wider">
              Accounts
            </p>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="px-3 py-4 space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="h-8 bg-sidebar-accent/20 rounded-md" />
                </div>
              ))}
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="px-3 py-4 text-sm text-red-400">
              Failed to load accounts
            </div>
          )}

          {/* Categories */}
          {categories && categories.map((category) => (
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
              Select a ledger to view accounts
            </div>
          )}
        </nav>

        {/* Settings Link */}
        <div className="px-2 mt-auto pb-2">
          <Link
            href="/settings"
            className={cn(
              'flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md',
              'transition-colors duration-150',
              pathname.startsWith('/settings')
                ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                : 'text-sidebar-foreground/80 hover:text-sidebar-foreground hover:bg-sidebar-accent/10'
            )}
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </Link>
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-sidebar-border">
          <Link
            href="/ledgers"
            className="text-xs text-sidebar-foreground/50 hover:text-sidebar-foreground transition-colors"
          >
            Switch Ledger
          </Link>
        </div>
      </aside>
    </>
  )
}
