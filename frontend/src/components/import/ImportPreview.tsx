import { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import {
  ImportPreviewResponse,
  ImportExecuteRequest,
  ImportResult,
  TransactionOverride,
  importApi,
} from '@/lib/api/import'
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

type TxEdit = {
  date?: string
  amount?: string
  description?: string
  toAccountId?: string
}

type EditingCell = { row: number; field: 'date' | 'description' | 'amount' } | null

export default function ImportPreview({ ledgerId, data, onSuccess, onCancel }: ImportPreviewProps) {
  const { t } = useTranslation()
  const [mappings, setMappings] = useState(data.account_mappings)
  const [skipDuplicates, setSkipDuplicates] = useState(true)
  const [existingAccounts, setExistingAccounts] = useState<AccountListItem[]>([])
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [importStatus, setImportStatus] = useState<ImportStatus>('pending')
  const [txEdits, setTxEdits] = useState<Record<number, TxEdit>>({})
  const [editingCell, setEditingCell] = useState<EditingCell>(null)

  const hasCategorySuggestions = useMemo(() => {
    return data.transactions.some((tx: any) => tx.category_suggestion)
  }, [data.transactions])

  useEffect(() => {
    accountsApi
      .list(ledgerId)
      .then((res) => setExistingAccounts(res.data))
      .catch((err) => console.error('Failed to fetch accounts', err))
  }, [ledgerId])

  // Map CSV account names to system account names based on current mappings
  const accountNameMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const m of mappings) {
      if (m.system_account_id) {
        const acc = existingAccounts.find((a: AccountListItem) => a.id === m.system_account_id)
        map[m.csv_account_name] = acc?.name ?? m.csv_account_name
      } else {
        map[m.csv_account_name] = m.suggested_name ?? m.csv_account_name
      }
    }
    return map
  }, [mappings, existingAccounts])

  // Resolved transactions with display names derived from current mappings
  const resolvedTransactions = useMemo(
    () =>
      data.transactions.map((tx: any) => ({
        ...tx,
        _displayFrom: accountNameMap[tx.from_account_name] ?? tx.from_account_name,
        _displayTo: accountNameMap[tx.to_account_name] ?? tx.to_account_name,
      })),
    [data.transactions, accountNameMap]
  )

  const expenseAccounts = useMemo(
    () => existingAccounts.filter((a: AccountListItem) => a.type === 'EXPENSE'),
    [existingAccounts]
  )

  const handleExecute = async () => {
    setExecuting(true)
    setError(null)
    setImportStatus('processing')
    try {
      const skippedRows = skipDuplicates ? data.duplicates.map((d: any) => d.row_number) : []

      const overrides: Record<number, TransactionOverride> = {}
      for (const [rowStr, edit] of Object.entries(txEdits)) {
        const row = parseInt(rowStr)
        const override: TransactionOverride = {}
        if (edit.date) override.date = edit.date
        if (edit.amount) override.amount = parseFloat(edit.amount)
        if (edit.description !== undefined) override.description = edit.description
        if (edit.toAccountId) override.to_account_id = edit.toAccountId
        overrides[row] = override
      }

      const req: ImportExecuteRequest = {
        session_id: data.session_id,
        account_mappings: mappings,
        skip_duplicate_rows: skippedRows,
        ...(Object.keys(overrides).length > 0 ? { transaction_overrides: overrides } : {}),
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

    if (field === 'system_account_id') {
      if (value) {
        newMappings[index].create_new = false
        newMappings[index].system_account_id = value
      } else {
        newMappings[index].create_new = true
        newMappings[index].system_account_id = null
      }
    }

    setMappings(newMappings)
  }

  const updateTxEdit = (rowNumber: number, field: keyof TxEdit, value: string) => {
    setTxEdits((prev) => ({
      ...prev,
      [rowNumber]: { ...prev[rowNumber], [field]: value },
    }))
  }

  const resetTxEdit = (rowNumber: number) => {
    setTxEdits((prev) => {
      const next = { ...prev }
      delete next[rowNumber]
      return next
    })
  }

  const renderEditableCell = (
    tx: any,
    field: 'date' | 'description' | 'amount',
    inputType: 'date' | 'text' | 'number',
    className?: string
  ) => {
    const isEditing = editingCell?.row === tx.row_number && editingCell?.field === field
    const override = txEdits[tx.row_number]
    const currentValue = override?.[field] ?? tx[field]?.toString() ?? ''
    const isModified = override?.[field] !== undefined

    if (isEditing) {
      return (
        <input
          type={inputType}
          defaultValue={currentValue}
          autoFocus
          className={`rounded border border-blue-400 px-1 py-0.5 text-sm focus:outline-none ${className ?? 'w-full'}`}
          onBlur={(e) => {
            const newVal = e.target.value
            if (newVal !== (tx[field]?.toString() ?? '')) {
              updateTxEdit(tx.row_number, field, newVal)
            }
            setEditingCell(null)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') e.currentTarget.blur()
            if (e.key === 'Escape') setEditingCell(null)
          }}
        />
      )
    }

    return (
      <span
        className={`cursor-pointer rounded px-1 py-0.5 hover:bg-blue-50 ${isModified ? 'font-medium text-blue-700' : ''}`}
        onClick={() => !executing && setEditingCell({ row: tx.row_number, field })}
        title={isModified ? t('import.editedRow') : undefined}
      >
        {currentValue || <span className="text-gray-400">—</span>}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Errors */}
      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
      )}

      {/* Validation Errors from parsing */}
      {data.validation_errors && data.validation_errors.length > 0 && (
        <div className="rounded border border-red-200 bg-red-50 p-4">
          <h4 className="mb-2 font-semibold text-red-800">
            {t('import.validationErrors', { count: data.validation_errors.length })}
          </h4>
          <ul className="max-h-40 space-y-1 overflow-y-auto text-sm text-red-700">
            {data.validation_errors.map((err: any, i: number) => (
              <li key={i}>
                Row {err.row}: {err.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Duplicates Warning */}
      {data.duplicates.length > 0 && (
        <div className="rounded border border-yellow-200 bg-yellow-50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-yellow-800">
                {t('import.duplicateTransactionsDetected')}
              </h4>
              <p className="text-sm text-yellow-700">
                {t('import.duplicateCount', { count: data.duplicates.length })}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="skipDuplicates"
                checked={skipDuplicates}
                onChange={(e) => setSkipDuplicates(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600"
              />
              <label
                htmlFor="skipDuplicates"
                className="cursor-pointer text-sm font-medium text-yellow-900"
              >
                {t('import.skipDuplicates')}
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Account Mappings */}
      <div className="rounded-lg border border-gray-100 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-bold text-gray-800">{t('import.accountMappings')}</h3>
        <p className="mb-4 text-sm text-gray-500">{t('import.reviewAccountMappings')}</p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 font-medium text-gray-700">
              <tr>
                <th className="px-4 py-2">{t('import.csvAccount')}</th>
                <th className="px-4 py-2">{t('import.csvType')}</th>
                <th className="px-4 py-2">{t('import.action')}</th>
                <th className="px-4 py-2">{t('import.details')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {mappings.map((m: any, idx: number) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium">{m.csv_account_name}</td>
                  <td className="px-4 py-2 text-xs text-gray-500">{m.csv_account_type}</td>
                  <td className="px-4 py-2">
                    <select
                      value={m.system_account_id || ''}
                      onChange={(e) => updateMapping(idx, 'system_account_id', e.target.value)}
                      className="rounded border border-gray-300 bg-white px-2 py-1 text-sm"
                    >
                      <option value="">{t('import.createNewAccount')}</option>
                      <optgroup label={t('import.existingAccounts')}>
                        {existingAccounts.map((acc) => (
                          <option key={acc.id} value={acc.id}>
                            {acc.name} ({acc.type})
                          </option>
                        ))}
                      </optgroup>
                    </select>
                  </td>
                  <td className="px-4 py-2">
                    {!m.system_account_id ? (
                      <div className="flex items-center space-x-2">
                        <span className="rounded border border-green-100 bg-green-50 px-2 py-0.5 text-xs text-green-600">
                          New
                        </span>
                        <span className="text-gray-600">
                          {m.suggested_name || m.csv_account_name}
                        </span>
                      </div>
                    ) : (
                      <span className="rounded border border-blue-100 bg-blue-50 px-2 py-0.5 text-xs text-blue-600">
                        Map
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transaction Preview */}
      <div className="rounded-lg border border-gray-100 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-bold text-gray-800">
          {t('import.transactionPreview', { count: data.total_count })}
        </h3>
        {hasCategorySuggestions && (
          <p className="mb-4 text-sm text-gray-500">{t('import.creditCardAutoCategory')}</p>
        )}
        <div className="max-h-96 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-gray-50 text-gray-700">
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
              {resolvedTransactions.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-400">
                    {t('import.noTransactions')}
                  </td>
                </tr>
              )}
              {resolvedTransactions.map((tx: any, i: number) => {
                const hasEdit =
                  Boolean(txEdits[tx.row_number]) && Object.keys(txEdits[tx.row_number]).length > 0
                const isDuplicate = data.duplicates.some((d: any) => d.row_number === tx.row_number)
                const toDisplayName = txEdits[tx.row_number]?.toAccountId
                  ? (existingAccounts.find((a) => a.id === txEdits[tx.row_number]?.toAccountId)
                      ?.name ?? tx._displayTo)
                  : tx._displayTo

                return (
                  <tr
                    key={i}
                    className={`hover:bg-gray-50 ${isDuplicate ? 'bg-yellow-50' : ''} ${hasEdit ? 'border-l-2 border-l-blue-400' : ''}`}
                  >
                    <td className="px-4 py-2 text-gray-500">
                      <div className="flex items-center gap-1">
                        {tx.row_number}
                        {hasEdit && (
                          <button
                            onClick={() => resetTxEdit(tx.row_number)}
                            className="text-xs text-gray-400 hover:text-red-500"
                            title={t('import.resetRowEdit')}
                          >
                            ↩
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-2">{renderEditableCell(tx, 'date', 'date', 'w-28')}</td>
                    {!hasCategorySuggestions && (
                      <td className="px-4 py-2">{tx.transaction_type}</td>
                    )}
                    <td className="px-4 py-2">
                      {renderEditableCell(tx, 'description', 'text', 'w-40')}
                    </td>
                    <td className="px-4 py-2 text-right font-mono">
                      {renderEditableCell(tx, 'amount', 'number', 'w-24 text-right')}
                    </td>
                    {hasCategorySuggestions ? (
                      <>
                        <td
                          className="max-w-[150px] truncate px-4 py-2 text-xs"
                          title={tx.from_account_name}
                        >
                          {tx._displayFrom}
                        </td>
                        <td className="px-4 py-2">
                          <CategoryEditor
                            suggestion={tx.category_suggestion}
                            value={toDisplayName}
                            selectedAccountId={txEdits[tx.row_number]?.toAccountId}
                            accounts={expenseAccounts}
                            disabled={executing}
                            onChange={(accountId) =>
                              setTxEdits((prev) => ({
                                ...prev,
                                [tx.row_number]: { ...prev[tx.row_number], toAccountId: accountId },
                              }))
                            }
                          />
                        </td>
                      </>
                    ) : (
                      <>
                        <td
                          className="max-w-[150px] truncate px-4 py-2 text-xs"
                          title={tx.from_account_name}
                        >
                          {tx._displayFrom}
                        </td>
                        <td
                          className="max-w-[150px] truncate px-4 py-2 text-xs"
                          title={tx.to_account_name}
                        >
                          {tx._displayTo}
                        </td>
                      </>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Progress Indicator */}
      {executing && (
        <div className="rounded-lg border border-gray-100 bg-white p-6 shadow-sm">
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
          className="rounded border border-gray-300 bg-white px-6 py-2 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {t('common.cancel')}
        </button>
        <button
          onClick={handleExecute}
          disabled={executing}
          className={`rounded px-6 py-2 font-medium text-white ${
            executing ? 'cursor-not-allowed bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {executing ? t('import.importing') : t('import.confirmImport')}
        </button>
      </div>
    </div>
  )
}
