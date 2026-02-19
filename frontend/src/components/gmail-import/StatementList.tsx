'use client'

import { useTranslations } from 'next-intl'
import {
  DiscoveredStatementResponse,
  StatementImportStatus,
  StatementParseStatus,
} from '@/lib/api/gmail-import'

interface StatementListProps {
  statements: DiscoveredStatementResponse[]
  onSelectStatement: (statementId: string) => void
  selectedStatementId?: string | null
}

export default function StatementList({
  statements,
  onSelectStatement,
  selectedStatementId,
}: StatementListProps) {
  const t = useTranslations('gmailImport')

  if (statements.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500">
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
        <p>{t('statements.noStatements')}</p>
      </div>
    )
  }

  const getParseStatusBadge = (status: StatementParseStatus) => {
    switch (status) {
      case StatementParseStatus.PARSED:
        return (
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
            {t('statements.parseStatus.parsed')}
          </span>
        )
      case StatementParseStatus.LLM_PARSED:
        return (
          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
            {t('statements.parseStatus.llmParsed')}
          </span>
        )
      case StatementParseStatus.PARSE_FAILED:
        return (
          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-700">
            {t('statements.parseStatus.failed')}
          </span>
        )
      default:
        return (
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
            {t('statements.parseStatus.pending')}
          </span>
        )
    }
  }

  const getImportStatusBadge = (status: StatementImportStatus) => {
    switch (status) {
      case StatementImportStatus.IMPORTED:
        return (
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
            {t('statements.importStatus.imported')}
          </span>
        )
      case StatementImportStatus.SKIPPED:
        return (
          <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs text-yellow-700">
            {t('statements.importStatus.skipped')}
          </span>
        )
      default:
        return null
    }
  }

  const formatAmount = (amount: number | null) => {
    if (amount === null) return '-'
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'TWD',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className="space-y-2">
      {statements.map((statement) => (
        <button
          key={statement.id}
          onClick={() => onSelectStatement(statement.id)}
          className={`w-full rounded-lg border p-4 text-left transition-colors ${
            selectedStatementId === statement.id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="min-w-0 flex-1">
              <div className="mb-1 flex items-center gap-2">
                <span className="font-medium text-gray-900">{statement.bank_name}</span>
                {getParseStatusBadge(statement.parse_status)}
                {getImportStatusBadge(statement.import_status)}
              </div>

              <p className="truncate text-sm text-gray-600">{statement.email_subject}</p>

              <div className="mt-1 flex items-center gap-4 text-xs text-gray-500">
                <span>{new Date(statement.email_date).toLocaleDateString()}</span>
                {statement.billing_period_start && statement.billing_period_end && (
                  <span>
                    {t('statements.billingPeriod')}: {statement.billing_period_start} ~{' '}
                    {statement.billing_period_end}
                  </span>
                )}
                <span>{statement.pdf_filename}</span>
              </div>
            </div>

            <div className="ml-4 flex-shrink-0 text-right">
              {statement.transaction_count > 0 && (
                <div className="text-sm font-medium text-gray-900">
                  {t('statements.transactionCount', {
                    count: statement.transaction_count,
                  })}
                </div>
              )}
              {statement.total_amount !== null && (
                <div className="text-sm text-gray-600">{formatAmount(statement.total_amount)}</div>
              )}
            </div>
          </div>

          {/* Confidence bar */}
          {statement.parse_confidence !== null && (
            <div className="mt-2">
              <div className="flex items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-200">
                  <div
                    className={`h-full rounded-full ${
                      statement.parse_confidence >= 0.8
                        ? 'bg-green-500'
                        : statement.parse_confidence >= 0.5
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                    }`}
                    style={{
                      width: `${statement.parse_confidence * 100}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-gray-500">
                  {Math.round(statement.parse_confidence * 100)}%
                </span>
              </div>
            </div>
          )}
        </button>
      ))}
    </div>
  )
}
