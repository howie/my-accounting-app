/**
 * API client for LedgerOne backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface ApiErrorResponse {
  error: ApiError
}

export class ApiClientError extends Error {
  code: string
  details?: Record<string, unknown>
  status: number

  constructor(error: ApiError, status: number) {
    super(error.message)
    this.name = 'ApiClientError'
    this.code = error.code
    this.details = error.details
    this.status = status
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error. Please check your connection.') {
    super(message)
    this.name = 'NetworkError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    try {
      const errorData = (await response.json()) as ApiErrorResponse
      throw new ApiClientError(errorData.error, response.status)
    } catch (e) {
      if (e instanceof ApiClientError) {
        throw e
      }
      // JSON parsing failed, create generic error
      throw new ApiClientError(
        {
          code: 'UNKNOWN_ERROR',
          message: `Request failed with status ${response.status}`,
        },
        response.status
      )
    }
  }

  // Handle empty responses (204 No Content)
  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

async function fetchWithErrorHandling(url: string, options: RequestInit): Promise<Response> {
  try {
    return await fetch(url, options)
  } catch (error) {
    if (error instanceof TypeError) {
      // Network error (connection refused, DNS failure, etc.)
      throw new NetworkError()
    }
    throw error
  }
}

export async function apiGet<T>(endpoint: string): Promise<T> {
  const response = await fetchWithErrorHandling(`${API_BASE_URL}${endpoint}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })
  return handleResponse<T>(response)
}

export async function apiPost<T, D = unknown>(endpoint: string, data: D): Promise<T> {
  const response = await fetchWithErrorHandling(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return handleResponse<T>(response)
}

export async function apiPut<T, D = unknown>(endpoint: string, data: D): Promise<T> {
  const response = await fetchWithErrorHandling(`${API_BASE_URL}${endpoint}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return handleResponse<T>(response)
}

export async function apiPatch<T, D = unknown>(endpoint: string, data: D): Promise<T> {
  const response = await fetchWithErrorHandling(`${API_BASE_URL}${endpoint}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return handleResponse<T>(response)
}

export async function apiDelete(endpoint: string): Promise<void> {
  const response = await fetchWithErrorHandling(`${API_BASE_URL}${endpoint}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  })
  return handleResponse<void>(response)
}
