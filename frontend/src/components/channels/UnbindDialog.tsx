'use client'

import { useTranslations } from 'next-intl'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useUnbindChannel } from '@/lib/hooks/useChannelBindings'
import type { ChannelBinding } from '@/types'

const CHANNEL_LABELS: Record<string, string> = {
  TELEGRAM: 'Telegram',
  LINE: 'LINE',
  SLACK: 'Slack',
}

interface UnbindDialogProps {
  binding: ChannelBinding | null
  onClose: () => void
}

export function UnbindDialog({ binding, onClose }: UnbindDialogProps) {
  const t = useTranslations('settings.channels')
  const unbind = useUnbindChannel()

  const handleUnbind = async () => {
    if (!binding) return
    await unbind.mutateAsync(binding.id)
    onClose()
  }

  return (
    <Dialog open={!!binding} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('unbindTitle')}</DialogTitle>
          <DialogDescription>{t('unbindDescription')}</DialogDescription>
        </DialogHeader>
        {binding && (
          <p className="text-sm">
            {t('unbindConfirm', {
              channel: CHANNEL_LABELS[binding.channel_type],
              name: binding.display_name || binding.external_user_id,
            })}
          </p>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {t('cancel')}
          </Button>
          <Button variant="destructive" onClick={handleUnbind} disabled={unbind.isPending}>
            {unbind.isPending ? t('unbinding') : t('unbind')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
