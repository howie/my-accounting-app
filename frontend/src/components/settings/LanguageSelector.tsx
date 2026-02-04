import { useTranslation } from 'react-i18next';
import { locales, localeNames, type Locale } from '@/i18n/config';
import { useUserPreferences } from '@/lib/hooks/useUserPreferences';

/**
 * Language selector component for Settings page.
 * Changes locale via i18next and persists preference to localStorage.
 */
export function LanguageSelector() {
  const { t, i18n } = useTranslation();
  const { preferences, setLanguage, isLoaded } = useUserPreferences();

  const handleLocaleChange = (newLocale: Locale) => {
    setLanguage(newLocale);
    i18n.changeLanguage(newLocale);
  };

  if (!isLoaded) {
    return (
      <div className="animate-pulse">
        <div className="h-10 w-48 rounded-md bg-muted" />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{t('settings.language')}</label>
      <div className="flex gap-2">
        {locales.map((locale) => (
          <button
            key={locale}
            type="button"
            onClick={() => handleLocaleChange(locale)}
            className={`rounded-md border px-4 py-2 text-sm transition-colors ${
              preferences.language === locale
                ? 'border-primary bg-primary text-primary-foreground'
                : 'border-border bg-background hover:bg-muted'
            }`}
          >
            {localeNames[locale]}
          </button>
        ))}
      </div>
    </div>
  );
}
