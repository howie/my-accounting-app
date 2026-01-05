'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useTranslations } from 'next-intl'

import { useUserStatus } from '@/lib/hooks/useUser'

export default function Home() {
  const router = useRouter()
  const { data: status, isLoading } = useUserStatus()
  const t = useTranslations()

  useEffect(() => {
    if (!isLoading && status) {
      if (status.setup_needed) {
        router.push('/setup')
      } else {
        router.push('/ledgers')
      }
    }
  }, [status, isLoading, router])

  if (isLoading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24">
        <div className="text-center">
          <h1 className="mb-4 text-4xl font-bold">{t('common.appName')}</h1>
          <p className="text-muted-foreground">{t('common.loading')}</p>
        </div>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="mb-4 text-4xl font-bold">{t('common.appName')}</h1>
        <p className="mb-8 text-lg text-muted-foreground">{t('home.title')}</p>
        <div className="flex gap-4">
          <Link
            href="/ledgers"
            className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
          >
            {t('home.getStarted')}
          </Link>
        </div>
      </div>
    </main>
  )
}
