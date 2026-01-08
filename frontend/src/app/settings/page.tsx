'use client'

import { useTranslations } from 'next-intl'
import { LanguageSelector } from '@/components/settings/LanguageSelector'
import { ThemeToggle } from '@/components/settings/ThemeToggle'

/**
 * Settings page - displays language and theme preferences.
 */
export default function SettingsPage() {
  const t = useTranslations('settings')

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">{t('title')}</h1>

      <div className="max-w-md space-y-6">
        <LanguageSelector />
        <ThemeToggle />
      </div>
    </div>
  )
}
