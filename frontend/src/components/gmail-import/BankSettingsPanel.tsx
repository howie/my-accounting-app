'use client'

import { useCallback, useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { gmailImportApi, UserBankSettingResponse } from '@/lib/api/gmail-import'

interface BankSettingsPanelProps {
  ledgerId: string
}

export default function BankSettingsPanel({ ledgerId }: BankSettingsPanelProps) {
  const t = useTranslations('gmailImport')

  const [settings, setSettings] = useState<UserBankSettingResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [passwordInputs, setPasswordInputs] = useState<Record<string, string>>({})
  const [showPasswordFor, setShowPasswordFor] = useState<string | null>(null)

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true)
      const response = await gmailImportApi.getBankSettings(ledgerId)
      setSettings(response.settings)
    } catch {
      setError(t('bankSettings.fetchError'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  const handleToggleBank = async (bankCode: string, isEnabled: boolean) => {
    setSaving(bankCode)
    setError(null)
    try {
      await gmailImportApi.updateBankSettings(ledgerId, {
        bank_code: bankCode,
        is_enabled: isEnabled,
      })
      setSettings((prev) =>
        prev.map((s) => (s.bank_code === bankCode ? { ...s, is_enabled: isEnabled } : s))
      )
    } catch {
      setError(t('bankSettings.saveError'))
    } finally {
      setSaving(null)
    }
  }

  const handleSavePassword = async (bankCode: string) => {
    const password = passwordInputs[bankCode]
    if (!password) return

    setSaving(bankCode)
    setError(null)
    try {
      await gmailImportApi.updateBankSettings(ledgerId, {
        bank_code: bankCode,
        pdf_password: password,
      })
      setSettings((prev) =>
        prev.map((s) => (s.bank_code === bankCode ? { ...s, has_password: true } : s))
      )
      setPasswordInputs((prev) => ({ ...prev, [bankCode]: '' }))
      setShowPasswordFor(null)
    } catch {
      setError(t('bankSettings.saveError'))
    } finally {
      setSaving(null)
    }
  }

  const handleClearPassword = async (bankCode: string) => {
    setSaving(bankCode)
    setError(null)
    try {
      await gmailImportApi.updateBankSettings(ledgerId, {
        bank_code: bankCode,
        pdf_password: null,
      })
      setSettings((prev) =>
        prev.map((s) => (s.bank_code === bankCode ? { ...s, has_password: false } : s))
      )
    } catch {
      setError(t('bankSettings.saveError'))
    } finally {
      setSaving(null)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 rounded-lg bg-gray-200" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3">
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {settings.map((setting) => (
        <div key={setting.bank_code} className="rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={setting.is_enabled}
                  onChange={(e) => handleToggleBank(setting.bank_code, e.target.checked)}
                  disabled={saving === setting.bank_code}
                  className="peer sr-only"
                />
                <div className="peer h-5 w-9 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:ring-2 peer-focus:ring-blue-300" />
              </label>
              <div>
                <span className="font-medium text-gray-900">{setting.bank_name}</span>
                <span className="ml-2 text-sm text-gray-500">({setting.bank_code})</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {setting.has_password ? (
                <span className="flex items-center gap-1 text-xs text-green-600">
                  <svg
                    className="h-3.5 w-3.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                  {t('bankSettings.passwordSet')}
                </span>
              ) : (
                <span className="text-xs text-gray-400">{t('bankSettings.noPassword')}</span>
              )}
            </div>
          </div>

          {/* Password section */}
          {setting.is_enabled && (
            <div className="mt-3 border-t border-gray-100 pt-3">
              {showPasswordFor === setting.bank_code ? (
                <div className="flex items-center gap-2">
                  <input
                    type="password"
                    value={passwordInputs[setting.bank_code] || ''}
                    onChange={(e) =>
                      setPasswordInputs((prev) => ({
                        ...prev,
                        [setting.bank_code]: e.target.value,
                      }))
                    }
                    placeholder={t('bankSettings.passwordPlaceholder')}
                    className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    onClick={() => handleSavePassword(setting.bank_code)}
                    disabled={saving === setting.bank_code || !passwordInputs[setting.bank_code]}
                    className="rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {t('bankSettings.save')}
                  </button>
                  <button
                    onClick={() => {
                      setShowPasswordFor(null)
                      setPasswordInputs((prev) => ({
                        ...prev,
                        [setting.bank_code]: '',
                      }))
                    }}
                    className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                  >
                    {t('bankSettings.cancel')}
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowPasswordFor(setting.bank_code)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    {setting.has_password
                      ? t('bankSettings.changePassword')
                      : t('bankSettings.setPassword')}
                  </button>
                  {setting.has_password && (
                    <button
                      onClick={() => handleClearPassword(setting.bank_code)}
                      disabled={saving === setting.bank_code}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      {t('bankSettings.clearPassword')}
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
