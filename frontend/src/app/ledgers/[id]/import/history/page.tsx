'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import Link from 'next/link'
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
    const router = useRouter()
    const t = useTranslations('import')
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
                const response = await importApi.getHistory(ledgerId, pageSize, page * pageSize) as ImportHistoryResponse
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
                return t('statusCompleted')
            case 'FAILED':
                return t('statusFailed')
            case 'PROCESSING':
                return t('statusProcessing')
            default:
                return t('statusPending')
        }
    }

    const getImportTypeText = (type: string) => {
        switch (type) {
            case 'MYAB_CSV':
                return t('myabCsv')
            case 'CREDIT_CARD':
                return t('creditCard')
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
        <div className="max-w-5xl mx-auto py-8 px-4">
            <div className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">{t('history')}</h1>
                    <p className="text-gray-500">{t('subtitle')}</p>
                </div>
                <Link
                    href={`/ledgers/${ledgerId}/import`}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                    {t('title')}
                </Link>
            </div>

            {loading ? (
                <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-100 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-500">Loading...</p>
                </div>
            ) : error ? (
                <div className="bg-red-50 p-6 rounded-lg border border-red-200 text-red-700">
                    {error}
                </div>
            ) : history.length === 0 ? (
                <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-100 text-center">
                    <p className="text-gray-500">{t('noHistory')}</p>
                    <button
                        onClick={() => router.push(`/ledgers/${ledgerId}/import`)}
                        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                        {t('title')}
                    </button>
                </div>
            ) : (
                <>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-gray-50 text-gray-700 font-medium">
                                <tr>
                                    <th className="px-4 py-3">{t('importType')}</th>
                                    <th className="px-4 py-3">{t('selectFile')}</th>
                                    <th className="px-4 py-3">{t('status')}</th>
                                    <th className="px-4 py-3 text-right">{t('importedCount')}</th>
                                    <th className="px-4 py-3 text-right">{t('skippedCount')}</th>
                                    <th className="px-4 py-3 text-right">{t('createdAccounts')}</th>
                                    <th className="px-4 py-3">Created At</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {history.map((item) => (
                                    <tr key={item.id} className="hover:bg-gray-50">
                                        <td className="px-4 py-3">
                                            <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                                                {getImportTypeText(item.import_type)}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 font-medium">{item.source_filename}</td>
                                        <td className="px-4 py-3">
                                            <span className={`text-xs px-2 py-1 rounded ${getStatusColor(item.status)}`}>
                                                {getStatusText(item.status)}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-right font-mono">{item.imported_count}</td>
                                        <td className="px-4 py-3 text-right font-mono">{item.skipped_count}</td>
                                        <td className="px-4 py-3 text-right font-mono">{item.created_accounts_count}</td>
                                        <td className="px-4 py-3 text-gray-500">{formatDate(item.created_at)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="mt-4 flex justify-center items-center space-x-4">
                            <button
                                onClick={() => setPage(p => Math.max(0, p - 1))}
                                disabled={page === 0}
                                className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                            >
                                Previous
                            </button>
                            <span className="text-sm text-gray-600">
                                Page {page + 1} of {totalPages}
                            </span>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                                disabled={page >= totalPages - 1}
                                className="px-3 py-1 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
