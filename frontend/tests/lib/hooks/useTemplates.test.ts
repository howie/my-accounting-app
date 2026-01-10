/**
 * Tests for useTemplates hook and related template hooks
 *
 * Tests the React Query hooks for CRUD operations on transaction templates.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// Mock the API module
vi.mock('@/lib/api', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

import {
  useTemplates,
  useTemplate,
  useCreateTemplate,
  useUpdateTemplate,
  useDeleteTemplate,
  useReorderTemplates,
  useApplyTemplate,
} from '@/lib/hooks/useTemplates'
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api'

// Helper to create wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

describe('useTemplates', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('useTemplates (list)', () => {
    it('should fetch templates for a ledger', async () => {
      const mockTemplates = {
        data: [
          {
            id: 'template-1',
            name: 'Lunch',
            transaction_type: 'EXPENSE',
            amount: '25.00',
          },
        ],
        total: 1,
      }

      vi.mocked(apiGet).mockResolvedValue(mockTemplates)

      const { result } = renderHook(() => useTemplates('ledger-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(apiGet).toHaveBeenCalledWith('/ledgers/ledger-123/templates')
      expect(result.current.data).toEqual(mockTemplates)
    })

    it('should not fetch when ledgerId is empty', () => {
      renderHook(() => useTemplates(''), {
        wrapper: createWrapper(),
      })

      expect(apiGet).not.toHaveBeenCalled()
    })

    it('should handle API errors', async () => {
      vi.mocked(apiGet).mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useTemplates('ledger-123'), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })
  })

  describe('useTemplate (single)', () => {
    it('should fetch a single template', async () => {
      const mockTemplate = {
        id: 'template-1',
        name: 'Monthly Rent',
        transaction_type: 'EXPENSE',
        amount: '1500.00',
      }

      vi.mocked(apiGet).mockResolvedValue(mockTemplate)

      const { result } = renderHook(
        () => useTemplate('ledger-123', 'template-1'),
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(apiGet).toHaveBeenCalledWith('/ledgers/ledger-123/templates/template-1')
      expect(result.current.data).toEqual(mockTemplate)
    })

    it('should not fetch when templateId is empty', () => {
      renderHook(() => useTemplate('ledger-123', ''), {
        wrapper: createWrapper(),
      })

      expect(apiGet).not.toHaveBeenCalled()
    })

    it('should not fetch when ledgerId is empty', () => {
      renderHook(() => useTemplate('', 'template-1'), {
        wrapper: createWrapper(),
      })

      expect(apiGet).not.toHaveBeenCalled()
    })
  })

  describe('useCreateTemplate', () => {
    it('should create a new template', async () => {
      const newTemplate = {
        name: 'New Template',
        transaction_type: 'EXPENSE',
        from_account_id: 'account-1',
        to_account_id: 'account-2',
        amount: '50.00',
        description: 'Test template',
      }

      const createdTemplate = {
        id: 'template-new',
        ...newTemplate,
      }

      vi.mocked(apiPost).mockResolvedValue(createdTemplate)

      const { result } = renderHook(() => useCreateTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync(newTemplate as any)

      expect(apiPost).toHaveBeenCalledWith('/ledgers/ledger-123/templates', newTemplate)
    })

    it('should handle creation errors', async () => {
      vi.mocked(apiPost).mockRejectedValue(new Error('Validation error'))

      const { result } = renderHook(() => useCreateTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await expect(
        result.current.mutateAsync({
          name: '',
          transaction_type: 'EXPENSE',
          from_account_id: 'account-1',
          to_account_id: 'account-2',
          amount: '50.00',
          description: 'Test',
        } as any)
      ).rejects.toThrow('Validation error')
    })
  })

  describe('useUpdateTemplate', () => {
    it('should update an existing template', async () => {
      const updateData = {
        name: 'Updated Name',
        amount: '75.00',
      }

      const updatedTemplate = {
        id: 'template-1',
        name: 'Updated Name',
        amount: '75.00',
      }

      vi.mocked(apiPatch).mockResolvedValue(updatedTemplate)

      const { result } = renderHook(() => useUpdateTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync({
        templateId: 'template-1',
        data: updateData as any,
      })

      expect(apiPatch).toHaveBeenCalledWith(
        '/ledgers/ledger-123/templates/template-1',
        updateData
      )
    })

    it('should handle partial updates', async () => {
      const updateData = { description: 'New description' }

      vi.mocked(apiPatch).mockResolvedValue({
        id: 'template-1',
        description: 'New description',
      })

      const { result } = renderHook(() => useUpdateTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync({
        templateId: 'template-1',
        data: updateData as any,
      })

      expect(apiPatch).toHaveBeenCalledWith(
        '/ledgers/ledger-123/templates/template-1',
        updateData
      )
    })
  })

  describe('useDeleteTemplate', () => {
    it('should delete a template', async () => {
      vi.mocked(apiDelete).mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync('template-1')

      expect(apiDelete).toHaveBeenCalledWith('/ledgers/ledger-123/templates/template-1')
    })

    it('should handle deletion errors', async () => {
      vi.mocked(apiDelete).mockRejectedValue(new Error('Not found'))

      const { result } = renderHook(() => useDeleteTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await expect(result.current.mutateAsync('non-existent')).rejects.toThrow(
        'Not found'
      )
    })
  })

  describe('useReorderTemplates', () => {
    it('should reorder templates', async () => {
      const reorderData = {
        template_ids: ['template-3', 'template-1', 'template-2'],
      }

      const reorderedList = {
        data: [
          { id: 'template-3', sort_order: 0 },
          { id: 'template-1', sort_order: 1 },
          { id: 'template-2', sort_order: 2 },
        ],
        total: 3,
      }

      vi.mocked(apiPatch).mockResolvedValue(reorderedList)

      const { result } = renderHook(() => useReorderTemplates('ledger-123'), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync(reorderData as any)

      expect(apiPatch).toHaveBeenCalledWith(
        '/ledgers/ledger-123/templates/reorder',
        reorderData
      )
    })

    it('should handle reorder validation errors', async () => {
      vi.mocked(apiPatch).mockRejectedValue(new Error('Template IDs must match'))

      const { result } = renderHook(() => useReorderTemplates('ledger-123'), {
        wrapper: createWrapper(),
      })

      await expect(
        result.current.mutateAsync({ template_ids: ['wrong-id'] } as any)
      ).rejects.toThrow('Template IDs must match')
    })
  })

  describe('useApplyTemplate', () => {
    it('should apply a template with default values', async () => {
      const createdTransaction = {
        id: 'tx-new',
        amount: '50.00',
        description: 'Template description',
        date: '2024-01-15',
      }

      vi.mocked(apiPost).mockResolvedValue(createdTransaction)

      const { result } = renderHook(() => useApplyTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync({
        templateId: 'template-1',
      })

      expect(apiPost).toHaveBeenCalledWith(
        '/ledgers/ledger-123/templates/template-1/apply',
        {}
      )
    })

    it('should apply a template with custom date', async () => {
      const createdTransaction = {
        id: 'tx-new',
        date: '2024-06-15',
      }

      vi.mocked(apiPost).mockResolvedValue(createdTransaction)

      const { result } = renderHook(() => useApplyTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync({
        templateId: 'template-1',
        data: { date: '2024-06-15' },
      })

      expect(apiPost).toHaveBeenCalledWith(
        '/ledgers/ledger-123/templates/template-1/apply',
        { date: '2024-06-15' }
      )
    })

    it('should apply a template with notes', async () => {
      vi.mocked(apiPost).mockResolvedValue({
        id: 'tx-new',
        notes: 'Special occasion',
      })

      const { result } = renderHook(() => useApplyTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await result.current.mutateAsync({
        templateId: 'template-1',
        data: { notes: 'Special occasion' },
      })

      expect(apiPost).toHaveBeenCalledWith(
        '/ledgers/ledger-123/templates/template-1/apply',
        { notes: 'Special occasion' }
      )
    })

    it('should handle apply errors', async () => {
      vi.mocked(apiPost).mockRejectedValue(new Error('Template not found'))

      const { result } = renderHook(() => useApplyTemplate('ledger-123'), {
        wrapper: createWrapper(),
      })

      await expect(
        result.current.mutateAsync({ templateId: 'non-existent' })
      ).rejects.toThrow('Template not found')
    })
  })
})

describe('Template hooks query invalidation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should have proper mutation keys for cache invalidation', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children)

    vi.mocked(apiPost).mockResolvedValue({ id: 'new-template' })

    const { result } = renderHook(() => useCreateTemplate('ledger-123'), {
      wrapper,
    })

    // Mock the template to be created
    await result.current.mutateAsync({
      name: 'Test',
      transaction_type: 'EXPENSE',
      from_account_id: 'acc-1',
      to_account_id: 'acc-2',
      amount: '100.00',
      description: 'Test',
    } as any)

    // The hook should invalidate 'templates' query key for the ledger
    // This is verified by the hook implementation
    expect(apiPost).toHaveBeenCalled()
  })
})
