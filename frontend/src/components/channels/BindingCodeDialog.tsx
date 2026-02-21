'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useGenerateCode } from '@/lib/hooks/useChannelBindings'
import type { ChannelType } from '@/types'

const CHANNEL_OPTIONS: { value: ChannelType; label: string }[] = [
  { value: 'TELEGRAM', label: 'Telegram' },
  { value: 'LINE', label: 'LINE' },
  { value: 'SLACK', label: 'Slack' },
]

interface BindingCodeDialogProps {
  isOpen: boolean
  onClose: () => void
}

export function BindingCodeDialog({ isOpen, onClose }: BindingCodeDialogProps) {
  const { t } = useTranslation(undefined, { keyPrefix: 'settings.channels' })
  const generateCode = useGenerateCode()
  const [selectedChannel, setSelectedChannel] = useState<ChannelType>('TELEGRAM')
  const [code, setCode] = useState<string | null>(null)
  const [countdown, setCountdown] = useState(0)

  const handleGenerate = useCallback(async () => {
    const result = await generateCode.mutateAsync({ channel_type: selectedChannel })
    setCode(result.code)
    setCountdown(result.expires_in_seconds)
  }, [generateCode, selectedChannel])

  useEffect(() => {
    if (countdown <= 0) return
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [countdown])

  const handleClose = useCallback(() => {
    setCode(null)
    setCountdown(0)
    generateCode.reset()
    onClose()
  }, [generateCode, onClose])

  const minutes = Math.floor(countdown / 60)
  const seconds = countdown % 60

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('generateTitle')}</DialogTitle>
          <DialogDescription>{t('generateDescription')}</DialogDescription>
        </DialogHeader>

        {!code ? (
          <div className="space-y-4">
            <div className="flex gap-2">
              {CHANNEL_OPTIONS.map((ch) => (
                <Button
                  key={ch.value}
                  variant={selectedChannel === ch.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedChannel(ch.value)}
                >
                  {ch.label}
                </Button>
              ))}
            </div>
            <Button onClick={handleGenerate} disabled={generateCode.isPending} className="w-full">
              {generateCode.isPending ? t('generating') : t('generate')}
            </Button>
          </div>
        ) : (
          <div className="space-y-4 text-center">
            <div className="font-mono text-4xl font-bold tracking-[0.5em]">{code}</div>
            {countdown > 0 ? (
              <p className="text-sm text-muted-foreground">
                {t('expiresIn', { minutes, seconds: seconds.toString().padStart(2, '0') })}
              </p>
            ) : (
              <p className="text-sm text-destructive">{t('expired')}</p>
            )}
            <p className="text-xs text-muted-foreground">{t('codeInstruction')}</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
