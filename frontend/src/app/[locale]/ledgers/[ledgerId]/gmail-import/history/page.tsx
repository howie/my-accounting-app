'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import ScanHistoryTable from '@/components/gmail-import/ScanHistoryTable'
import { gmailImportApi, ScanJobResponse } from '@/lib/api/gmail-import'

const PAGE_SIZE = 20

export default function ScanHistoryPage() {
  const params = useParams()
  const router = useRouter()
  const t = useTranslations('gmailImport')
  const ledgerId = (params?.ledgerId ?? '') as string

  const [jobs, setJobs] = useState<ScanJobResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)

  const fetchHistory = useCallback(
    async (currentOffset: number) => {
      try {
        setLoading(true)
        const response = await gmailImportApi.getScanHistory(ledgerId, PAGE_SIZE, currentOffset)
        setJobs(response.items)
        setTotal(response.total)
      } catch {
        // Non-critical error
      } finally {
        setLoading(false)
      }
    },
    [ledgerId]
  )

  useEffect(() => {
    fetchHistory(offset)
  }, [fetchHistory, offset])

  const handleViewStatements = (jobId: string) => {
    // Navigate to main import page - in future could pass jobId to auto-load statements
    router.push(`/${params?.locale}/ledgers/${ledgerId}/gmail-import?scan=${jobId}`)
  }

  const hasMore = offset + PAGE_SIZE < total
  const hasPrev = offset > 0

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Breadcrumb & Header */}
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-2 text-sm text-gray-500">
          <Link href={`/ledgers/${ledgerId}`} className="hover:text-gray-700">
            {t('ledger')}
          </Link>
          <span>/</span>
          <Link
            href={`/${params?.locale}/ledgers/${ledgerId}/gmail-import`}
            className="hover:text-gray-700"
          >
            {t('gmailImport')}
          </Link>
          <span>/</span>
          <span>{t('history.title')}</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">{t('history.title')}</h1>
        <p className="text-gray-500">{t('history.subtitle')}</p>
      </div>

      {/* History table */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
        {loading ? (
          <div className="animate-pulse space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 rounded bg-gray-200" />
            ))}
          </div>
        ) : (
          <>
            <ScanHistoryTable jobs={jobs} onViewStatements={handleViewStatements} />

            {/* Pagination */}
            {total > PAGE_SIZE && (
              <div className="mt-4 flex items-center justify-between border-t border-gray-200 pt-4">
                <span className="text-sm text-gray-500">
                  {t('history.showing', {
                    from: offset + 1,
                    to: Math.min(offset + PAGE_SIZE, total),
                    total,
                  })}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                    disabled={!hasPrev}
                    className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    {t('history.previous')}
                  </button>
                  <button
                    onClick={() => setOffset(offset + PAGE_SIZE)}
                    disabled={!hasMore}
                    className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    {t('history.next')}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
