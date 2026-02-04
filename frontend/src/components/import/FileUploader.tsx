

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
                importType === ImportType.CREDIT_CARD ? bankCode ?? undefined : undefined
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
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 mb-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">1. Upload File</h2>

            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Import Type</label>
                    <select
                        value={importType}
                        onChange={(e) => handleImportTypeChange(e.target.value as ImportType)}
                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={loading}
                    >
                        <option value={ImportType.MYAB_CSV}>MyAB CSV Export</option>
                        <option value={ImportType.CREDIT_CARD}>Credit Card Statement</option>
                    </select>
                </div>

                {importType === ImportType.CREDIT_CARD && (
                    <BankSelector
                        value={bankCode}
                        onChange={setBankCode}
                        disabled={loading}
                    />
                )}

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Select File</label>
                    <input
                        type="file"
                        accept=".csv"
                        onChange={handleFileChange}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                        disabled={loading}
                    />
                </div>

                {error && (
                    <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
                        {error}
                    </div>
                )}

                <button
                    onClick={handleUpload}
                    disabled={!file || loading || (importType === ImportType.CREDIT_CARD && !bankCode)}
                    className={`w-full py-2 px-4 rounded-md text-white font-medium transition-colors ${!file || loading || (importType === ImportType.CREDIT_CARD && !bankCode)
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700'
                        }`}
                >
                    {loading ? 'Analyzing...' : 'Generate Preview'}
                </button>
            </div>
        </div>
    )
}
