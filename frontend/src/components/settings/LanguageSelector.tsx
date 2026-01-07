'use client'

import { useTranslations } from 'next-intl'
import { useRouter } from 'next/navigation'
import { locales, localeNames, type Locale } from '@/i18n/config'
import { useUserPreferences } from '@/lib/hooks/useUserPreferences'

const LOCALE_COOKIE = 'NEXT_LOCALE'

/**
 * Language selector component for Settings page.
 * Changes locale via cookie and persists preference to localStorage.
 */
export function LanguageSelector() {
  const t = useTranslations('settings')
  const router = useRouter()
  const { preferences, setLanguage, isLoaded } = useUserPreferences()

  const handleLocaleChange = (newLocale: Locale) => {
    // Update localStorage preference
    setLanguage(newLocale)

    // Set cookie for next-intl server-side reading
    document.cookie = `${LOCALE_COOKIE}=${newLocale}; path=/; max-age=31536000; SameSite=Lax`

    // Refresh the page to apply new locale
    router.refresh()
  }

  if (!isLoaded) {
    return (
      <div className="animate-pulse">
        <div className="h-10 w-48 bg-muted rounded-md" />
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{t('language')}</label>
      <div className="flex gap-2">
        {locales.map((locale) => (
          <button
            key={locale}
            type="button"
            onClick={() => handleLocaleChange(locale)}
            className={`px-4 py-2 text-sm rounded-md border transition-colors ${
              preferences.language === locale
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-background border-border hover:bg-muted'
            }`}
          >
            {localeNames[locale]}
          </button>
        ))}
      </div>
    </div>
  )
}
