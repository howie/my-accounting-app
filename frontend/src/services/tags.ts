import { apiGet, apiPost, apiPut, apiDelete } from '@/lib/api'

export interface Tag {
  id: string
  name: string
  color: string
  created_at: string
}

export interface TagCreate {
  name: string
  color?: string
}

export interface TagUpdate {
  name?: string
  color?: string
}

export const tagService = {
  listTags: async (): Promise<Tag[]> => {
    return apiGet<Tag[]>('/tags')
  },

  createTag: async (data: TagCreate): Promise<Tag> => {
    return apiPost<Tag, TagCreate>('/tags', data)
  },

  updateTag: async (id: string, data: TagUpdate): Promise<Tag> => {
    return apiPut<Tag, TagUpdate>(`/tags/${id}`, data)
  },

  deleteTag: async (id: string): Promise<void> => {
    return apiDelete(`/tags/${id}`)
  },
}
