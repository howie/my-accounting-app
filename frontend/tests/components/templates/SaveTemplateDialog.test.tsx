/**
 * Tests for SaveTemplateDialog component.
 *
 * T069: Component test for SaveTemplateDialog
 * Per TDD: Write tests FIRST, ensure they FAIL, then implement.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextIntlClientProvider } from 'next-intl'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { SaveTemplateDialog } from '@/components/templates/SaveTemplateDialog'
import zhTW from '../../../messages/zh-TW.json'

// Mock useCreateTemplate hook
const mockCreateTemplate = vi.fn()
vi.mock('@/lib/hooks/useTemplates', () => ({
  useCreateTemplate: () => ({
    mutateAsync: mockCreateTemplate,
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

describe('SaveTemplateDialog', () => {
  const defaultProps = {
    ledgerId: 'ledger-123',
    open: true,
    onOpenChange: vi.fn(),
    templateData: {
      transaction_type: 'EXPENSE' as const,
      from_account_id: 'account-1',
      to_account_id: 'account-2',
      amount: 100,
      description: 'Test expense',
    },
    onSuccess: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders dialog with title when open', () => {
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByText(zhTW.templates.saveTemplate)).toBeInTheDocument()
    })

    it('does not render dialog when closed', () => {
      render(<SaveTemplateDialog {...defaultProps} open={false} />, { wrapper: createWrapper() })

      expect(screen.queryByText(zhTW.templates.saveTemplate)).not.toBeInTheDocument()
    })

    it('renders template name input field', () => {
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      const input = screen.getByTestId('template-name-input')
      expect(input).toBeInTheDocument()
    })

    it('renders save and cancel buttons', () => {
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByTestId('save-template-button')).toBeInTheDocument()
      expect(screen.getByTestId('cancel-template-button')).toBeInTheDocument()
    })
  })

  describe('Validation', () => {
    it('shows error when name is empty and save is clicked', async () => {
      const user = userEvent.setup()
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      await user.click(screen.getByTestId('save-template-button'))

      expect(screen.getByText(zhTW.validation.templateNameRequired)).toBeInTheDocument()
    })

    it('limits input to 50 characters via maxLength attribute', async () => {
      const user = userEvent.setup()
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      const longName = 'a'.repeat(60)
      await user.type(screen.getByTestId('template-name-input'), longName)

      // maxLength limits the input to 50 characters
      const input = screen.getByTestId('template-name-input') as HTMLInputElement
      expect(input.value.length).toBe(50)
    })

    it('clears error when user starts typing valid name', async () => {
      const user = userEvent.setup()
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      // Trigger error first
      await user.click(screen.getByTestId('save-template-button'))
      expect(screen.getByText(zhTW.validation.templateNameRequired)).toBeInTheDocument()

      // Type valid name
      await user.type(screen.getByTestId('template-name-input'), 'Valid Name')

      // Error should clear
      expect(screen.queryByText(zhTW.validation.templateNameRequired)).not.toBeInTheDocument()
    })
  })

  describe('Template Creation', () => {
    it('calls createTemplate with correct data when form is valid', async () => {
      const user = userEvent.setup()
      mockCreateTemplate.mockResolvedValueOnce({ id: 'template-1' })

      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      await user.type(screen.getByTestId('template-name-input'), 'Monthly Rent')
      await user.click(screen.getByTestId('save-template-button'))

      await waitFor(() => {
        expect(mockCreateTemplate).toHaveBeenCalledWith({
          name: 'Monthly Rent',
          transaction_type: 'EXPENSE',
          from_account_id: 'account-1',
          to_account_id: 'account-2',
          amount: 100,
          description: 'Test expense',
        })
      })
    })

    it('calls onSuccess after successful creation', async () => {
      const user = userEvent.setup()
      mockCreateTemplate.mockResolvedValueOnce({ id: 'template-1' })

      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      await user.type(screen.getByTestId('template-name-input'), 'Monthly Rent')
      await user.click(screen.getByTestId('save-template-button'))

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalled()
      })
    })

    it('calls onOpenChange(false) after successful creation', async () => {
      const user = userEvent.setup()
      mockCreateTemplate.mockResolvedValueOnce({ id: 'template-1' })

      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      await user.type(screen.getByTestId('template-name-input'), 'Monthly Rent')
      await user.click(screen.getByTestId('save-template-button'))

      await waitFor(() => {
        expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false)
      })
    })

    it('shows API error message on creation failure', async () => {
      const user = userEvent.setup()
      mockCreateTemplate.mockRejectedValueOnce(new Error('Template name already exists'))

      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      await user.type(screen.getByTestId('template-name-input'), 'Duplicate')
      await user.click(screen.getByTestId('save-template-button'))

      await waitFor(() => {
        expect(screen.getByText('Template name already exists')).toBeInTheDocument()
      })
    })
  })

  describe('Cancel Behavior', () => {
    it('calls onOpenChange(false) when cancel is clicked', async () => {
      const user = userEvent.setup()
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      await user.click(screen.getByTestId('cancel-template-button'))

      expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false)
    })

    it('clears form data when reopened', async () => {
      const user = userEvent.setup()
      const { rerender } = render(<SaveTemplateDialog {...defaultProps} />, {
        wrapper: createWrapper(),
      })

      // Type something
      await user.type(screen.getByTestId('template-name-input'), 'Test Name')

      // Close and reopen
      rerender(
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <NextIntlClientProvider locale="zh-TW" messages={zhTW}>
            <SaveTemplateDialog {...defaultProps} open={false} />
          </NextIntlClientProvider>
        </QueryClientProvider>
      )

      rerender(
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <NextIntlClientProvider locale="zh-TW" messages={zhTW}>
            <SaveTemplateDialog {...defaultProps} open={true} />
          </NextIntlClientProvider>
        </QueryClientProvider>
      )

      // Input should be cleared
      const input = screen.getByTestId('template-name-input') as HTMLInputElement
      expect(input.value).toBe('')
    })
  })

  describe('Accessibility', () => {
    it('has accessible dialog role', () => {
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('has accessible name input label', () => {
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      const input = screen.getByTestId('template-name-input')
      expect(input).toHaveAccessibleName()
    })

    it('focuses name input when dialog opens', async () => {
      render(<SaveTemplateDialog {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByTestId('template-name-input')).toHaveFocus()
      })
    })
  })
})
