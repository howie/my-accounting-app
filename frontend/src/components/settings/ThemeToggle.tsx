import { useTranslation } from 'react-i18next';
import { useTheme } from '@/lib/context/ThemeContext';
import { Sun, Moon, Monitor } from 'lucide-react';

type ThemeOption = 'light' | 'dark' | 'system';

interface ThemeButtonProps {
  theme: ThemeOption;
  currentTheme: string;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

function ThemeButton({ theme, currentTheme, onClick, icon, label }: ThemeButtonProps) {
  const isActive = currentTheme === theme;

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
  );
}

/**
 * Theme toggle component for Settings page.
 * Allows switching between light, dark, and system themes.
 */
export function ThemeToggle() {
  const { t } = useTranslation();
  const { theme, setTheme } = useTheme();

  const themes: { value: ThemeOption; icon: React.ReactNode; labelKey: string }[] = [
    { value: 'light', icon: <Sun className="h-4 w-4" />, labelKey: 'settings.themeLight' },
    { value: 'dark', icon: <Moon className="h-4 w-4" />, labelKey: 'settings.themeDark' },
    { value: 'system', icon: <Monitor className="h-4 w-4" />, labelKey: 'settings.themeSystem' },
  ];

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{t('settings.theme')}</label>
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
  );
}
