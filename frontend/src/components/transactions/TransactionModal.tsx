import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { X, Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { TransactionForm } from '@/components/transactions/TransactionForm'
import type { AccountType, Transaction } from '@/types'

export interface TransactionModalProps {
  ledgerId: string
  /** Pre-selected account ID */
  preSelectedAccountId?: string
  /** Pre-selected account type */
  preSelectedAccountType?: AccountType
  /** Called when a transaction is created/updated successfully */
  onTransactionCreated?: () => void
  /** Custom trigger element - if not provided, default button is rendered */
  trigger?: React.ReactNode
  /** Custom trigger button text */
  triggerText?: string
  /** Variant for the default trigger button */
  triggerVariant?: 'default' | 'outline' | 'ghost'
  /** Transaction data for edit mode */
  editTransaction?: Transaction
  /** Whether the modal is controlled externally */
  open?: boolean
  /** Called when modal open state changes (for controlled mode) */
  onOpenChange?: (open: boolean) => void
}

/**
 * TransactionModal - A modal dialog for creating or editing transactions
 *
 * Features:
 * - Opens on trigger click (uncontrolled) or via open prop (controlled)
 * - Closes on save, cancel, or overlay click
 * - Supports account pre-selection
 * - Supports edit mode with editTransaction prop
 * - Triggers callback on successful transaction creation/update
 */
export function TransactionModal({
  ledgerId,
  preSelectedAccountId,
  preSelectedAccountType,
  onTransactionCreated,
  trigger,
  triggerText,
  triggerVariant = 'default',
  editTransaction,
  open,
  onOpenChange,
}: TransactionModalProps) {
  const { t } = useTranslation()
  const [internalOpen, setInternalOpen] = useState(false)

  const isControlled = open !== undefined
  const isOpen = isControlled ? open : internalOpen

  const setOpen = useCallback(
    (value: boolean) => {
      if (isControlled) {
        onOpenChange?.(value)
      } else {
        setInternalOpen(value)
      }
    },
    [isControlled, onOpenChange]
  )

  const handleOpen = useCallback(() => {
    setOpen(true)
  }, [setOpen])

  const handleClose = useCallback(() => {
    setOpen(false)
  }, [setOpen])

  const handleSuccess = useCallback(() => {
    setOpen(false)
    onTransactionCreated?.()
  }, [setOpen, onTransactionCreated])

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        setOpen(false)
      }
    },
    [setOpen]
  )

  const isEditMode = !!editTransaction
  const modalTitle = isEditMode
    ? t('transactionEntry.editTransaction')
    : t('transactionModal.title')
  const defaultTriggerText = triggerText || t('transactionModal.trigger')

  return (
    <>
      {/* Trigger - only render if not controlled */}
      {!isControlled && (
        <>
          {trigger ? (
            <div onClick={handleOpen}>{trigger}</div>
          ) : (
            <Button
              type="button"
              variant={triggerVariant}
              onClick={handleOpen}
              data-testid="add-transaction-trigger"
            >
              <Plus className="mr-2 h-4 w-4" />
              {defaultTriggerText}
            </Button>
          )}
        </>
      )}

      {/* Modal */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="transaction-modal-title"
        >
          {/* Backdrop / Overlay */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleOverlayClick}
            aria-hidden="true"
            data-testid="modal-overlay"
          />

          {/* Dialog */}
          <div className="relative z-10 w-full max-w-lg rounded-lg border bg-background shadow-lg">
            {/* Header */}
            <div className="flex items-center justify-between border-b px-6 py-4">
              <h2 id="transaction-modal-title" className="text-lg font-semibold">
                {modalTitle}
              </h2>
              <button
                type="button"
                onClick={handleClose}
                className="text-muted-foreground transition-colors hover:text-foreground"
                aria-label={t('common.cancel')}
                data-testid="modal-close-button"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Form Content */}
            <div className="max-h-[70vh] overflow-y-auto p-6">
              <TransactionForm
                ledgerId={ledgerId}
                preSelectedAccountId={preSelectedAccountId}
                preSelectedAccountType={preSelectedAccountType}
                editTransaction={editTransaction}
                onSuccess={handleSuccess}
                onCancel={handleClose}
              />
            </div>
          </div>
        </div>
      )}
    </>
  )
}
