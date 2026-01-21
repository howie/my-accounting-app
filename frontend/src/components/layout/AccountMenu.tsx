'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { useTheme } from 'next-themes'
import { Settings, Sun, Moon, Monitor, Languages, User } from 'lucide-react'
import { locales, localeNames, type Locale } from '@/i18n/config'
import { useUserPreferences } from '@/lib/hooks/useUserPreferences'

const LOCALE_COOKIE = 'NEXT_LOCALE'

export function AccountMenu() {
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const t = useTranslations('settings')
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const { preferences, setLanguage } = useUserPreferences()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLocaleChange = (newLocale: Locale) => {
    setLanguage(newLocale)
    document.cookie = `${LOCALE_COOKIE}=${newLocale}; path=/; max-age=31536000; SameSite=Lax`
    router.refresh()
  }

  const themes = [
    { value: 'light' as const, icon: Sun, labelKey: 'themeLight' },
    { value: 'dark' as const, icon: Moon, labelKey: 'themeDark' },
    { value: 'system' as const, icon: Monitor, labelKey: 'themeSystem' },
  ]

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-9 w-9 items-center justify-center rounded-full border bg-muted transition-colors hover:bg-accent"
        aria-label="Account menu"
      >
        <User className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-md border bg-background shadow-lg">
          {/* Theme Section */}
          <div className="border-b p-3">
            <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Sun className="h-3 w-3" />
              {t('theme')}
            </div>
            <div className="flex gap-1">
              {mounted &&
                themes.map(({ value, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => setTheme(value)}
                    className={`flex flex-1 items-center justify-center rounded-md p-2 text-xs transition-colors ${
                      theme === value ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                    }`}
                    title={t(themes.find((th) => th.value === value)?.labelKey || '')}
                  >
                    <Icon className="h-4 w-4" />
                  </button>
                ))}
            </div>
          </div>

          {/* Language Section */}
          <div className="border-b p-3">
            <div className="mb-2 flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Languages className="h-3 w-3" />
              {t('language')}
            </div>
            <div className="flex gap-1">
              {locales.map((locale) => (
                <button
                  key={locale}
                  onClick={() => handleLocaleChange(locale)}
                  className={`flex-1 rounded-md px-2 py-1.5 text-xs transition-colors ${
                    preferences.language === locale
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  {localeNames[locale]}
                </button>
              ))}
            </div>
          </div>

          {/* Settings Link */}
          <div className="p-2">
            <Link
              href="/settings"
              onClick={() => setIsOpen(false)}
              className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm transition-colors hover:bg-muted"
            >
              <Settings className="h-4 w-4" />
              {t('title')}
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
