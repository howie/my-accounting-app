'use client'

import { useState, useEffect } from 'react'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCreateTag, useUpdateTag } from '@/lib/hooks/useTags'
import type { Tag } from '@/services/tags'

interface TagFormProps {
  initialData?: Tag
  onSuccess?: () => void
  onCancel?: () => void
}

export function TagForm({ initialData, onSuccess, onCancel }: TagFormProps) {
  const [name, setName] = useState(initialData?.name || '')
  const [color, setColor] = useState(initialData?.color || '#000000')
  const [error, setError] = useState<string | null>(null)
  const t = useTranslations('tags')

  const createTag = useCreateTag()
  const updateTag = useUpdateTag()

  const isEditing = !!initialData
  const isPending = createTag.isPending || updateTag.isPending

  useEffect(() => {
    if (initialData) {
      setName(initialData.name)
      setColor(initialData.color)
    }
  }, [initialData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError(t('form.nameRequired'))
      return
    }

    try {
      if (isEditing && initialData) {
        await updateTag.mutateAsync({
          id: initialData.id,
          data: { name: name.trim(), color },
        })
      } else {
        await createTag.mutateAsync({
          name: name.trim(),
          color,
        })
      }
      onSuccess?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('form.failedToSave'))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      )}

      <div className="space-y-2">
        <label htmlFor="name" className="text-sm font-medium">
          {t('form.nameLabel')}
        </label>
        <Input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t('form.namePlaceholder')}
          required
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="color" className="text-sm font-medium">
          {t('form.colorLabel')}
        </label>
        <div className="flex gap-2">
          <Input
            id="color"
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            className="h-10 w-20 cursor-pointer p-1"
          />
          <Input
            type="text"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            placeholder="#000000"
            pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
            className="flex-1"
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            {t('common.cancel')}
          </Button>
        )}
        <Button type="submit" disabled={isPending}>
          {isPending
            ? isEditing
              ? t('form.updating')
              : t('form.creating')
            : isEditing
              ? t('form.update')
              : t('form.create')}
        </Button>
      </div>
    </form>
  )
}
