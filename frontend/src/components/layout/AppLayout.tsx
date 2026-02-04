

import { Sidebar } from './Sidebar'
import { MainContent } from './MainContent'

interface AppLayoutProps {
  children: React.ReactNode
}

/**
 * Main application layout with sidebar and content area.
 * Used for authenticated pages that show the sidebar.
 */
export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <MainContent>{children}</MainContent>
    </div>
  )
}
