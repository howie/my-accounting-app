'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { TokenList, CreateTokenDialog } from '@/components/settings/TokenManagement'
import { useTokens } from '@/lib/hooks/useTokens'

export default function TokensPage() {
  const t = useTranslations('settings.tokens')
  const { data: tokens, isLoading, error } = useTokens()
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{t('title')}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t('description')}</p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          {t('create')}
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

      {tokens && <TokenList tokens={tokens} />}

      <CreateTokenDialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
      />
    </div>
  )
}
