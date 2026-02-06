

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Copy, Check, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useCreateToken } from '@/lib/hooks/useTokens'
import type { ApiTokenCreateResponse } from '@/types'

interface CreateTokenDialogProps {
  isOpen: boolean
  onClose: () => void
}

export function CreateTokenDialog({ isOpen, onClose }: CreateTokenDialogProps) {
  const { t } = useTranslation(undefined, { keyPrefix: 'settings.tokens' })
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [createdToken, setCreatedToken] = useState<ApiTokenCreateResponse | null>(null)
  const [copied, setCopied] = useState(false)

  const createToken = useCreateToken()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError(t('nameRequired'))
      return
    }

    try {
      const token = await createToken.mutateAsync({ name: name.trim() })
      setCreatedToken(token)
    } catch (err) {
      setError(t('createError'))
      console.error(err)
    }
  }

  const handleCopyToken = async () => {
    if (!createdToken) return
    await navigator.clipboard.writeText(createdToken.token)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleClose = () => {
    setName('')
    setError(null)
    setCreatedToken(null)
    setCopied(false)
    onClose()
  }

  // Show success state after token creation
  if (createdToken) {
    return (
      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('tokenCreated')}</DialogTitle>
            <DialogDescription>{t('tokenCreatedDescription')}</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600 dark:text-amber-500" />
                <div className="text-sm text-amber-800 dark:text-amber-200">
                  {t('tokenWarning')}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">{t('yourToken')}</label>
              <div className="flex gap-2">
                <code className="flex-1 rounded-md border bg-muted p-3 font-mono text-sm break-all">
                  {createdToken.token}
                </code>
                <Button variant="outline" size="icon" onClick={handleCopyToken}>
                  {copied ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button onClick={handleClose}>{t('done')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  // Show create form
  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('createTitle')}</DialogTitle>
          <DialogDescription>{t('createDescription')}</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="token-name" className="text-sm font-medium">
              {t('tokenName')}
            </label>
            <Input
              id="token-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('tokenNamePlaceholder')}
              autoFocus
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              {t('cancel')}
            </Button>
            <Button type="submit" disabled={createToken.isPending || !name.trim()}>
              {createToken.isPending ? t('creating') : t('create')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
