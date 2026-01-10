'use client'

interface CategorySuggestion {
    suggested_account_id: string | null
    suggested_account_name: string
    confidence: number
    matched_keyword: string | null
}

interface CategoryEditorProps {
    suggestion: CategorySuggestion | null
    value: string
    onChange?: (category: string) => void
    disabled?: boolean
}

export default function CategoryEditor({
    suggestion,
    value,
}: CategoryEditorProps) {
    const confidence = suggestion?.confidence ?? 0
    const matchedKeyword = suggestion?.matched_keyword

    // Confidence indicator color
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
                className={`px-2 py-1 rounded text-sm border ${getConfidenceColor(confidence)}`}
                title={matchedKeyword ? `匹配關鍵字: ${matchedKeyword}` : undefined}
            >
                {value}
            </span>
            {suggestion && (
                <span
                    className={`text-xs px-1.5 py-0.5 rounded border ${getConfidenceColor(confidence)}`}
                    title={`信心度: ${Math.round(confidence * 100)}%`}
                >
                    {getConfidenceLabel(confidence)}
                </span>
            )}
        </div>
    )
}
