

import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Pencil, Trash2, Check, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { TagForm } from './TagForm'
import { useTags, useDeleteTag } from '@/lib/hooks/useTags'
import type { Tag } from '@/services/tags'

export function TagList() {
  const { t } = useTranslation(undefined, { keyPrefix: 'tags' })
  const { data: tags, isLoading } = useTags()
  const deleteTag = useDeleteTag()

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingTag, setEditingTag] = useState<Tag | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (id: string) => {
    try {
      await deleteTag.mutateAsync(id)
      setDeletingId(null)
    } catch (err) {
      console.error('Failed to delete tag:', err)
    }
  }

  if (isLoading) {
    return <div className="p-4 text-center text-muted-foreground">{t('common.loading')}</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">{t('title')}</h2>
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {t('newTag')}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('form.create')}</DialogTitle>
            </DialogHeader>
            <TagForm
              onSuccess={() => setIsCreateOpen(false)}
              onCancel={() => setIsCreateOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border">
        {(!tags || tags.length === 0) ? (
          <div className="p-8 text-center text-muted-foreground">{t('noTags')}</div>
        ) : (
          <div className="divide-y">
            <div className="flex items-center bg-muted/50 px-4 py-3 text-sm font-medium">
              <div className="flex-1">{t('table.name')}</div>
              <div className="w-24">{t('table.color')}</div>
              <div className="w-32 text-right">{t('table.actions')}</div>
            </div>
            {tags.map((tag) => (
              <div key={tag.id} className="flex items-center px-4 py-3">
                <div className="flex flex-1 items-center gap-3">
                  <div
                    className="h-4 w-4 rounded-full border shadow-sm"
                    style={{ backgroundColor: tag.color }}
                  />
                  <span>{tag.name}</span>
                </div>
                <div className="w-24 font-mono text-xs text-muted-foreground">{tag.color}</div>
                <div className="flex w-32 justify-end gap-2">
                  {deletingId === tag.id ? (
                    <>
                      <Button
                        size="sm"
                        variant="destructive"
                        className="h-8 w-8 p-0"
                        onClick={() => handleDelete(tag.id)}
                        disabled={deleteTag.isPending}
                        title={t('common.confirm')}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 w-8 p-0"
                        onClick={() => setDeletingId(null)}
                        title={t('common.cancel')}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => setEditingTag(tag)}
                        title={t('templates.edit')}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => setDeletingId(tag.id)}
                        title={t('common.delete')}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={!!editingTag} onOpenChange={(open) => !open && setEditingTag(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('form.update')}</DialogTitle>
          </DialogHeader>
          <TagForm
            initialData={editingTag || undefined}
            onSuccess={() => setEditingTag(null)}
            onCancel={() => setEditingTag(null)}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
