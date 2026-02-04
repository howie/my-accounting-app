

import { useTranslation } from 'react-i18next'
import { AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useRevokeToken } from '@/lib/hooks/useTokens'
import type { ApiToken } from '@/types'

interface RevokeTokenDialogProps {
  token: ApiToken
  isOpen: boolean
  onClose: () => void
}

export function RevokeTokenDialog({ token, isOpen, onClose }: RevokeTokenDialogProps) {
  const { t } = useTranslation(undefined, { keyPrefix: 'settings.tokens' })
  const revokeToken = useRevokeToken()

  const handleRevoke = async () => {
    try {
      await revokeToken.mutateAsync(token.id)
      onClose()
    } catch (err) {
      console.error('Failed to revoke token:', err)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('revokeTitle')}</DialogTitle>
          <DialogDescription>{t('revokeDescription')}</DialogDescription>
        </DialogHeader>

        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-destructive" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-destructive">{t('revokeWarning')}</p>
              <p className="text-sm text-muted-foreground">
                {t('revokeTokenName', { name: token.name })}
              </p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            {t('cancel')}
          </Button>
          <Button
            variant="destructive"
            onClick={handleRevoke}
            disabled={revokeToken.isPending}
          >
            {revokeToken.isPending ? t('revoking') : t('revoke')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
