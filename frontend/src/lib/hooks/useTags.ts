

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { tagService } from '@/services/tags'
import type { TagCreate, TagUpdate } from '@/services/tags'

const TAGS_KEY = ['tags']

export function useTags() {
  return useQuery({
    queryKey: TAGS_KEY,
    queryFn: tagService.listTags,
  })
}

export function useCreateTag() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: TagCreate) => tagService.createTag(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_KEY })
    },
  })
}

export function useUpdateTag() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TagUpdate }) =>
      tagService.updateTag(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_KEY })
    },
  })
}

export function useDeleteTag() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => tagService.deleteTag(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TAGS_KEY })
    },
  })
}
