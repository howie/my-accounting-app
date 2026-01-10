'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import FileUploader from '@/components/import/FileUploader'
import ImportPreview from '@/components/import/ImportPreview'
import { ImportPreviewResponse, ImportResult } from '@/lib/api/import'

export default function ImportPage() {
    const params = useParams()
    const router = useRouter()
    const ledgerId = params.id as string
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
            <div className="max-w-3xl mx-auto py-12 px-4 text-center">
                <div className="bg-white p-8 rounded-lg shadow-lg border border-green-100">
                    <div className="mb-6 flex justify-center">
                        <div className="h-16 w-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                        </div>
                    </div>

                    <h2 className="text-3xl font-bold text-gray-800 mb-2">Import Complete!</h2>
                    <p className="text-gray-500 mb-8">Your transactions have been successfully imported.</p>

                    <div className="grid grid-cols-3 gap-4 mb-8">
                        <div className="p-4 bg-gray-50 rounded border border-gray-100">
                            <div className="text-3xl font-bold text-gray-900">{result.imported_count}</div>
                            <div className="text-xs uppercase font-bold text-gray-400 tracking-wider">Imported</div>
                        </div>
                        <div className="p-4 bg-gray-50 rounded border border-gray-100">
                            <div className="text-3xl font-bold text-gray-900">{result.created_accounts.length}</div>
                            <div className="text-xs uppercase font-bold text-gray-400 tracking-wider">New Accounts</div>
                        </div>
                        <div className="p-4 bg-gray-50 rounded border border-gray-100">
                            <div className="text-3xl font-bold text-gray-900">{result.skipped_count}</div>
                            <div className="text-xs uppercase font-bold text-gray-400 tracking-wider">Skipped</div>
                        </div>
                    </div>

                    <div className="flex justify-center space-x-4">
                        <button
                            onClick={handleReset}
                            className="px-6 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                            Import More
                        </button>
                        <button
                            onClick={() => router.push(`/ledgers/${idValue}/transactions`)}
                            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium shadow-md transition-colors"
                        >
                            View Transactions
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="max-w-5xl mx-auto py-8 px-4">
            {!previewData ? (
                <>
                    <div className="mb-8">
                        <h1 className="text-2xl font-bold text-gray-900">Import Transactions</h1>
                        <p className="text-gray-500">Upload CSV files to import transactions into your ledger.</p>
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
