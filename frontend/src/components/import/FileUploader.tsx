'use client'

import { useState } from 'react'
import { ImportType, importApi, ImportPreviewResponse } from '@/lib/api/import'
import BankSelector from './BankSelector'

interface FileUploaderProps {
  ledgerId: string
  onPreviewLoaded: (data: ImportPreviewResponse) => void
}

export default function FileUploader({ ledgerId, onPreviewLoaded }: FileUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [importType, setImportType] = useState<ImportType>(ImportType.MYAB_CSV)
  const [bankCode, setBankCode] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const needsBankCode =
    importType === ImportType.CREDIT_CARD || importType === ImportType.BANK_RECORD

  const handleImportTypeChange = (type: ImportType) => {
    setImportType(type)
    // Reset bank code when switching import types
    setBankCode(null)
  }

  const handleUpload = async () => {
    if (!file) return
    if (needsBankCode && !bankCode) {
      setError('Please select a bank')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await importApi.createPreview(
        ledgerId,
        file,
        importType,
        needsBankCode ? (bankCode ?? undefined) : undefined
      )
      onPreviewLoaded(response)
    } catch (err: any) {
      console.error(err)
      setError(err.message || 'Failed to upload file')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mb-6 rounded-lg border border-gray-100 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-gray-800">1. Upload File</h2>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Import Type</label>
          <select
            value={importType}
            onChange={(e) => handleImportTypeChange(e.target.value as ImportType)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          >
            <option value={ImportType.MYAB_CSV}>MyAB CSV Export</option>
            <option value={ImportType.CREDIT_CARD}>Credit Card Statement</option>
            <option value={ImportType.BANK_RECORD}>Bank Account Statement</option>
          </select>
        </div>

        {needsBankCode && (
          <BankSelector
            value={bankCode}
            onChange={setBankCode}
            disabled={loading}
            importType={importType}
          />
        )}

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Select File</label>
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
          disabled={!file || loading || (needsBankCode && !bankCode)}
          className={`w-full rounded-md px-4 py-2 font-medium text-white transition-colors ${
            !file || loading || (needsBankCode && !bankCode)
              ? 'cursor-not-allowed bg-gray-400'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? 'Analyzing...' : 'Generate Preview'}
        </button>
      </div>
    </div>
  )
}
