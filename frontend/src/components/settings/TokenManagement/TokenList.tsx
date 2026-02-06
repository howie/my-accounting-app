

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Trash2, Copy, Check, Key } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { RevokeTokenDialog } from './RevokeTokenDialog'
import type { ApiToken } from '@/types'

interface TokenListProps {
  tokens: ApiToken[]
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function TokenRow({ token }: { token: ApiToken }) {
  const { t } = useTranslation(undefined, { keyPrefix: 'settings.tokens' })
  const [copied, setCopied] = useState(false)
  const [showRevokeDialog, setShowRevokeDialog] = useState(false)

  const handleCopyPrefix = async () => {
    await navigator.clipboard.writeText(token.token_prefix)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <div className="flex items-center justify-between border-b py-4 last:border-b-0">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
            <Key className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <div className="font-medium">{token.name}</div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                {token.token_prefix}...
              </code>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={handleCopyPrefix}
                title={t('copyPrefix')}
              >
                {copied ? (
                  <Check className="h-3 w-3 text-green-500" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </Button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right text-sm">
            <div className="text-muted-foreground">{t('created')}</div>
            <div>{formatDate(token.created_at)}</div>
          </div>
          <div className="text-right text-sm">
            <div className="text-muted-foreground">{t('lastUsed')}</div>
            <div>{token.last_used_at ? formatDate(token.last_used_at) : t('never')}</div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="text-destructive hover:bg-destructive/10 hover:text-destructive"
            onClick={() => setShowRevokeDialog(true)}
            title={t('revoke')}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <RevokeTokenDialog
        token={token}
        isOpen={showRevokeDialog}
        onClose={() => setShowRevokeDialog(false)}
      />
    </>
  )
}

export function TokenList({ tokens }: TokenListProps) {
  const { t } = useTranslation(undefined, { keyPrefix: 'settings.tokens' })

  if (tokens.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center">
        <Key className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <h3 className="mt-4 font-medium">{t('noTokens')}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{t('noTokensDescription')}</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border">
      <div className="divide-y">
        {tokens.map((token) => (
          <TokenRow key={token.id} token={token} />
        ))}
      </div>
    </div>
  )
}
