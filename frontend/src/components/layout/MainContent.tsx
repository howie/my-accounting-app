'use client'

import { cn } from '@/lib/utils'

interface MainContentProps {
  children: React.ReactNode
  className?: string
}

/**
 * Main content wrapper that adjusts for sidebar.
 * Provides proper margin/padding on different screen sizes.
 */
export function MainContent({ children, className }: MainContentProps) {
  return (
    <main
      className={cn(
        'min-h-screen flex-1',
        'bg-background',
        // On mobile, add top padding for hamburger menu
        'pt-16 lg:pt-0',
        className
      )}
    >
      {children}
    </main>
  )
}
