'use client'

import { useTranslations } from 'next-intl'
import { ScanJobResponse, ScanJobStatus, ScanTriggerType } from '@/lib/api/gmail-import'

interface ScanHistoryTableProps {
  jobs: ScanJobResponse[]
  onViewStatements?: (jobId: string) => void
}

export default function ScanHistoryTable({ jobs, onViewStatements }: ScanHistoryTableProps) {
  const t = useTranslations('gmailImport')

  if (jobs.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 p-8 text-center">
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
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-gray-500">{t('history.noHistory')}</p>
      </div>
    )
  }

  const getStatusBadge = (status: ScanJobStatus) => {
    const styles: Record<ScanJobStatus, string> = {
      [ScanJobStatus.PENDING]: 'bg-gray-100 text-gray-700',
      [ScanJobStatus.SCANNING]: 'bg-blue-100 text-blue-700',
      [ScanJobStatus.COMPLETED]: 'bg-green-100 text-green-700',
      [ScanJobStatus.FAILED]: 'bg-red-100 text-red-700',
    }
    const labels: Record<ScanJobStatus, string> = {
      [ScanJobStatus.PENDING]: t('scan.status.pending'),
      [ScanJobStatus.SCANNING]: t('scan.status.scanning'),
      [ScanJobStatus.COMPLETED]: t('scan.status.completed'),
      [ScanJobStatus.FAILED]: t('scan.status.failed'),
    }
    return (
      <span
        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${styles[status]}`}
      >
        {labels[status]}
      </span>
    )
  }

  const getTriggerLabel = (trigger: ScanTriggerType) => {
    return trigger === ScanTriggerType.MANUAL
      ? t('history.triggerManual')
      : t('history.triggerScheduled')
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString()
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-xs uppercase text-gray-500">
            <th className="px-3 py-2">{t('history.date')}</th>
            <th className="px-3 py-2">{t('history.trigger')}</th>
            <th className="px-3 py-2">{t('history.status')}</th>
            <th className="px-3 py-2">{t('history.banks')}</th>
            <th className="px-3 py-2">{t('history.statements')}</th>
            <th className="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="px-3 py-2.5 text-gray-900">{formatDate(job.started_at)}</td>
              <td className="px-3 py-2.5 text-gray-600">{getTriggerLabel(job.trigger_type)}</td>
              <td className="px-3 py-2.5">{getStatusBadge(job.status)}</td>
              <td className="px-3 py-2.5 text-gray-600">{job.banks_scanned.length}</td>
              <td className="px-3 py-2.5 text-gray-600">{job.statements_found}</td>
              <td className="px-3 py-2.5">
                {job.status === ScanJobStatus.COMPLETED &&
                  job.statements_found > 0 &&
                  onViewStatements && (
                    <button
                      onClick={() => onViewStatements(job.id)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      {t('history.viewStatements')}
                    </button>
                  )}
                {job.status === ScanJobStatus.FAILED && job.error_message && (
                  <span className="text-xs text-red-500" title={job.error_message}>
                    {t('history.error')}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
