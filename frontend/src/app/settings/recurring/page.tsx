import { RecurringList } from '@/components/recurring/RecurringList'
import { getTranslations } from 'next-intl/server'

export async function generateMetadata() {
  const t = await getTranslations('recurring')
  return {
    title: t('title'),
  }
}

export default function RecurringSettingsPage() {
  return (
    <div className="space-y-6">
      <RecurringList />
    </div>
  )
}
