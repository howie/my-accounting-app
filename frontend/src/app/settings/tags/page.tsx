import { TagList } from '@/components/tags/TagList'
import { getTranslations } from 'next-intl/server'

export async function generateMetadata() {
  const t = await getTranslations('tags')
  return {
    title: t('title'),
  }
}

export default function TagsSettingsPage() {
  return (
    <div className="space-y-6">
      <TagList />
    </div>
  )
}
