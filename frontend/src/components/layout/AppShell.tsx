'use client'

import { usePathname } from 'next/navigation'
import { Sidebar } from './Sidebar'
import { MainContent } from './MainContent'
import { ChatPanel } from '@/components/chat/ChatPanel'

interface AppShellProps {
  children: React.ReactNode
}

// Routes that should NOT show the sidebar (exact match only)
const NO_SIDEBAR_ROUTES = ['/setup', '/ledgers']

/**
 * Application shell that conditionally renders sidebar.
 * Shows sidebar for main app pages, hides for setup/ledger selection.
 */
export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname()

  // Check if current route should hide sidebar
  // Only exact matches - /ledgers/[id]/* routes should show sidebar
  const shouldHideSidebar = NO_SIDEBAR_ROUTES.includes(pathname)

  // No sidebar for setup/ledger pages
  if (shouldHideSidebar) {
    return <>{children}</>
  }

  // Full app layout with sidebar
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <MainContent>{children}</MainContent>
      <ChatPanel />
    </div>
  )
}
