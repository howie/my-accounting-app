'use client'

import { useVersion } from '@/lib/hooks/useVersion'

export function Footer() {
  const { data: version } = useVersion()

  return (
    <footer className="fixed bottom-0 right-0 p-2 text-xs text-muted-foreground">
      {version && <span>v{version}</span>}
    </footer>
  )
}
