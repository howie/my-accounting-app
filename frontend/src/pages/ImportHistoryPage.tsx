import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { importApi } from '@/lib/api/import'

interface ImportHistoryItem {
  id: string
  import_type: string
  source_filename: string
  status: string
  imported_count: number
  skipped_count: number
  error_count: number
  created_accounts_count: number
  created_at: string | null
  completed_at: string | null
}

interface ImportHistoryResponse {
  items: ImportHistoryItem[]
  total: number
}

export default function ImportHistoryPage() {
  const params = useParams()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const ledgerId = (params?.id ?? '') as string

  const [history, setHistory] = useState<ImportHistoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const pageSize = 10

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = (await importApi.getHistory(
          ledgerId,
          pageSize,
          page * pageSize
        )) as ImportHistoryResponse
        setHistory(response.items)
        setTotal(response.total)
      } catch (err: unknown) {
        console.error(err)
        setError(err instanceof Error ? err.message : 'Failed to load history')
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [ledgerId, page])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-100 text-green-800'
      case 'FAILED':
        return 'bg-red-100 text-red-800'
      case 'PROCESSING':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return t('import.statusCompleted')
      case 'FAILED':
        return t('import.statusFailed')
      case 'PROCESSING':
        return t('import.statusProcessing')
      default:
        return t('import.statusPending')
    }
  }

  const getImportTypeText = (type: string) => {
    switch (type) {
      case 'MYAB_CSV':
        return t('import.myabCsv')
      case 'CREDIT_CARD':
        return t('import.creditCard')
      default:
        return type
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('import.history')}</h1>
          <p className="text-gray-500">{t('import.subtitle')}</p>
        </div>
        <Link
          to={`/ledgers/${ledgerId}/import`}
          className="rounded-md bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
        >
          {t('import.title')}
        </Link>
      </div>

      {loading ? (
        <div className="rounded-lg border border-gray-100 bg-white p-8 text-center shadow-sm">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <p className="text-gray-500">{t('common.loading')}</p>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">{error}</div>
      ) : history.length === 0 ? (
        <div className="rounded-lg border border-gray-100 bg-white p-8 text-center shadow-sm">
          <p className="text-gray-500">{t('import.noHistory')}</p>
          <button
            onClick={() => navigate(`/ledgers/${ledgerId}/import`)}
            className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
          >
            {t('import.title')}
          </button>
        </div>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-gray-100 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 font-medium text-gray-700">
                <tr>
                  <th className="px-4 py-3">{t('import.importType')}</th>
                  <th className="px-4 py-3">{t('import.selectFile')}</th>
                  <th className="px-4 py-3">{t('import.status')}</th>
                  <th className="px-4 py-3 text-right">{t('import.importedCount')}</th>
                  <th className="px-4 py-3 text-right">{t('import.skippedCount')}</th>
                  <th className="px-4 py-3 text-right">{t('import.createdAccounts')}</th>
                  <th className="px-4 py-3">{t('common.createdAt')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {history.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-700">
                        {getImportTypeText(item.import_type)}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium">{item.source_filename}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded px-2 py-1 text-xs ${getStatusColor(item.status)}`}>
                        {getStatusText(item.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono">{item.imported_count}</td>
                    <td className="px-4 py-3 text-right font-mono">{item.skipped_count}</td>
                    <td className="px-4 py-3 text-right font-mono">
                      {item.created_accounts_count}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-center space-x-4">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="rounded-md border border-gray-300 px-3 py-1 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {t('common.previous')}
              </button>
              <span className="text-sm text-gray-600">
                Page {page + 1} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="rounded-md border border-gray-300 px-3 py-1 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {t('common.next')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
