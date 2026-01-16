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
        'flex-1 bg-background',
        className
      )}
    >
      {children}
    </main>
  )
}
