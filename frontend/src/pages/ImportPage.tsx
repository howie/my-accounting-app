import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import FileUploader from '@/components/import/FileUploader'
import ImportPreview from '@/components/import/ImportPreview'
import { ImportPreviewResponse, ImportResult } from '@/lib/api/import'

export default function ImportPage() {
  const params = useParams()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const ledgerId = (params?.id ?? '') as string
  const idValue = Array.isArray(ledgerId) ? ledgerId[0] : ledgerId

  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null)
  const [result, setResult] = useState<ImportResult | null>(null)

  const handleSuccess = (res: ImportResult) => {
    setResult(res)
    setPreviewData(null)
  }

  const handleCancelPreview = () => {
    setPreviewData(null)
  }

  const handleReset = () => {
    setResult(null)
    setPreviewData(null)
  }

  if (result) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12 text-center">
        <div className="rounded-lg border border-green-100 bg-white p-8 shadow-lg">
          <div className="mb-6 flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-green-600">
              <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M5 13l4 4L19 7"
                ></path>
              </svg>
            </div>
          </div>

          <h2 className="mb-2 text-3xl font-bold text-gray-800">{t('import.importSuccess')}</h2>
          <p className="mb-8 text-gray-500">
            {t('import.importSuccessMessage', { count: result.imported_count })}
          </p>

          <div className="mb-8 grid grid-cols-3 gap-4">
            <div className="rounded border border-gray-100 bg-gray-50 p-4">
              <div className="text-3xl font-bold text-gray-900">{result.imported_count}</div>
              <div className="text-xs font-bold uppercase tracking-wider text-gray-400">
                {t('import.importedCount')}
              </div>
            </div>
            <div className="rounded border border-gray-100 bg-gray-50 p-4">
              <div className="text-3xl font-bold text-gray-900">
                {result.created_accounts.length}
              </div>
              <div className="text-xs font-bold uppercase tracking-wider text-gray-400">
                {t('import.createdAccounts')}
              </div>
            </div>
            <div className="rounded border border-gray-100 bg-gray-50 p-4">
              <div className="text-3xl font-bold text-gray-900">{result.skipped_count}</div>
              <div className="text-xs font-bold uppercase tracking-wider text-gray-400">
                {t('import.skippedCount')}
              </div>
            </div>
          </div>

          <div className="flex justify-center space-x-4">
            <button
              onClick={handleReset}
              className="rounded border border-gray-300 px-6 py-2 text-gray-700 transition-colors hover:bg-gray-50"
            >
              {t('import.importMore')}
            </button>
            <button
              onClick={() => navigate(`/ledgers/${idValue}`)}
              className="rounded bg-blue-600 px-6 py-2 font-medium text-white shadow-md transition-colors hover:bg-blue-700"
            >
              {t('import.viewTransactions')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      {!previewData ? (
        <>
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{t('import.title')}</h1>
              <p className="text-gray-500">{t('import.subtitle')}</p>
            </div>
            <Link
              to={`/ledgers/${idValue}/import/history`}
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              {t('import.history')}
            </Link>
          </div>
          <FileUploader ledgerId={idValue} onPreviewLoaded={setPreviewData} />
        </>
      ) : (
        <ImportPreview
          ledgerId={idValue}
          data={previewData}
          onSuccess={handleSuccess}
          onCancel={handleCancelPreview}
        />
      )}
    </div>
  )
}
