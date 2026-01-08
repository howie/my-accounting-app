'use client'

import { useTranslations } from 'next-intl'
import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'
import { Sun, Moon, Monitor } from 'lucide-react'

type ThemeOption = 'light' | 'dark' | 'system'

interface ThemeButtonProps {
  theme: ThemeOption
  currentTheme: string | undefined
  onClick: () => void
  icon: React.ReactNode
  label: string
}

function ThemeButton({ theme, currentTheme, onClick, icon, label }: ThemeButtonProps) {
  const isActive = currentTheme === theme

  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 rounded-md border px-4 py-2 text-sm transition-colors ${
        isActive
          ? 'border-primary bg-primary text-primary-foreground'
          : 'border-border bg-background hover:bg-muted'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  )
}

/**
 * Theme toggle component for Settings page.
 * Allows switching between light, dark, and system themes.
 */
export function ThemeToggle() {
  const t = useTranslations('settings')
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  // Avoid hydration mismatch
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="animate-pulse">
        <div className="h-10 w-64 rounded-md bg-muted" />
      </div>
    )
  }

  const themes: { value: ThemeOption; icon: React.ReactNode; labelKey: string }[] = [
    { value: 'light', icon: <Sun className="h-4 w-4" />, labelKey: 'themeLight' },
    { value: 'dark', icon: <Moon className="h-4 w-4" />, labelKey: 'themeDark' },
    { value: 'system', icon: <Monitor className="h-4 w-4" />, labelKey: 'themeSystem' },
  ]

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{t('theme')}</label>
      <div className="flex gap-2">
        {themes.map(({ value, icon, labelKey }) => (
          <ThemeButton
            key={value}
            theme={value}
            currentTheme={theme}
            onClick={() => setTheme(value)}
            icon={icon}
            label={t(labelKey)}
          />
        ))}
      </div>
    </div>
  )
}
