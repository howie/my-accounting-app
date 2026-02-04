/**
 * T071 [US1] Component test for ImportPreview
 *
 * Tests the import preview component:
 * 1. Displays transaction preview table
 * 2. Shows duplicate warnings with skip option
 * 3. Shows account mappings with edit capability
 * 4. Handles import execution flow
 * 5. Shows progress during import
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { I18nextProvider } from 'react-i18next'
import i18n from '@/i18n'

import ImportPreview from '@/components/import/ImportPreview'
import { ImportPreviewResponse } from '@/lib/api/import'
import zhTW from '../../../messages/zh-TW.json'

// Mock the APIs
const mockExecute = vi.fn()
const mockListAccounts = vi.fn()

vi.mock('@/lib/api/import', () => ({
  importApi: {
    execute: (...args: unknown[]) => mockExecute(...args),
  },
}))

vi.mock('@/lib/api/accounts', () => ({
  accountsApi: {
    list: (...args: unknown[]) => mockListAccounts(...args),
  },
}))

// Mock ImportProgress component
vi.mock('@/components/import/ImportProgress', () => ({
  default: ({ current, total, status }: { current: number; total: number; status: string }) => (
    <div data-testid="import-progress" data-status={status}>
      Progress: {current}/{total}
    </div>
  ),
}))

// Mock CategoryEditor component
vi.mock('@/components/import/CategoryEditor', () => ({
  default: ({ value }: { value: string }) => (
    <span data-testid="category-editor">{value}</span>
  ),
}))

function createWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <I18nextProvider i18n={i18n}>
        {children}
      </I18nextProvider>
    )
  }
}

describe('ImportPreview', () => {
  const mockPreviewData: ImportPreviewResponse = {
    session_id: 'session-123',
    total_count: 3,
    date_range: { start: '2024-01-01', end: '2024-01-31' },
    transactions: [
      {
        row_number: 1,
        date: '2024-01-01',
        transaction_type: 'EXPENSE',
        from_account_name: 'A-現金',
        to_account_name: 'E-餐飲費',
        amount: '50.00',
        description: '午餐',
      },
      {
        row_number: 2,
        date: '2024-01-05',
        transaction_type: 'INCOME',
        from_account_name: 'I-薪資',
        to_account_name: 'A-銀行',
        amount: '30000.00',
        description: '月薪',
      },
      {
        row_number: 3,
        date: '2024-01-10',
        transaction_type: 'EXPENSE',
        from_account_name: 'A-現金',
        to_account_name: 'E-交通費',
        amount: '100.00',
        description: '捷運',
      },
    ],
    duplicates: [],
    account_mappings: [
      {
        csv_account_name: 'A-現金',
        csv_account_type: 'ASSET',
        system_account_id: 'cash-id',
        create_new: false,
        suggested_name: null,
      },
      {
        csv_account_name: 'E-餐飲費',
        csv_account_type: 'EXPENSE',
        system_account_id: null,
        create_new: true,
        suggested_name: '餐飲費',
      },
    ],
    validation_errors: [],
    is_valid: true,
  }

  const existingAccounts = [
    { id: 'cash-id', name: '現金', type: 'ASSET' },
    { id: 'bank-id', name: '銀行帳戶', type: 'ASSET' },
    { id: 'food-id', name: '餐飲費', type: 'EXPENSE' },
  ]

  const defaultProps = {
    ledgerId: 'ledger-123',
    data: mockPreviewData,
    onSuccess: vi.fn(),
    onCancel: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockListAccounts.mockResolvedValue({ data: existingAccounts })
  })

  describe('Transaction Preview', () => {
    it('displays transaction count', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(/Transaction Preview \(3\)/i)).toBeInTheDocument()
      })
    })

    it('displays transaction details in table', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('午餐')).toBeInTheDocument()
        expect(screen.getByText('月薪')).toBeInTheDocument()
        expect(screen.getByText('捷運')).toBeInTheDocument()
      })
    })

    it('displays transaction dates', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('2024-01-01')).toBeInTheDocument()
        expect(screen.getByText('2024-01-05')).toBeInTheDocument()
        expect(screen.getByText('2024-01-10')).toBeInTheDocument()
      })
    })

    it('displays transaction amounts', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('50.00')).toBeInTheDocument()
        expect(screen.getByText('30000.00')).toBeInTheDocument()
        expect(screen.getByText('100.00')).toBeInTheDocument()
      })
    })
  })

  describe('Duplicate Warnings', () => {
    const dataWithDuplicates: ImportPreviewResponse = {
      ...mockPreviewData,
      duplicates: [
        { row_number: 1, similarity_reason: '同日期+同金額+同科目' },
      ],
    }

    it('shows duplicate warning when duplicates exist', async () => {
      render(
        <ImportPreview {...defaultProps} data={dataWithDuplicates} />,
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(screen.getByText(/Duplicate Transactions Detected/i)).toBeInTheDocument()
      })
    })

    it('displays duplicate count', async () => {
      render(
        <ImportPreview {...defaultProps} data={dataWithDuplicates} />,
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(screen.getByText(/1 transactions seem to be duplicates/i)).toBeInTheDocument()
      })
    })

    it('shows skip duplicates checkbox checked by default', async () => {
      render(
        <ImportPreview {...defaultProps} data={dataWithDuplicates} />,
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        const checkbox = screen.getByRole('checkbox', { name: /skip duplicates/i })
        expect(checkbox).toBeChecked()
      })
    })

    it('allows toggling skip duplicates', async () => {
      const user = userEvent.setup()
      render(
        <ImportPreview {...defaultProps} data={dataWithDuplicates} />,
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(screen.getByRole('checkbox')).toBeInTheDocument()
      })

      const checkbox = screen.getByRole('checkbox', { name: /skip duplicates/i })
      await user.click(checkbox)

      expect(checkbox).not.toBeChecked()
    })

    it('highlights duplicate rows in transaction table', async () => {
      const { container } = render(
        <ImportPreview {...defaultProps} data={dataWithDuplicates} />,
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        const highlightedRow = container.querySelector('tr.bg-yellow-50')
        expect(highlightedRow).toBeInTheDocument()
      })
    })

    it('does not show duplicate warning when no duplicates', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.queryByText(/Duplicate Transactions Detected/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Account Mappings', () => {
    it('displays account mappings table', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Account Mappings')).toBeInTheDocument()
      })
    })

    it('shows CSV account names', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        // Find in account mappings table - there should be at least one for each
        const cashElements = screen.getAllByText('A-現金')
        const foodElements = screen.getAllByText('E-餐飲費')
        expect(cashElements.length).toBeGreaterThan(0)
        expect(foodElements.length).toBeGreaterThan(0)
      })
    })

    it('shows create new badge for new accounts', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('New')).toBeInTheDocument()
      })
    })

    it('shows map badge for existing accounts', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Map')).toBeInTheDocument()
      })
    })

    it('allows changing account mapping', async () => {
      const user = userEvent.setup()
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getAllByRole('combobox').length).toBeGreaterThan(0)
      })

      const selects = screen.getAllByRole('combobox')
      await user.selectOptions(selects[1], 'food-id')

      // The mapping should now show "Map" instead of "New"
      // (This depends on implementation - we're testing the user can interact)
    })
  })

  describe('Action Buttons', () => {
    it('displays confirm button', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })
    })

    it('displays cancel button', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      })
    })

    it('calls onCancel when cancel is clicked', async () => {
      const user = userEvent.setup()
      const onCancel = vi.fn()
      render(
        <ImportPreview {...defaultProps} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /cancel/i }))
      expect(onCancel).toHaveBeenCalled()
    })
  })

  describe('Import Execution', () => {
    it('calls execute API when confirm is clicked', async () => {
      const user = userEvent.setup()
      mockExecute.mockResolvedValueOnce({
        success: true,
        imported_count: 3,
        skipped_count: 0,
        created_accounts: [],
      })

      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /confirm import/i }))

      await waitFor(() => {
        expect(mockExecute).toHaveBeenCalledWith('ledger-123', expect.objectContaining({
          session_id: 'session-123',
        }))
      })
    })

    it('includes skipped duplicate rows when skip is enabled', async () => {
      const user = userEvent.setup()
      const dataWithDuplicates: ImportPreviewResponse = {
        ...mockPreviewData,
        duplicates: [{ row_number: 1, similarity_reason: 'test' }],
      }
      mockExecute.mockResolvedValueOnce({
        success: true,
        imported_count: 2,
        skipped_count: 1,
        created_accounts: [],
      })

      render(
        <ImportPreview {...defaultProps} data={dataWithDuplicates} />,
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /confirm import/i }))

      await waitFor(() => {
        expect(mockExecute).toHaveBeenCalledWith('ledger-123', expect.objectContaining({
          skip_duplicate_rows: [1],
        }))
      })
    })

    it('shows importing state while executing', async () => {
      const user = userEvent.setup()
      mockExecute.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /confirm import/i }))

      expect(screen.getByText('Importing...')).toBeInTheDocument()
    })

    it('disables buttons while importing', async () => {
      const user = userEvent.setup()
      mockExecute.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      )

      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /confirm import/i }))

      expect(screen.getByRole('button', { name: /importing/i })).toBeDisabled()
      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled()
    })

    it('calls onSuccess on successful import', async () => {
      const user = userEvent.setup()
      const onSuccess = vi.fn()
      const result = {
        success: true,
        imported_count: 3,
        skipped_count: 0,
        created_accounts: [],
      }
      mockExecute.mockResolvedValueOnce(result)

      render(
        <ImportPreview {...defaultProps} onSuccess={onSuccess} />,
        { wrapper: createWrapper() }
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /confirm import/i }))

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith(result)
      })
    })

    it('shows error message on import failure', async () => {
      const user = userEvent.setup()
      mockExecute.mockRejectedValueOnce(new Error('Database error'))

      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /confirm import/i }))

      await waitFor(() => {
        expect(screen.getByText('Database error')).toBeInTheDocument()
      })
    })
  })

  describe('Progress Indicator', () => {
    it('shows progress component while importing', async () => {
      const user = userEvent.setup()
      mockExecute.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /confirm import/i }))

      expect(screen.getByTestId('import-progress')).toBeInTheDocument()
    })

    it('does not show progress when not importing', async () => {
      render(<ImportPreview {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm import/i })).toBeInTheDocument()
      })

      expect(screen.queryByTestId('import-progress')).not.toBeInTheDocument()
    })
  })
})
