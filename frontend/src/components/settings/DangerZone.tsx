'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { AlertTriangle, Trash2, Database, FileX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { apiPost, apiDelete } from '@/lib/api'

interface DangerZoneProps {
  ledgerId: string
}

type ActionType = 'clearTransactions' | 'clearAccounts' | 'deleteLedger' | null

export function DangerZone({ ledgerId }: DangerZoneProps) {
  const t = useTranslations('settings.dangerZone')
  const router = useRouter()
  const [confirmAction, setConfirmAction] = useState<ActionType>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleClearTransactions = async () => {
    setIsProcessing(true)
    try {
      const response = await apiPost<{ deleted_count: number }>(
        `/ledgers/${ledgerId}/clear-transactions`,
        {}
      )
      setResult(t('clearTransactionsSuccess', { count: response.deleted_count }))
      setConfirmAction(null)
      router.refresh()
    } catch (err) {
      console.error('Failed to clear transactions:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleClearAccounts = async () => {
    setIsProcessing(true)
    try {
      const response = await apiPost<{
        transactions_deleted: number
        accounts_deleted: number
      }>(`/ledgers/${ledgerId}/clear-accounts`, {})
      setResult(
        t('clearAccountsSuccess', {
          accounts: response.accounts_deleted,
          transactions: response.transactions_deleted,
        })
      )
      setConfirmAction(null)
      router.refresh()
    } catch (err) {
      console.error('Failed to clear accounts:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDeleteLedger = async () => {
    setIsProcessing(true)
    try {
      await apiDelete(`/ledgers/${ledgerId}`)
      setConfirmAction(null)
      router.push('/ledgers')
    } catch (err) {
      console.error('Failed to delete ledger:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleConfirm = () => {
    switch (confirmAction) {
      case 'clearTransactions':
        handleClearTransactions()
        break
      case 'clearAccounts':
        handleClearAccounts()
        break
      case 'deleteLedger':
        handleDeleteLedger()
        break
    }
  }

  const getConfirmMessage = () => {
    switch (confirmAction) {
      case 'clearTransactions':
        return t('clearTransactionsConfirm')
      case 'clearAccounts':
        return t('clearAccountsConfirm')
      case 'deleteLedger':
        return t('deleteLedgerConfirm')
      default:
        return ''
    }
  }

  const getActionTitle = () => {
    switch (confirmAction) {
      case 'clearTransactions':
        return t('clearTransactions')
      case 'clearAccounts':
        return t('clearAccounts')
      case 'deleteLedger':
        return t('deleteLedger')
      default:
        return ''
    }
  }

  return (
    <>
      <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-6">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <h3 className="text-lg font-semibold text-destructive">{t('title')}</h3>
        </div>
        <p className="text-sm text-muted-foreground mb-6">{t('description')}</p>

        {result && (
          <div className="mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-700 dark:text-green-400 text-sm">
            {result}
          </div>
        )}

        <div className="space-y-4">
          {/* Clear Transactions */}
          <div className="flex items-center justify-between rounded-lg border border-destructive/30 p-4">
            <div className="flex items-start gap-3">
              <FileX className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <h4 className="font-medium">{t('clearTransactions')}</h4>
                <p className="text-sm text-muted-foreground">
                  {t('clearTransactionsDesc')}
                </p>
              </div>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmAction('clearTransactions')}
            >
              {t('clearTransactions')}
            </Button>
          </div>

          {/* Clear Accounts */}
          <div className="flex items-center justify-between rounded-lg border border-destructive/30 p-4">
            <div className="flex items-start gap-3">
              <Database className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <h4 className="font-medium">{t('clearAccounts')}</h4>
                <p className="text-sm text-muted-foreground">
                  {t('clearAccountsDesc')}
                </p>
              </div>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmAction('clearAccounts')}
            >
              {t('clearAccounts')}
            </Button>
          </div>

          {/* Delete Ledger */}
          <div className="flex items-center justify-between rounded-lg border border-destructive/30 p-4">
            <div className="flex items-start gap-3">
              <Trash2 className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <h4 className="font-medium">{t('deleteLedger')}</h4>
                <p className="text-sm text-muted-foreground">
                  {t('deleteLedgerDesc')}
                </p>
              </div>
            </div>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmAction('deleteLedger')}
            >
              {t('deleteLedger')}
            </Button>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={confirmAction !== null} onOpenChange={() => setConfirmAction(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              {getActionTitle()}
            </DialogTitle>
            <DialogDescription>{getConfirmMessage()}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmAction(null)}
              disabled={isProcessing}
            >
              {t('processing') === 'Processing...' ? 'Cancel' : '取消'}
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirm}
              disabled={isProcessing}
            >
              {isProcessing
                ? t('processing')
                : t('processing') === 'Processing...'
                  ? 'Confirm'
                  : '確認'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
