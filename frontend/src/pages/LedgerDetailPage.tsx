import { Link, useParams, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'

import { useLedger } from '@/lib/hooks/useLedgers'
import { useLedgerContext } from '@/lib/context/LedgerContext'

/**
 * Ledger Detail Page - Redirects to Dashboard after setting ledger context.
 *
 * This page serves as an intermediate redirect. When a user navigates to
 * /ledgers/[id], it loads the ledger, sets it as the current ledger in
 * context, and redirects to the Dashboard.
 */
export default function LedgerDetailPage() {
  const params = useParams()
  const navigate = useNavigate()
  const ledgerId = (params?.id ?? '') as string
  const { t } = useTranslation()

  const { data: ledger, isLoading, error } = useLedger(ledgerId)
  const { setCurrentLedger } = useLedgerContext()

  // Set current ledger in context and redirect to dashboard
  useEffect(() => {
    if (ledger) {
      setCurrentLedger(ledger)
      navigate('/', { replace: true })
    }
  }, [ledger, setCurrentLedger, navigate])

  // Error state
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="mb-4 text-destructive">
            {t('common.error')}: {error.message}
          </p>
          <Link to="/ledgers" className="text-primary hover:underline">
            {t('ledgers.backToLedgers')}
          </Link>
        </div>
      </div>
    )
  }

  // Loading state (also shown while redirecting)
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="mb-4 text-2xl font-bold">{t('common.appName')}</h1>
        <p className="text-muted-foreground">
          {isLoading ? t('common.loading') : 'Redirecting to dashboard...'}
        </p>
      </div>
    </div>
  )
}
