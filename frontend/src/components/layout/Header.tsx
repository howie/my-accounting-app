'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Home } from 'lucide-react'
import { ThemeToggle } from '@/components/settings/ThemeToggle'
import { LanguageSelector } from '@/components/settings/LanguageSelector'
import { useLedgerContext } from '@/lib/context/LedgerContext'

export function Header() {
  const pathname = usePathname()
  const { currentLedger } = useLedgerContext()

  // Generate breadcrumbs
  const pathSegments = pathname.split('/').filter((segment) => segment !== '')
  const breadcrumbs = pathSegments.map((segment, index) => {
    const href = `/${pathSegments.slice(0, index + 1).join('/')}`
    const isLast = index === pathSegments.length - 1

    // Simple mapping for common paths (can be improved with i18n)
    let label = segment
    if (segment === 'settings') label = 'Settings'
    if (segment === 'ledgers') label = 'Ledgers'

    return { href, label, isLast }
  })

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b bg-background px-6 transition-all">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
         <Link href="/" className="flex items-center hover:text-foreground">
            <Home className="h-4 w-4" />
         </Link>
         {breadcrumbs.length > 0 && <ChevronRight className="h-4 w-4 text-muted-foreground/50" />}

         {breadcrumbs.map((crumb) => (
           <div key={crumb.href} className="flex items-center gap-1">
             {crumb.isLast ? (
               <span className="font-medium text-foreground">{crumb.label}</span>
             ) : (
               <Link href={crumb.href} className="hover:text-foreground">
                 {crumb.label}
               </Link>
             )}
             {!crumb.isLast && <ChevronRight className="h-4 w-4 text-muted-foreground/50" />}
           </div>
         ))}
      </div>

      <div className="flex items-center gap-4">
        {/* Ledger Selector / Info */}
        {currentLedger && (
            <div className="hidden items-center gap-2 text-sm font-medium md:flex">
                <span className="text-muted-foreground">Ledger:</span>
                <Link
                    href="/ledgers"
                    className="flex items-center gap-1 rounded-md px-2 py-1 transition-colors hover:bg-muted"
                    title="Switch Ledger"
                >
                    <span>{currentLedger.name}</span>
                </Link>
            </div>
        )}

        <div className="flex items-center gap-2">
            <ThemeToggle />
            <LanguageSelector />
        </div>
      </div>
    </header>
  )
}
