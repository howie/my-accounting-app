'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiGet, apiPost } from '@/lib/api'
import type { User, UserSetup } from '@/types'

const USER_KEY = 'user'

export interface UserStatus {
  setup_needed: boolean
}

export function useUserStatus() {
  return useQuery({
    queryKey: [USER_KEY, 'status'],
    queryFn: async () => {
      return apiGet<UserStatus>('/users/status')
    },
  })
}

export function useCurrentUser() {
  return useQuery({
    queryKey: [USER_KEY, 'me'],
    queryFn: async () => {
      return apiGet<User>('/users/me')
    },
  })
}

export function useSetupUser() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: UserSetup) => {
      return apiPost<User>('/users/setup', data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [USER_KEY] })
    },
  })
}
