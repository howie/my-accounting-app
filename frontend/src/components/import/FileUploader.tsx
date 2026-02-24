import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ImportType, importApi, ImportPreviewResponse } from '@/lib/api/import'
import { useLedgers } from '@/lib/hooks/useLedgers'
import BankSelector from './BankSelector'

interface FileUploaderProps {
  ledgerId: string
  onPreviewLoaded: (data: ImportPreviewResponse) => void
}

export default function FileUploader({ ledgerId, onPreviewLoaded }: FileUploaderProps) {
  const { t } = useTranslation()
  const [file, setFile] = useState<File | null>(null)
  const [importType, setImportType] = useState<ImportType>(ImportType.MYAB_CSV)
  const [bankCode, setBankCode] = useState<string | null>(null)
  const [referenceLedgerId, setReferenceLedgerId] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: ledgers } = useLedgers()
  const otherLedgers = ledgers?.filter((l) => l.id !== ledgerId) ?? []

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleImportTypeChange = (type: ImportType) => {
    setImportType(type)
    // Reset bank code when switching import types
    if (type !== ImportType.CREDIT_CARD) {
      setBankCode(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    if (importType === ImportType.CREDIT_CARD && !bankCode) {
      setError(t('import.selectBankRequired'))
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await importApi.createPreview(
        ledgerId,
        file,
        importType,
        importType === ImportType.CREDIT_CARD ? (bankCode ?? undefined) : undefined,
        referenceLedgerId || undefined
      )
      onPreviewLoaded(response)
    } catch (err: any) {
      console.error(err)
      setError(err.message || t('import.uploadError'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mb-6 rounded-lg border border-gray-100 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-gray-800">1. {t('import.uploadFile')}</h2>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            {t('import.importType')}
          </label>
          <select
            value={importType}
            onChange={(e) => handleImportTypeChange(e.target.value as ImportType)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          >
            <option value={ImportType.MYAB_CSV}>{t('import.myabCsv')}</option>
            <option value={ImportType.CREDIT_CARD}>{t('import.creditCard')}</option>
          </select>
        </div>

        {importType === ImportType.CREDIT_CARD && (
          <BankSelector value={bankCode} onChange={setBankCode} disabled={loading} />
        )}

        {otherLedgers.length > 0 && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              {t('import.referenceLedger')}
            </label>
            <select
              value={referenceLedgerId}
              onChange={(e) => setReferenceLedgerId(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="">{t('import.referenceLedgerPlaceholder')}</option>
              {otherLedgers.map((ledger) => (
                <option key={ledger.id} value={ledger.id}>
                  {ledger.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            {t('import.selectFile')}
          </label>
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
            disabled={loading}
          />
        </div>

        {error && <div className="rounded bg-red-50 p-2 text-sm text-red-600">{error}</div>}

        <button
          onClick={handleUpload}
          disabled={!file || loading || (importType === ImportType.CREDIT_CARD && !bankCode)}
          className={`w-full rounded-md px-4 py-2 font-medium text-white transition-colors ${
            !file || loading || (importType === ImportType.CREDIT_CARD && !bankCode)
              ? 'cursor-not-allowed bg-gray-400'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? t('import.analyzing') : t('import.generatePreview')}
        </button>
      </div>
    </div>
  )
}
