'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ChannelBindingList } from '@/components/channels/ChannelBindingList'
import { BindingCodeDialog } from '@/components/channels/BindingCodeDialog'
import { UnbindDialog } from '@/components/channels/UnbindDialog'
import { useChannelBindings } from '@/lib/hooks/useChannelBindings'
import type { ChannelBinding } from '@/types'

export default function ChannelsPage() {
  const t = useTranslations('settings.channels')
  const { data: bindings, isLoading, error } = useChannelBindings()
  const [showCodeDialog, setShowCodeDialog] = useState(false)
  const [unbindTarget, setUnbindTarget] = useState<ChannelBinding | null>(null)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('title')}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t('description')}</p>
        </div>
        <Button onClick={() => setShowCodeDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t('addBinding')}
        </Button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-muted-foreground">{t('loading')}</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 text-destructive">
          {t('loadError')}
        </div>
      )}

      {bindings && <ChannelBindingList bindings={bindings} onUnbind={setUnbindTarget} />}

      <BindingCodeDialog isOpen={showCodeDialog} onClose={() => setShowCodeDialog(false)} />
      <UnbindDialog binding={unbindTarget} onClose={() => setUnbindTarget(null)} />
    </div>
  )
}
