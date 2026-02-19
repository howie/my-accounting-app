'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
import ScanProgressIndicator from '@/components/gmail-import/ScanProgressIndicator'
import StatementList from '@/components/gmail-import/StatementList'
import StatementPreview from '@/components/gmail-import/StatementPreview'
import {
  gmailImportApi,
  GmailConnectionResponse,
  GmailConnectionStatus,
  DiscoveredStatementResponse,
  ScanJobResponse,
  ScanJobStatus,
} from '@/lib/api/gmail-import'

export default function GmailImportPage() {
  const params = useParams()
  const t = useTranslations('gmailImport')
  const ledgerId = (params?.ledgerId ?? '') as string

  // Connection state
  const [connection, setConnection] = useState<GmailConnectionResponse | null>(null)
  const [connectionLoading, setConnectionLoading] = useState(true)

  // Scan state
  const [scanJob, setScanJob] = useState<ScanJobResponse | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)

  // Statements state
  const [statements, setStatements] = useState<DiscoveredStatementResponse[]>([])
  const [selectedStatementId, setSelectedStatementId] = useState<string | null>(null)

  // Import state
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<{
    success: boolean
    message: string
    count?: number
  } | null>(null)

  const selectedStatement = statements.find((s) => s.id === selectedStatementId) ?? null

  const fetchConnection = useCallback(async () => {
    try {
      setConnectionLoading(true)
      const response = await gmailImportApi.getConnection()
      setConnection(response)
    } catch {
      setConnection(null)
    } finally {
      setConnectionLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchConnection()
  }, [fetchConnection])

  const handleTriggerScan = async () => {
    if (!ledgerId) return

    setIsScanning(true)
    setScanError(null)
    setStatements([])
    setSelectedStatementId(null)

    try {
      const job = await gmailImportApi.triggerScan(ledgerId)
      setScanJob(job)

      // Poll for completion if scanning
      if (job.status === ScanJobStatus.SCANNING || job.status === ScanJobStatus.PENDING) {
        pollScanStatus(job.id)
      } else {
        setIsScanning(false)
        if (job.status === ScanJobStatus.COMPLETED) {
          fetchStatements(job.id)
        }
      }
    } catch (err) {
      setScanError(err instanceof Error ? err.message : t('errors.scanFailed'))
      setIsScanning(false)
    }
  }

  const pollScanStatus = async (jobId: string) => {
    const maxAttempts = 60
    let attempts = 0

    const poll = async () => {
      if (attempts >= maxAttempts) {
        setIsScanning(false)
        setScanError(t('errors.scanTimeout'))
        return
      }

      try {
        const job = await gmailImportApi.getScanStatus(jobId)
        setScanJob(job)

        if (job.status === ScanJobStatus.COMPLETED) {
          setIsScanning(false)
          fetchStatements(jobId)
        } else if (job.status === ScanJobStatus.FAILED) {
          setIsScanning(false)
        } else {
          attempts++
          setTimeout(poll, 2000)
        }
      } catch {
        attempts++
        setTimeout(poll, 3000)
      }
    }

    poll()
  }

  const fetchStatements = async (scanJobId: string) => {
    try {
      const response = await gmailImportApi.getStatements(scanJobId)
      setStatements(response.statements)
    } catch {
      // Statements fetch failure is non-critical
    }
  }

  const handleImport = async (statementId: string) => {
    setImporting(true)
    setImportResult(null)
    try {
      const result = await gmailImportApi.importStatement(ledgerId, statementId, {
        statement_id: statementId,
      })
      // Refresh statements to show updated import status
      if (scanJob) {
        fetchStatements(scanJob.id)
      }
      setSelectedStatementId(null)
      setImportResult({
        success: true,
        message: t('import.success'),
        count: result.imported_count,
      })
    } catch (err) {
      setImportResult({
        success: false,
        message: err instanceof Error ? err.message : t('import.failed'),
      })
    } finally {
      setImporting(false)
    }
  }

  const isConnected = connection?.status === GmailConnectionStatus.CONNECTED

  if (connectionLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-1/3 rounded bg-gray-200"></div>
          <div className="h-4 w-2/3 rounded bg-gray-200"></div>
          <div className="h-32 rounded bg-gray-200"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {/* Breadcrumb & Header */}
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-2 text-sm text-gray-500">
          <Link href={`/ledgers/${ledgerId}`} className="hover:text-gray-700">
            {t('ledger')}
          </Link>
          <span>/</span>
          <span>{t('gmailImport')}</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('pageTitle')}</h1>
            <p className="text-gray-500">{t('pageSubtitle')}</p>
          </div>
          <Link
            href={`/${params?.locale}/ledgers/${ledgerId}/gmail-import/settings`}
            className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {t('settings')}
          </Link>
        </div>
      </div>

      {/* Not connected state */}
      {!isConnected && (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center shadow">
          <svg
            className="mx-auto mb-4 h-16 w-16 text-gray-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          <h2 className="mb-2 text-lg font-semibold text-gray-900">{t('notConnectedTitle')}</h2>
          <p className="mb-4 text-gray-500">{t('notConnectedDesc')}</p>
          <Link
            href={`/${params?.locale}/ledgers/${ledgerId}/gmail-import/settings`}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            {t('goToSettings')}
          </Link>
        </div>
      )}

      {/* Connected - scan section */}
      {isConnected && (
        <div className="space-y-6">
          {/* Connection info bar */}
          <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 p-3">
            <div className="h-2 w-2 rounded-full bg-green-500" />
            <span className="text-sm text-green-800">
              {t('connectedAs')} {connection?.email_address}
            </span>
          </div>

          {/* Scan section */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">{t('scan.title')}</h2>
            <ScanProgressIndicator
              scanJob={scanJob}
              isScanning={isScanning}
              onTriggerScan={handleTriggerScan}
            />
            {scanError && (
              <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3">
                <span className="text-sm text-red-700">{scanError}</span>
              </div>
            )}
          </div>

          {/* Import result notification */}
          {importResult && (
            <div
              className={`rounded-lg border p-4 ${
                importResult.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {importResult.success ? (
                    <svg
                      className="h-5 w-5 text-green-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="h-5 w-5 text-red-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  )}
                  <span
                    className={`text-sm ${importResult.success ? 'text-green-800' : 'text-red-800'}`}
                  >
                    {importResult.message}
                    {importResult.count !== undefined &&
                      ` (${t('import.transactionsImported', { count: importResult.count })})`}
                  </span>
                </div>
                <button
                  onClick={() => setImportResult(null)}
                  className="rounded p-1 hover:bg-black/5"
                >
                  <svg
                    className="h-4 w-4 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {/* Results section */}
          {statements.length > 0 && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Statement list */}
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
                <h2 className="mb-4 text-lg font-semibold text-gray-900">
                  {t('statements.title')}
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    ({statements.length})
                  </span>
                </h2>
                <StatementList
                  statements={statements}
                  onSelectStatement={setSelectedStatementId}
                  selectedStatementId={selectedStatementId}
                />
              </div>

              {/* Statement preview */}
              <div>
                {selectedStatement ? (
                  <StatementPreview
                    statement={selectedStatement}
                    onImport={handleImport}
                    onClose={() => setSelectedStatementId(null)}
                    importing={importing}
                  />
                ) : (
                  <div className="rounded-lg border border-gray-200 bg-white p-8 text-center shadow">
                    <svg
                      className="mx-auto mb-3 h-12 w-12 text-gray-300"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                      />
                    </svg>
                    <p className="text-gray-500">{t('preview.selectStatement')}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Empty state after scan with no results */}
          {scanJob?.status === ScanJobStatus.COMPLETED && statements.length === 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center shadow">
              <svg
                className="mx-auto mb-3 h-12 w-12 text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="text-gray-500">{t('scan.noStatements')}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
