'use client'

import { useTranslation } from 'react-i18next'
import { MessageSquare, Unlink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { ChannelBinding, ChannelType } from '@/types'

const CHANNEL_LABELS: Record<ChannelType, string> = {
  TELEGRAM: 'Telegram',
  LINE: 'LINE',
  SLACK: 'Slack',
}

interface ChannelBindingListProps {
  bindings: ChannelBinding[]
  onUnbind: (binding: ChannelBinding) => void
}

export function ChannelBindingList({ bindings, onUnbind }: ChannelBindingListProps) {
  const { t } = useTranslation(undefined, { keyPrefix: 'settings.channels' })

  if (bindings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-12">
        <MessageSquare className="mb-3 h-10 w-10 text-muted-foreground" />
        <p className="text-sm font-medium">{t('noBindings')}</p>
        <p className="mt-1 text-xs text-muted-foreground">{t('noBindingsDescription')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {bindings.map((binding) => (
        <div key={binding.id} className="flex items-center justify-between rounded-lg border p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
              {CHANNEL_LABELS[binding.channel_type].charAt(0)}
            </div>
            <div>
              <div className="text-sm font-medium">{CHANNEL_LABELS[binding.channel_type]}</div>
              <div className="text-xs text-muted-foreground">
                {binding.display_name || binding.external_user_id}
              </div>
              {binding.last_used_at && (
                <div className="mt-0.5 text-xs text-muted-foreground">
                  {t('lastUsed')}: {new Date(binding.last_used_at).toLocaleDateString()}
                </div>
              )}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onUnbind(binding)}>
            <Unlink className="mr-1 h-3 w-3" />
            {t('unbind')}
          </Button>
        </div>
      ))}
    </div>
  )
}
