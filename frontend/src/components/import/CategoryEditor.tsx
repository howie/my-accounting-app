import { useTranslation } from 'react-i18next'
import { AccountListItem } from '@/lib/api/accounts'

interface CategorySuggestion {
  suggested_account_id: string | null
  suggested_account_name: string
  confidence: number
  matched_keyword: string | null
}

interface CategoryEditorProps {
  suggestion: CategorySuggestion | null
  value: string
  onChange?: (accountId: string) => void
  accounts?: AccountListItem[]
  selectedAccountId?: string
  disabled?: boolean
}

export default function CategoryEditor({
  suggestion,
  value,
  onChange,
  accounts,
  selectedAccountId,
  disabled,
}: CategoryEditorProps) {
  const { t } = useTranslation()
  const confidence = suggestion?.confidence ?? 0
  const matchedKeyword = suggestion?.matched_keyword

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return 'text-green-600 bg-green-50 border-green-200'
    if (conf >= 0.5) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-gray-500 bg-gray-50 border-gray-200'
  }

  const getConfidenceLabel = (conf: number) => {
    if (conf >= 0.8) return '高'
    if (conf >= 0.5) return '中'
    return '低'
  }

  return (
    <div className="flex items-center space-x-2">
      <span
        className={`rounded border px-2 py-1 text-sm ${getConfidenceColor(confidence)}`}
        title={matchedKeyword ? `匹配關鍵字: ${matchedKeyword}` : undefined}
      >
        {value}
      </span>
      {suggestion && (
        <span
          className={`rounded border px-1.5 py-0.5 text-xs ${getConfidenceColor(confidence)}`}
          title={`信心度: ${Math.round(confidence * 100)}%`}
        >
          {getConfidenceLabel(confidence)}
        </span>
      )}
      {onChange && accounts && accounts.length > 0 && (
        <select
          disabled={disabled}
          value={selectedAccountId || ''}
          onChange={(e) => e.target.value && onChange(e.target.value)}
          className="rounded border border-gray-300 bg-white px-2 py-1 text-xs"
        >
          <option value="">{t('import.overrideCategory')}</option>
          {accounts.map((acc) => (
            <option key={acc.id} value={acc.id}>
              {acc.name}
            </option>
          ))}
        </select>
      )}
    </div>
  )
}
