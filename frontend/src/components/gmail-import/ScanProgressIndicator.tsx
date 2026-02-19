'use client'

import { useTranslations } from 'next-intl'
import { ScanJobResponse, ScanJobStatus } from '@/lib/api/gmail-import'

interface ScanProgressIndicatorProps {
  scanJob: ScanJobResponse | null
  isScanning: boolean
  onTriggerScan: () => void
  disabled?: boolean
}

export default function ScanProgressIndicator({
  scanJob,
  isScanning,
  onTriggerScan,
  disabled = false,
}: ScanProgressIndicatorProps) {
  const t = useTranslations('gmailImport')

  const getStatusColor = (status: ScanJobStatus) => {
    switch (status) {
      case ScanJobStatus.COMPLETED:
        return 'text-green-600'
      case ScanJobStatus.FAILED:
        return 'text-red-600'
      case ScanJobStatus.SCANNING:
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusBgColor = (status: ScanJobStatus) => {
    switch (status) {
      case ScanJobStatus.COMPLETED:
        return 'bg-green-50 border-green-200'
      case ScanJobStatus.FAILED:
        return 'bg-red-50 border-red-200'
      case ScanJobStatus.SCANNING:
        return 'bg-blue-50 border-blue-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="space-y-4">
      {/* Scan trigger button */}
      <div className="flex items-center gap-3">
        <button
          onClick={onTriggerScan}
          disabled={disabled || isScanning}
          className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isScanning ? (
            <>
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              {t('scan.scanning')}
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              {t('scan.triggerScan')}
            </>
          )}
        </button>
      </div>

      {/* Scan status */}
      {scanJob && (
        <div className={`rounded-lg border p-4 ${getStatusBgColor(scanJob.status)}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {scanJob.status === ScanJobStatus.SCANNING && (
                <svg className="h-4 w-4 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
              )}
              {scanJob.status === ScanJobStatus.COMPLETED && (
                <svg
                  className="h-4 w-4 text-green-600"
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
              )}
              {scanJob.status === ScanJobStatus.FAILED && (
                <svg
                  className="h-4 w-4 text-red-600"
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
              <span className={`text-sm font-medium ${getStatusColor(scanJob.status)}`}>
                {t(`scan.status.${scanJob.status.toLowerCase()}`)}
              </span>
            </div>

            {scanJob.started_at && (
              <span className="text-xs text-gray-500">
                {new Date(scanJob.started_at).toLocaleString()}
              </span>
            )}
          </div>

          {/* Banks scanned */}
          {scanJob.banks_scanned.length > 0 && (
            <div className="mt-2 text-sm text-gray-600">
              {t('scan.banksScanned')}: {scanJob.banks_scanned.join(', ')}
            </div>
          )}

          {/* Statements found */}
          {scanJob.status === ScanJobStatus.COMPLETED && (
            <div className="mt-1 text-sm text-gray-600">
              {t('scan.statementsFound', { count: scanJob.statements_found })}
            </div>
          )}

          {/* Error message */}
          {scanJob.error_message && (
            <div className="mt-2 text-sm text-red-600">{scanJob.error_message}</div>
          )}
        </div>
      )}
    </div>
  )
}
