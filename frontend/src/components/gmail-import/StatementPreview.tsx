'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import {
  DiscoveredStatementResponse,
  StatementImportStatus,
  StatementParseStatus,
} from '@/lib/api/gmail-import'

interface StatementPreviewProps {
  statement: DiscoveredStatementResponse
  onImport?: (statementId: string) => void
  onClose: () => void
  importing?: boolean
}

export default function StatementPreview({
  statement,
  onImport,
  onClose,
  importing = false,
}: StatementPreviewProps) {
  const t = useTranslations('gmailImport')
  const [_activeTab] = useState<'details' | 'transactions'>('details')

  const canImport =
    statement.parse_status === StatementParseStatus.PARSED ||
    statement.parse_status === StatementParseStatus.LLM_PARSED

  const isImported = statement.import_status === StatementImportStatus.IMPORTED

  const formatAmount = (amount: number | null) => {
    if (amount === null) return '-'
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'TWD',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  const getConfidenceLabel = (confidence: number | null) => {
    if (confidence === null) return t('preview.confidenceUnknown')
    if (confidence >= 0.8) return t('preview.confidenceHigh')
    if (confidence >= 0.5) return t('preview.confidenceMedium')
    return t('preview.confidenceLow')
  }

  const getConfidenceColor = (confidence: number | null) => {
    if (confidence === null) return 'text-gray-500'
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.5) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 p-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{statement.bank_name}</h3>
          <p className="text-sm text-gray-500">{statement.email_subject}</p>
        </div>
        <button
          onClick={onClose}
          className="rounded-md p-1 hover:bg-gray-100"
          aria-label={t('preview.close')}
        >
          <svg
            className="h-5 w-5 text-gray-400"
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

      {/* Statement info */}
      <div className="space-y-4 p-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-xs uppercase text-gray-500">{t('preview.bank')}</dt>
            <dd className="text-sm font-medium text-gray-900">
              {statement.bank_name} ({statement.bank_code})
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase text-gray-500">{t('preview.emailDate')}</dt>
            <dd className="text-sm font-medium text-gray-900">
              {new Date(statement.email_date).toLocaleDateString()}
            </dd>
          </div>
          {statement.billing_period_start && statement.billing_period_end && (
            <div>
              <dt className="text-xs uppercase text-gray-500">{t('preview.billingPeriod')}</dt>
              <dd className="text-sm font-medium text-gray-900">
                {statement.billing_period_start} ~ {statement.billing_period_end}
              </dd>
            </div>
          )}
          <div>
            <dt className="text-xs uppercase text-gray-500">{t('preview.pdfFile')}</dt>
            <dd className="text-sm font-medium text-gray-900">{statement.pdf_filename}</dd>
          </div>
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-6 rounded-lg bg-gray-50 p-3">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{statement.transaction_count}</div>
            <div className="text-xs text-gray-500">{t('preview.transactions')}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {formatAmount(statement.total_amount)}
            </div>
            <div className="text-xs text-gray-500">{t('preview.totalAmount')}</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getConfidenceColor(statement.parse_confidence)}`}>
              {statement.parse_confidence !== null
                ? `${Math.round(statement.parse_confidence * 100)}%`
                : '-'}
            </div>
            <div className="text-xs text-gray-500">
              {getConfidenceLabel(statement.parse_confidence)}
            </div>
          </div>
        </div>

        {/* Parse status warning */}
        {statement.parse_status === StatementParseStatus.PARSE_FAILED && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3">
            <div className="flex items-center gap-2">
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
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
              <span className="text-sm text-red-700">{t('preview.parseFailed')}</span>
            </div>
          </div>
        )}

        {/* Low confidence warning */}
        {statement.parse_confidence !== null &&
          statement.parse_confidence < 0.5 &&
          statement.parse_status !== StatementParseStatus.PARSE_FAILED && (
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-3">
              <div className="flex items-center gap-2">
                <svg
                  className="h-4 w-4 text-yellow-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
                <span className="text-sm text-yellow-700">{t('preview.lowConfidence')}</span>
              </div>
            </div>
          )}

        {/* Already imported notice */}
        {isImported && (
          <div className="rounded-lg border border-green-200 bg-green-50 p-3">
            <div className="flex items-center gap-2">
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
              <span className="text-sm text-green-700">{t('preview.alreadyImported')}</span>
            </div>
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex items-center justify-end gap-3 border-t border-gray-200 p-4">
        <button
          onClick={onClose}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
        >
          {t('preview.close')}
        </button>
        {canImport && !isImported && onImport && (
          <button
            onClick={() => onImport(statement.id)}
            disabled={importing}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {importing ? (
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
                {t('preview.importing')}
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                {t('preview.importButton')}
              </>
            )}
          </button>
        )}
      </div>
    </div>
  )
}
