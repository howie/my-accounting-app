import { SettingsNav } from '@/components/settings/SettingsNav'

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-8 p-6">
      <SettingsNav />
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  )
}
