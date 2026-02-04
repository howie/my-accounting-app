

import { useTranslation } from 'react-i18next'

interface ImportProgressProps {
    current: number
    total: number
    status: 'pending' | 'processing' | 'completed' | 'failed'
}

export default function ImportProgress({ current, total, status }: ImportProgressProps) {
    const { t } = useTranslation(undefined, { keyPrefix: 'import' })

    const percentage = total > 0 ? Math.round((current / total) * 100) : 0

    const statusColors = {
        pending: 'bg-gray-200',
        processing: 'bg-blue-500',
        completed: 'bg-green-500',
        failed: 'bg-red-500',
    }

    const statusText = {
        pending: t('statusPending'),
        processing: t('statusProcessing'),
        completed: t('statusCompleted'),
        failed: t('statusFailed'),
    }

    return (
        <div className="w-full">
            <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">
                    {t('progress')}
                </span>
                <span className="text-sm text-gray-500">
                    {t('progressText', { current, total })}
                </span>
            </div>

            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                <div
                    className={`h-2.5 rounded-full transition-all duration-300 ${statusColors[status]}`}
                    style={{ width: `${percentage}%` }}
                />
            </div>

            <div className="flex justify-between items-center">
                <span className={`text-xs px-2 py-0.5 rounded ${
                    status === 'processing' ? 'bg-blue-100 text-blue-700' :
                    status === 'completed' ? 'bg-green-100 text-green-700' :
                    status === 'failed' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-600'
                }`}>
                    {statusText[status]}
                </span>
                <span className="text-sm font-medium text-gray-700">
                    {percentage}%
                </span>
            </div>
        </div>
    )
}
