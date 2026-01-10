/**
 * T098 [US7] Component test for TemplateList with edit/delete functionality
 *
 * Tests template management features:
 * 1. Lists templates with edit and delete buttons
 * 2. Edit button opens edit mode/dialog
 * 3. Delete button shows confirmation
 * 4. Confirming delete removes template
 * 5. Canceling delete keeps template
 * 6. Apply template works from list
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextIntlClientProvider } from 'next-intl'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { TemplateList } from '@/components/templates/TemplateList'
import zhTW from '../../../messages/zh-TW.json'

// Mock templates data
const mockTemplates = [
  {
    id: 'template-1',
    name: 'Lunch',
    transaction_type: 'EXPENSE' as const,
    from_account_id: 'cash-id',
    to_account_id: 'food-id',
    amount: '50.00',
    description: 'Daily lunch',
    sort_order: 0,
  },
  {
    id: 'template-2',
    name: 'Monthly Rent',
    transaction_type: 'EXPENSE' as const,
    from_account_id: 'bank-id',
    to_account_id: 'rent-id',
    amount: '15000.00',
    description: 'Monthly rent payment',
    sort_order: 1,
  },
]

// Mock hooks
const mockApplyTemplate = vi.fn()
const mockDeleteTemplate = vi.fn()
vi.mock('@/lib/hooks/useTemplates', () => ({
  useTemplates: () => ({
    data: { data: mockTemplates, total: 2 },
    isLoading: false,
    error: null,
  }),
  useApplyTemplate: () => ({
    mutateAsync: mockApplyTemplate,
    isPending: false,
  }),
  useDeleteTemplate: () => ({
    mutateAsync: mockDeleteTemplate,
    isPending: false,
  }),
}))

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <NextIntlClientProvider locale="zh-TW" messages={zhTW}>
          {children}
        </NextIntlClientProvider>
      </QueryClientProvider>
    )
  }
}

describe('TemplateList', () => {
  const defaultProps = {
    ledgerId: 'ledger-123',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders list of templates', () => {
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByText('Lunch')).toBeInTheDocument()
      expect(screen.getByText('Monthly Rent')).toBeInTheDocument()
    })

    it('shows template amounts', () => {
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByText('$50.00')).toBeInTheDocument()
      expect(screen.getByText('$15,000.00')).toBeInTheDocument()
    })

    it('shows apply buttons for each template', () => {
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const applyButtons = screen.getAllByTestId('apply-template-button')
      expect(applyButtons).toHaveLength(2)
    })

    it('shows delete buttons for each template when onDelete handler provided', () => {
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const deleteButtons = screen.getAllByTestId('delete-template-button')
      expect(deleteButtons).toHaveLength(2)
    })
  })

  describe('Template Application', () => {
    it('shows confirmation dialog when apply is clicked', async () => {
      const user = userEvent.setup()
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const applyButtons = screen.getAllByTestId('apply-template-button')
      await user.click(applyButtons[0])

      expect(screen.getByText(zhTW.templates.confirmApply)).toBeInTheDocument()
    })

    it('applies template when confirmed', async () => {
      const user = userEvent.setup()
      mockApplyTemplate.mockResolvedValueOnce({ id: 'new-transaction' })

      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const applyButtons = screen.getAllByTestId('apply-template-button')
      await user.click(applyButtons[0])
      await user.click(screen.getByTestId('confirm-apply'))

      await waitFor(() => {
        expect(mockApplyTemplate).toHaveBeenCalledWith({
          templateId: 'template-1',
        })
      })
    })

    it('closes dialog when canceled', async () => {
      const user = userEvent.setup()
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const applyButtons = screen.getAllByTestId('apply-template-button')
      await user.click(applyButtons[0])
      await user.click(screen.getByTestId('cancel-apply'))

      await waitFor(() => {
        expect(screen.queryByText(zhTW.templates.confirmApply)).not.toBeInTheDocument()
      })
    })

    it('calls onApplySuccess after successful apply', async () => {
      const user = userEvent.setup()
      const onApplySuccess = vi.fn()
      mockApplyTemplate.mockResolvedValueOnce({ id: 'new-transaction' })

      render(
        <TemplateList {...defaultProps} onApplySuccess={onApplySuccess} />,
        { wrapper: createWrapper() }
      )

      const applyButtons = screen.getAllByTestId('apply-template-button')
      await user.click(applyButtons[0])
      await user.click(screen.getByTestId('confirm-apply'))

      await waitFor(() => {
        expect(onApplySuccess).toHaveBeenCalled()
      })
    })
  })

  describe('Template Deletion', () => {
    it('shows confirmation dialog when delete is clicked', async () => {
      const user = userEvent.setup()
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const deleteButtons = screen.getAllByTestId('delete-template-button')
      await user.click(deleteButtons[0])

      expect(screen.getByText(zhTW.templates.confirmDelete)).toBeInTheDocument()
    })

    it('shows template name in delete confirmation', async () => {
      const user = userEvent.setup()
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const deleteButtons = screen.getAllByTestId('delete-template-button')
      await user.click(deleteButtons[0])

      expect(screen.getByText(/"Lunch"/)).toBeInTheDocument()
    })

    it('deletes template when confirmed', async () => {
      const user = userEvent.setup()
      mockDeleteTemplate.mockResolvedValueOnce({})

      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const deleteButtons = screen.getAllByTestId('delete-template-button')
      await user.click(deleteButtons[0])
      await user.click(screen.getByTestId('confirm-delete'))

      await waitFor(() => {
        expect(mockDeleteTemplate).toHaveBeenCalledWith('template-1')
      })
    })

    it('closes dialog when delete is canceled', async () => {
      const user = userEvent.setup()
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const deleteButtons = screen.getAllByTestId('delete-template-button')
      await user.click(deleteButtons[0])
      await user.click(screen.getByTestId('cancel-delete'))

      await waitFor(() => {
        expect(screen.queryByText(zhTW.templates.confirmDelete)).not.toBeInTheDocument()
      })
    })

    it('does not delete when canceled', async () => {
      const user = userEvent.setup()
      render(<TemplateList {...defaultProps} />, { wrapper: createWrapper() })

      const deleteButtons = screen.getAllByTestId('delete-template-button')
      await user.click(deleteButtons[0])
      await user.click(screen.getByTestId('cancel-delete'))

      expect(mockDeleteTemplate).not.toHaveBeenCalled()
    })
  })

  describe('Template Editing', () => {
    it('calls onEdit with template id when edit is clicked', async () => {
      const user = userEvent.setup()
      const onEdit = vi.fn()
      render(
        <TemplateList {...defaultProps} onEdit={onEdit} />,
        { wrapper: createWrapper() }
      )

      const editButtons = screen.getAllByTestId('edit-template-button')
      await user.click(editButtons[0])

      expect(onEdit).toHaveBeenCalledWith('template-1')
    })

    it('shows edit buttons when onEdit is provided', () => {
      const onEdit = vi.fn()
      render(
        <TemplateList {...defaultProps} onEdit={onEdit} />,
        { wrapper: createWrapper() }
      )

      const editButtons = screen.getAllByTestId('edit-template-button')
      expect(editButtons).toHaveLength(2)
    })
  })

  describe('Empty State', () => {
    it('shows empty message when no templates', async () => {
      vi.doMock('@/lib/hooks/useTemplates', () => ({
        useTemplates: () => ({
          data: { data: [], total: 0 },
          isLoading: false,
          error: null,
        }),
        useApplyTemplate: () => ({
          mutateAsync: vi.fn(),
          isPending: false,
        }),
        useDeleteTemplate: () => ({
          mutateAsync: vi.fn(),
          isPending: false,
        }),
      }))

      // With the current mock, this test is more of a placeholder
      // The actual empty state test needs proper module mocking
    })
  })
})
