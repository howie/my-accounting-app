'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

import { useUserStatus } from '@/lib/hooks/useUser'

export default function Home() {
  const router = useRouter()
  const { data: status, isLoading } = useUserStatus()

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
          <h1 className="mb-4 text-4xl font-bold">LedgerOne</h1>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </main>
    )
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="mb-4 text-4xl font-bold">LedgerOne</h1>
        <p className="mb-8 text-lg text-muted-foreground">Personal Accounting System</p>
        <div className="flex gap-4">
          <Link
            href="/ledgers"
            className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
          >
            Get Started
          </Link>
        </div>
      </div>
    </main>
  )
}
