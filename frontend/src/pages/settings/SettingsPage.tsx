import { useTranslation } from 'react-i18next'
import { LanguageSelector } from '@/components/settings/LanguageSelector'
import { ThemeToggle } from '@/components/settings/ThemeToggle'
import { DangerZone } from '@/components/settings/DangerZone'
import { useLedgerContext } from '@/lib/context/LedgerContext'

/**
 * Settings page - displays language and theme preferences.
 */
export default function SettingsPage() {
  const { t } = useTranslation()
  const { currentLedger } = useLedgerContext()

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">{t('title')}</h1>

      <div className="max-w-md space-y-6">
        <LanguageSelector />
        <ThemeToggle />
      </div>

      {currentLedger && (
        <div className="mt-8">
          <DangerZone ledgerId={currentLedger.id} />
        </div>
      )}
    </div>
  )
}
