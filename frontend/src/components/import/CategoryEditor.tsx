import { useTranslation } from 'react-i18next'
import { AccountListItem } from '@/lib/api/accounts'

export function buildHierarchicalAccountOptions(
  accounts: AccountListItem[]
): Array<{ id: string; displayName: string }> {
  const accountMap = new Map(accounts.map((a) => [a.id, a]))

  const getFullPath = (acc: AccountListItem): string => {
    const parts: string[] = [acc.name]
    let current = acc
    while (current.parent_id) {
      const parent = accountMap.get(current.parent_id)
      if (!parent) break
      parts.unshift(parent.name)
      current = parent
    }
    return parts.join(' - ')
  }

  const accountIds = new Set(accounts.map((a) => a.id))
  const childrenMap = new Map<string, AccountListItem[]>()
  const roots: AccountListItem[] = []

  for (const acc of accounts) {
    if (!acc.parent_id || !accountIds.has(acc.parent_id)) {
      roots.push(acc)
    } else {
      if (!childrenMap.has(acc.parent_id)) childrenMap.set(acc.parent_id, [])
      childrenMap.get(acc.parent_id)!.push(acc)
    }
  }

  roots.sort((a, b) => a.sort_order - b.sort_order)
  for (const children of childrenMap.values()) {
    children.sort((a, b) => a.sort_order - b.sort_order)
  }

  const result: Array<{ id: string; displayName: string }> = []
  const dfs = (acc: AccountListItem) => {
    result.push({ id: acc.id, displayName: getFullPath(acc) })
    for (const child of childrenMap.get(acc.id) ?? []) dfs(child)
  }
  for (const root of roots) dfs(root)

  return result
}

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
          {buildHierarchicalAccountOptions(accounts).map((opt) => (
            <option key={opt.id} value={opt.id}>
              {opt.displayName}
            </option>
          ))}
        </select>
      )}
    </div>
  )
}
