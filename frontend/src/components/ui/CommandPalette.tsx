'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { Search, Home, Settings, FileText, CreditCard, Wallet, TrendingUp, Receipt } from 'lucide-react'
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useSidebarAccounts } from '@/lib/hooks/useSidebarAccounts'
import { cn } from '@/lib/utils'
import type { AccountType, SidebarCategory, SidebarAccountItem } from '@/types/dashboard'

export function CommandPalette() {
  const [open, setOpen] = React.useState(false)
  const [query, setQuery] = React.useState('')
  const [selectedIndex, setSelectedIndex] = React.useState(0)
  const router = useRouter()
  const { data: categories } = useSidebarAccounts()

  // Flatten accounts for search
  const accounts = React.useMemo(() => {
    if (!categories) return []
    const accs: { id: string; name: string; type: AccountType }[] = []

    const traverse = (items: SidebarAccountItem[]) => {
        items.forEach(item => {
            accs.push({ id: item.id, name: item.name, type: item.type })
            if (item.children) traverse(item.children)
        })
    }

    categories.forEach(cat => traverse(cat.accounts))
    return accs
  }, [categories])

  // Filter items
  const filteredItems = React.useMemo(() => {
    if (!query) return [
        { type: 'nav', label: 'Dashboard', href: '/', icon: Home, meta: undefined },
        { type: 'nav', label: 'Settings', href: '/settings', icon: Settings, meta: undefined },
        { type: 'nav', label: 'Ledgers', href: '/ledgers', icon: FileText, meta: undefined },
    ]

    const q = query.toLowerCase()
    const navs = [
        { type: 'nav', label: 'Dashboard', href: '/', icon: Home, meta: undefined },
        { type: 'nav', label: 'Settings', href: '/settings', icon: Settings, meta: undefined },
        { type: 'nav', label: 'Ledgers', href: '/ledgers', icon: FileText, meta: undefined },
    ].filter(item => item.label.toLowerCase().includes(q))

    const accountItems = accounts
        .filter(acc => acc.name.toLowerCase().includes(q))
        .map(acc => ({
            type: 'account',
            label: acc.name,
            href: `/accounts/${acc.id}`,
            icon: getIconForType(acc.type),
            meta: acc.type as string | undefined
        }))

    return [...navs, ...accountItems].slice(0, 10)
  }, [query, accounts])

  // Keyboard listeners
  React.useEffect(() => {
    let lastKey = ''
    let timeout: NodeJS.Timeout

    const down = (e: KeyboardEvent) => {
      // Toggle Command Palette
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
        return
      }

      // Ignore other shortcuts if input focused (except Escape)
      if (
        (document.activeElement?.tagName === 'INPUT' ||
         document.activeElement?.tagName === 'TEXTAREA') &&
        !open
      ) {
        return
      }

      // Navigation Shortcuts (g+d, g+s)
      if (!open) {
          if (e.key === 'g') {
              lastKey = 'g'
              clearTimeout(timeout)
              timeout = setTimeout(() => { lastKey = '' }, 1000)
              return
          }
          if (lastKey === 'g') {
              if (e.key === 'd') {
                  router.push('/')
                  lastKey = ''
              } else if (e.key === 's') {
                  router.push('/settings')
                  lastKey = ''
              }
          }
      }
    }

    document.addEventListener('keydown', down)
    return () => {
        document.removeEventListener('keydown', down)
        clearTimeout(timeout)
    }
  }, [open, router])

  const runCommand = React.useCallback((command: () => void) => {
    setOpen(false)
    command()
  }, [])

  const handleSelect = (index: number) => {
      const item = filteredItems[index]
      if (item) {
          runCommand(() => router.push(item.href))
      }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="p-0 overflow-hidden max-w-2xl gap-0">
        <DialogTitle className="sr-only">Command Palette</DialogTitle>
        <div className="flex items-center border-b px-3" cmdk-input-wrapper="">
          <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
          <Input
            className="flex h-12 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50 border-none focus-visible:ring-0"
            placeholder="Type a command or search..."
            value={query}
            onChange={(e) => {
                setQuery(e.target.value)
                setSelectedIndex(0)
            }}
            onKeyDown={(e) => {
                if (e.key === 'ArrowDown') {
                    e.preventDefault()
                    setSelectedIndex(prev => Math.min(prev + 1, filteredItems.length - 1))
                }
                if (e.key === 'ArrowUp') {
                    e.preventDefault()
                    setSelectedIndex(prev => Math.max(prev - 1, 0))
                }
                if (e.key === 'Enter') {
                    e.preventDefault()
                    handleSelect(selectedIndex)
                }
            }}
          />
        </div>
        <div className="max-h-[300px] overflow-y-auto p-2">
            {filteredItems.length === 0 && (
                 <p className="p-4 text-center text-sm text-muted-foreground">No results found.</p>
            )}
            {filteredItems.map((item, index) => (
                <button
                    key={item.href + item.label}
                    className={cn(
                        "relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none",
                        index === selectedIndex ? "bg-accent text-accent-foreground" : "text-foreground hover:bg-accent/50"
                    )}
                    onClick={() => handleSelect(index)}
                    onMouseEnter={() => setSelectedIndex(index)}
                >
                    <item.icon className="mr-2 h-4 w-4" />
                    <span>{item.label}</span>
                    {item.meta && (
                        <span className="ml-auto text-xs text-muted-foreground capitalize">{item.meta.toLowerCase()}</span>
                    )}
                </button>
            ))}
        </div>
        <div className="border-t px-4 py-2 text-xs text-muted-foreground flex justify-between">
            <span>Pro tip: <b>g</b> then <b>d</b> for Dashboard, <b>g</b> then <b>s</b> for Settings</span>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function getIconForType(type: AccountType) {
    switch (type) {
        case 'ASSET': return Wallet
        case 'LIABILITY': return CreditCard
        case 'INCOME': return TrendingUp
        case 'EXPENSE': return Receipt
        default: return FileText
    }
}
