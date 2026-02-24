import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { importApi, BankConfig } from '@/lib/api/import'

interface BankSelectorProps {
  value: string | null
  onChange: (bankCode: string) => void
  disabled?: boolean
  statementType?: string
}

export default function BankSelector({
  value,
  onChange,
  disabled,
  statementType = 'CREDIT_CARD',
}: BankSelectorProps) {
  const { t } = useTranslation(undefined, { keyPrefix: 'import' })
  const [banks, setBanks] = useState<BankConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchBanks = async () => {
      try {
        const response = await importApi.getBanks(statementType)
        setBanks(response.banks)
        // Auto-select first bank if none selected
        if (!value && response.banks.length > 0) {
          onChange(response.banks[0].code)
        }
      } catch (err) {
        console.error('Failed to fetch banks:', err)
        setError('Failed to load banks')
      } finally {
        setLoading(false)
      }
    }
    fetchBanks()
  }, [onChange, value, statementType])

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-10 rounded bg-gray-200"></div>
      </div>
    )
  }

  if (error) {
    return <div className="text-sm text-red-600">{error}</div>
  }

  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-gray-700">{t('selectBank')}</label>
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-100"
      >
        <option value="" disabled>
          -- {t('selectBank')} --
        </option>
        {banks.map((bank) => (
          <option key={bank.code} value={bank.code}>
            {bank.name}
          </option>
        ))}
      </select>
    </div>
  )
}
