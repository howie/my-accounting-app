/**
 * Hook for fetching application version from the backend.
 */

import { useQuery } from '@tanstack/react-query'

interface HealthResponse {
  status: string
  version: string
}

// Health endpoint is at root level, not under /api/v1
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000'

async function fetchVersion(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) {
    throw new Error('Failed to fetch version')
  }
  const data: HealthResponse = await response.json()
  return data.version
}

export function useVersion() {
  return useQuery({
    queryKey: ['version'],
    queryFn: fetchVersion,
    staleTime: Infinity, // Version doesn't change during a session
    retry: 1,
  })
}
