'use client'

import * as React from 'react'
import { Plus, X, Check } from 'lucide-react'
import { useTranslations } from 'next-intl'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useTags, useCreateTag } from '@/lib/hooks/useTags'
import { cn } from '@/lib/utils'

interface TagSelectProps {
  selectedTagIds: string[]
  onChange: (ids: string[]) => void
}

export function TagSelect({ selectedTagIds, onChange }: TagSelectProps) {
  const t = useTranslations('tags')
  const { data: tags = [] } = useTags()
  const createTag = useCreateTag()

  const [open, setOpen] = React.useState(false)
  const [search, setSearch] = React.useState('')
  const dropdownRef = React.useRef<HTMLDivElement>(null)

  // Handle clicking outside to close
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filteredTags = tags.filter(
    (tag) =>
      !selectedTagIds.includes(tag.id) &&
      tag.name.toLowerCase().includes(search.toLowerCase())
  )

  const selectedTags = tags.filter((tag) => selectedTagIds.includes(tag.id))

  const handleSelect = (id: string) => {
    onChange([...selectedTagIds, id])
    setSearch('')
    // Keep open for multiple selection? Or close? User preference.
    // Let's keep open but focus input
    document.getElementById('tag-search-input')?.focus()
  }

  const handleRemove = (id: string) => {
    onChange(selectedTagIds.filter((tid) => tid !== id))
  }

  const handleCreate = async () => {
    if (!search.trim()) return
    try {
      const newTag = await createTag.mutateAsync({
        name: search.trim(),
        color: '#808080', // Default color
      })
      handleSelect(newTag.id)
    } catch (e) {
      console.error('Failed to create tag', e)
    }
  }

  const exactMatch = tags.find(
    (tag) => tag.name.toLowerCase() === search.trim().toLowerCase()
  )

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {selectedTags.map((tag) => (
          <div
            key={tag.id}
            className="flex items-center gap-1 rounded-full border px-2 py-0.5 text-sm font-medium"
            style={{ backgroundColor: tag.color + '20', borderColor: tag.color }}
          >
            <span style={{ color: tag.color }}>{tag.name}</span>
            <button
              type="button"
              onClick={() => handleRemove(tag.id)}
              className="ml-1 rounded-full p-0.5 hover:bg-black/10"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-7 rounded-full px-3"
          onClick={() => setOpen(!open)}
        >
          <Plus className="mr-1 h-3 w-3" />
          {t('title')}
        </Button>
      </div>

      {open && (
        <div
          ref={dropdownRef}
          className="absolute z-50 mt-1 w-64 rounded-md border bg-popover p-1 shadow-md"
        >
          <Input
            id="tag-search-input"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('form.namePlaceholder')}
            className="h-8 text-xs"
            autoFocus
          />
          <div className="mt-1 max-h-48 overflow-y-auto">
            {filteredTags.map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => handleSelect(tag.id)}
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground"
              >
                <div
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: tag.color }}
                />
                {tag.name}
              </button>
            ))}
            {search.trim() && !exactMatch && (
              <button
                type="button"
                onClick={handleCreate}
                disabled={createTag.isPending}
                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-primary hover:bg-accent"
              >
                <Plus className="h-3 w-3" />
                {createTag.isPending ? t('form.creating') : `${t('form.create')} "${search}"`}
              </button>
            )}
            {filteredTags.length === 0 && !search && (
              <div className="px-2 py-2 text-xs text-muted-foreground text-center">
                {t('noTags')}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
