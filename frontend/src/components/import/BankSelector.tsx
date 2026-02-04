

import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { importApi, BankConfig } from '@/lib/api/import'

interface BankSelectorProps {
    value: string | null
    onChange: (bankCode: string) => void
    disabled?: boolean
}

export default function BankSelector({ value, onChange, disabled }: BankSelectorProps) {
    const { t } = useTranslation(undefined, { keyPrefix: 'import' })
    const [banks, setBanks] = useState<BankConfig[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const fetchBanks = async () => {
            try {
                const response = await importApi.getBanks()
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
    }, [onChange, value])

    if (loading) {
        return (
            <div className="animate-pulse">
                <div className="h-10 bg-gray-200 rounded"></div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="text-red-600 text-sm">
                {error}
            </div>
        )
    }

    return (
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('selectBank')}
            </label>
            <select
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
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
