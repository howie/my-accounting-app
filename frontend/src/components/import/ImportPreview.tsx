

import { useState, useEffect, useMemo } from 'react'
import { ImportPreviewResponse, ImportExecuteRequest, ImportResult, importApi } from '@/lib/api/import'
import { accountsApi, AccountListItem } from '@/lib/api/accounts'
import ImportProgress from './ImportProgress'
import CategoryEditor from './CategoryEditor'

interface ImportPreviewProps {
    ledgerId: string
    data: ImportPreviewResponse
    onSuccess: (result: ImportResult) => void
    onCancel: () => void
}

type ImportStatus = 'pending' | 'processing' | 'completed' | 'failed'

export default function ImportPreview({ ledgerId, data, onSuccess, onCancel }: ImportPreviewProps) {
    const [mappings, setMappings] = useState(data.account_mappings)
    const [skipDuplicates, setSkipDuplicates] = useState(true)
    const [existingAccounts, setExistingAccounts] = useState<AccountListItem[]>([])
    const [executing, setExecuting] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [importStatus, setImportStatus] = useState<ImportStatus>('pending')

    // Check if this is a credit card import (has category suggestions)
    const hasCategorySuggestions = useMemo(() => {
        return data.transactions.some((tx: any) => tx.category_suggestion)
    }, [data.transactions])

    useEffect(() => {
        accountsApi.list(ledgerId)
            .then(res => setExistingAccounts(res.data))
            .catch((err) => console.error("Failed to fetch accounts", err))
    }, [ledgerId])

    const handleExecute = async () => {
        setExecuting(true)
        setError(null)
        setImportStatus('processing')
        try {
            const skippedRows = skipDuplicates ? data.duplicates.map((d: any) => d.row_number) : []

            const req: ImportExecuteRequest = {
                session_id: data.session_id,
                account_mappings: mappings,
                skip_duplicate_rows: skippedRows
            }

            const res = await importApi.execute(ledgerId, req)
            setImportStatus('completed')
            onSuccess(res)
        } catch (err: any) {
            console.error(err)
            setError(err.message || 'Import failed')
            setImportStatus('failed')
        } finally {
            setExecuting(false)
        }
    }

    const updateMapping = (index: number, field: string, value: any) => {
        const newMappings = [...mappings]
        newMappings[index] = { ...newMappings[index], [field]: value }

        // If user selects an existing account, set create_new to false and update ID
        if (field === 'system_account_id') {
            if (value) {
                newMappings[index].create_new = false
                newMappings[index].system_account_id = value
                // also update suggested_name to match? Not necessary logic-wise but maybe display
            } else {
                newMappings[index].create_new = true
                newMappings[index].system_account_id = null
            }
        }

        setMappings(newMappings)
    }

    return (
        <div className="space-y-6">
            {/* Errors */}
            {error && (
                <div className="bg-red-50 p-4 border border-red-200 rounded text-red-700">
                    {error}
                </div>
            )}

            {/* Duplicates Warning */}
            {data.duplicates.length > 0 && (
                <div className="bg-yellow-50 p-4 border border-yellow-200 rounded">
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-semibold text-yellow-800">Duplicate Transactions Detected</h4>
                            <p className="text-sm text-yellow-700">
                                {data.duplicates.length} transactions seem to be duplicates.
                            </p>
                        </div>
                        <div className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                id="skipDuplicates"
                                checked={skipDuplicates}
                                onChange={(e) => setSkipDuplicates(e.target.checked)}
                                className="h-4 w-4 text-blue-600 rounded border-gray-300"
                            />
                            <label htmlFor="skipDuplicates" className="text-sm text-yellow-900 font-medium cursor-pointer">
                                Skip Duplicates
                            </label>
                        </div>
                    </div>
                </div>
            )}

            {/* Account Mappings */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <h3 className="text-lg font-bold text-gray-800 mb-4">Account Mappings</h3>
                <p className="text-sm text-gray-500 mb-4">
                    Review how CSV accounts map to your ledger. We&apos;ve auto-matched names where possible.
                </p>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 text-gray-700 font-medium">
                            <tr>
                                <th className="px-4 py-2">CSV Account</th>
                                <th className="px-4 py-2">CSV Type</th>
                                <th className="px-4 py-2">Action</th>
                                <th className="px-4 py-2">Details</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {mappings.map((m: any, idx: number) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                    <td className="px-4 py-2 font-medium">{m.csv_account_name}</td>
                                    <td className="px-4 py-2 text-gray-500 text-xs">{m.csv_account_type}</td>
                                    <td className="px-4 py-2">
                                        <select
                                            value={m.system_account_id || ""}
                                            onChange={(e) => updateMapping(idx, 'system_account_id', e.target.value)}
                                            className="border border-gray-300 rounded px-2 py-1 text-sm bg-white"
                                        >
                                            <option value="">Create New Account</option>
                                            <optgroup label="Existing Accounts">
                                                {existingAccounts.map(acc => (
                                                    <option key={acc.id} value={acc.id}>{acc.name} ({acc.type})</option>
                                                ))}
                                            </optgroup>
                                        </select>
                                    </td>
                                    <td className="px-4 py-2">
                                        {!m.system_account_id ? (
                                            <div className="flex items-center space-x-2">
                                                <span className="text-green-600 text-xs bg-green-50 px-2 py-0.5 rounded border border-green-100">New</span>
                                                <span className="text-gray-600">{m.suggested_name || m.csv_account_name}</span>
                                            </div>
                                        ) : (
                                            <span className="text-blue-600 text-xs bg-blue-50 px-2 py-0.5 rounded border border-blue-100">Map</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Transaction Preview */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                <h3 className="text-lg font-bold text-gray-800 mb-4">Transaction Preview ({data.total_count})</h3>
                {hasCategorySuggestions && (
                    <p className="text-sm text-gray-500 mb-4">
                        信用卡交易已自動分類。點擊類別可修改。
                    </p>
                )}
                <div className="overflow-x-auto max-h-96">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 text-gray-700 sticky top-0">
                            <tr>
                                <th className="px-4 py-2">Row</th>
                                <th className="px-4 py-2">Date</th>
                                {!hasCategorySuggestions && <th className="px-4 py-2">Type</th>}
                                <th className="px-4 py-2">Description</th>
                                <th className="px-4 py-2 text-right">Amount</th>
                                {hasCategorySuggestions ? (
                                    <>
                                        <th className="px-4 py-2">Card</th>
                                        <th className="px-4 py-2">Category</th>
                                    </>
                                ) : (
                                    <>
                                        <th className="px-4 py-2">From</th>
                                        <th className="px-4 py-2">To</th>
                                    </>
                                )}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {data.transactions.map((tx: any, i: number) => (
                                <tr key={i} className={`hover:bg-gray-50 ${data.duplicates.some((d: any) => d.row_number === tx.row_number) ? "bg-yellow-50" : ""}`}>
                                    <td className="px-4 py-2 text-gray-500">{tx.row_number}</td>
                                    <td className="px-4 py-2">{tx.date}</td>
                                    {!hasCategorySuggestions && <td className="px-4 py-2">{tx.transaction_type}</td>}
                                    <td className="px-4 py-2">{tx.description}</td>
                                    <td className="px-4 py-2 text-right font-mono">{tx.amount}</td>
                                    {hasCategorySuggestions ? (
                                        <>
                                            <td className="px-4 py-2 text-xs truncate max-w-[150px]" title={tx.from_account_name}>
                                                {tx.from_account_name}
                                            </td>
                                            <td className="px-4 py-2">
                                                <CategoryEditor
                                                    suggestion={tx.category_suggestion}
                                                    value={tx.to_account_name}
                                                />
                                            </td>
                                        </>
                                    ) : (
                                        <>
                                            <td className="px-4 py-2 text-xs truncate max-w-[150px]" title={tx.from_account_name}>{tx.from_account_name}</td>
                                            <td className="px-4 py-2 text-xs truncate max-w-[150px]" title={tx.to_account_name}>{tx.to_account_name}</td>
                                        </>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Progress Indicator */}
            {executing && (
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                    <ImportProgress
                        current={importStatus === 'processing' ? data.total_count : 0}
                        total={data.total_count}
                        status={importStatus}
                    />
                </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-4 pt-4">
                <button
                    onClick={onCancel}
                    disabled={executing}
                    className="px-6 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 bg-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Cancel
                </button>
                <button
                    onClick={handleExecute}
                    disabled={executing}
                    className={`px-6 py-2 rounded text-white font-medium ${executing ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                        }`}
                >
                    {executing ? 'Importing...' : 'Confirm Import'}
                </button>
            </div>
        </div>
    )
}
