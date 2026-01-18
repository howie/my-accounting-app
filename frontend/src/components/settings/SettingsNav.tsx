'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { Users, Settings, Key, Tag, Repeat, Calculator } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  labelKey: string
  icon: React.ElementType
  exact?: boolean
}

const navItems: NavItem[] = [
  { href: '/settings', labelKey: 'preferences', icon: Settings, exact: true },
  { href: '/settings/accounts', labelKey: 'accounts', icon: Users },
  { href: '/settings/tags', labelKey: 'tags', icon: Tag },
  { href: '/settings/recurring', labelKey: 'recurring', icon: Repeat },
  { href: '/settings/installments', labelKey: 'installments', icon: Calculator },
  { href: '/settings/tokens', labelKey: 'apiTokens', icon: Key },
]

/**
 * Side navigation for Settings pages.
 * Displays links to Account Management and other settings sections.
 */
export function SettingsNav() {
  const pathname = usePathname()
  const t = useTranslations('settings')

  return (
    <nav className="w-48 flex-shrink-0">
      <ul className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = item.exact
            ? pathname === item.href
            : (pathname ?? '').startsWith(item.href)
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{t(item.labelKey)}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
