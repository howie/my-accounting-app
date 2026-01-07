'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'

import { useUserStatus } from '@/lib/hooks/useUser'
import { useLedgerContext } from '@/lib/context/LedgerContext'
import { DashboardGrid } from '@/components/dashboard'

export default function Home() {
  const router = useRouter()
  const { data: status, isLoading: statusLoading } = useUserStatus()
  const { currentLedger, isLoading: ledgerLoading } = useLedgerContext()
  const t = useTranslations()

  const isLoading = statusLoading || ledgerLoading

  useEffect(() => {
    if (!isLoading && status) {
      if (status.setup_needed) {
        router.push('/setup')
      } else if (!currentLedger) {
        // No ledger selected, go to ledgers page to select one
        router.push('/ledgers')
      }
      // If ledger is selected, stay on dashboard (this page)
    }
  }, [status, isLoading, router, currentLedger])

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-24">
        <div className="text-center">
          <h1 className="mb-4 text-4xl font-bold">{t('common.appName')}</h1>
          <p className="text-muted-foreground">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  // Show dashboard if ledger is selected
  if (currentLedger) {
    return (
      <div className="p-6 lg:p-8">
        <DashboardGrid />
      </div>
    )
  }

  // Fallback while redirecting
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="mb-4 text-4xl font-bold">{t('common.appName')}</h1>
        <p className="text-muted-foreground">{t('common.loading')}</p>
      </div>
    </div>
  )
}
