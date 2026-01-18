/**
 * T018 [US1] Component test for TransactionForm
 * T018A [US1] Edge case test for zero-amount confirmation dialog
 *
 * Tests the transaction form component:
 * 1. Form renders with all required fields
 * 2. Transaction type selection updates account lists
 * 3. Form validation (description required, valid amount, different accounts)
 * 4. Successful submission calls createTransaction
 * 5. Notes field support
 * 6. Amount expression evaluation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock next-intl
vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => {
    const translations: Record<string, string> = {
      'transactionForm.title': 'New Transaction',
      'transactionForm.typeLabel': 'Transaction Type',
      'transactionForm.dateLabel': 'Date',
      'transactionForm.descriptionLabel': 'Description',
      'transactionForm.descriptionPlaceholder': 'Enter description',
      'transactionForm.amountLabel': 'Amount',
      'transactionForm.fromAccountLabel': 'From Account',
      'transactionForm.toAccountLabel': 'To Account',
      'transactionForm.selectAccount': 'Select account',
      'transactionForm.saveTransaction': 'Save',
      'transactionForm.saving': 'Saving...',
      'transactionForm.invalidAmount': 'Invalid amount',
      'transactionForm.accountsRequired': 'Both accounts are required',
      'transactionForm.failedToCreate': 'Failed to create transaction',
      'transactionTypes.EXPENSE': 'Expense',
      'transactionTypes.INCOME': 'Income',
      'transactionTypes.TRANSFER': 'Transfer',
      'transactionTypes.expenseDesc': 'Money out',
      'transactionTypes.incomeDesc': 'Money in',
      'transactionTypes.transferDesc': 'Move between accounts',
      'accountTypes.ASSET': 'Asset',
      'accountTypes.LIABILITY': 'Liability',
      'accountTypes.INCOME': 'Income',
      'accountTypes.EXPENSE': 'Expense',
      'common.cancel': 'Cancel',
      'transactionEntry.notes': 'Notes',
      'transactionEntry.notesPlaceholder': 'Optional notes',
      'transactionEntry.expressionHint': 'Enter expression',
      'validation.descriptionRequired': 'Description is required',
      'validation.descriptionTooLong': 'Description too long',
      'validation.amountRequired': 'Amount is required',
      'validation.sameAccountError': 'Same account error',
      'validation.notesTooLong': 'Notes too long',
    }
    return translations[key] || key
  },
}))

// Mock accounts data with proper Account structure
const mockAccounts = [
  {
    id: 'cash-id',
    ledger_id: 'test-ledger',
    name: 'Cash',
    type: 'ASSET' as const,
    balance: '1000.00',
    is_system: false,
    parent_id: null,
    depth: 0,
    sort_order: 0,
    has_children: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
  {
    id: 'bank-id',
    ledger_id: 'test-ledger',
    name: 'Bank',
    type: 'ASSET' as const,
    balance: '5000.00',
    is_system: false,
    parent_id: null,
    depth: 0,
    sort_order: 1,
    has_children: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
  {
    id: 'salary-id',
    ledger_id: 'test-ledger',
    name: 'Salary',
    type: 'INCOME' as const,
    balance: '0.00',
    is_system: false,
    parent_id: null,
    depth: 0,
    sort_order: 0,
    has_children: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
  {
    id: 'food-id',
    ledger_id: 'test-ledger',
    name: 'Food',
    type: 'EXPENSE' as const,
    balance: '0.00',
    is_system: false,
    parent_id: null,
    depth: 0,
    sort_order: 0,
    has_children: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
  {
    id: 'credit-id',
    ledger_id: 'test-ledger',
    name: 'Credit Card',
    type: 'LIABILITY' as const,
    balance: '0.00',
    is_system: false,
    parent_id: null,
    depth: 0,
    sort_order: 0,
    has_children: false,
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
]

// Mock useAccounts hook
vi.mock('@/lib/hooks/useAccounts', () => ({
  useAccounts: () => ({
    data: mockAccounts,
    isLoading: false,
    error: null,
  }),
}))

// Mock createTransaction mutation
const mockMutateAsync = vi.fn()
vi.mock('@/lib/hooks/useTransactions', () => ({
  useCreateTransaction: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  }),
}))

// Mock useTemplates hook (needed for SaveTemplateDialog)
vi.mock('@/lib/hooks/useTemplates', () => ({
  useCreateTemplate: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}))

// Mock useTags hook
vi.mock('@/lib/hooks/useTags', () => ({
  useTags: () => ({
    data: [
      { id: 'tag-1', name: 'Vacation', color: '#ff0000' },
      { id: 'tag-2', name: 'Work', color: '#00ff00' },
    ],
    isLoading: false,
  }),
  useCreateTag: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}))

// Import after mocks
import { TransactionForm } from '@/components/transactions/TransactionForm'

describe('TransactionForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockMutateAsync.mockResolvedValue({ id: 'new-transaction-id' })
  })

  describe('rendering', () => {
    it('should render all form fields', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      expect(screen.getByText('Transaction Type')).toBeInTheDocument()
      expect(screen.getByTestId('date-input')).toBeInTheDocument()
      expect(screen.getByTestId('description-input')).toBeInTheDocument()
      expect(screen.getByTestId('amount-input')).toBeInTheDocument()
      expect(screen.getByTestId('from-account-select')).toBeInTheDocument()
      expect(screen.getByTestId('to-account-select')).toBeInTheDocument()
      expect(screen.getByTestId('notes-input')).toBeInTheDocument()
    })

    it('should render transaction type buttons', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      expect(screen.getByTestId('type-expense')).toBeInTheDocument()
      expect(screen.getByTestId('type-income')).toBeInTheDocument()
      expect(screen.getByTestId('type-transfer')).toBeInTheDocument()
    })

    it('should default to EXPENSE type', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      const expenseButton = screen.getByTestId('type-expense')
      expect(expenseButton).toHaveClass('border-primary')
    })

    it('should set date to today by default', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      const dateInput = screen.getByTestId('date-input') as HTMLInputElement
      const today = new Date().toISOString().split('T')[0]
      expect(dateInput.value).toBe(today)
    })
  })

  describe('transaction type selection', () => {
    it('should filter from accounts based on EXPENSE type', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      const fromSelect = screen.getByTestId('from-account-select') as HTMLSelectElement
      const optionTexts = Array.from(fromSelect.querySelectorAll('option')).map((o) => o.textContent)

      // EXPENSE: from should be ASSET or LIABILITY
      expect(optionTexts.some((t) => t?.includes('Cash'))).toBe(true)
      expect(optionTexts.some((t) => t?.includes('Bank'))).toBe(true)
      expect(optionTexts.some((t) => t?.includes('Credit Card'))).toBe(true)
      expect(optionTexts.some((t) => t?.includes('Salary'))).toBe(false)
      expect(optionTexts.some((t) => t?.includes('Food'))).toBe(false)
    })

    it('should filter to accounts based on EXPENSE type', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      const toSelect = screen.getByTestId('to-account-select') as HTMLSelectElement
      const optionTexts = Array.from(toSelect.querySelectorAll('option')).map((o) => o.textContent)

      // EXPENSE: to should be EXPENSE only
      expect(optionTexts.some((t) => t?.includes('Food'))).toBe(true)
      expect(optionTexts.some((t) => t?.includes('Cash'))).toBe(false)
      expect(optionTexts.some((t) => t?.includes('Salary'))).toBe(false)
    })

    it('should update account lists when type changes to INCOME', async () => {
      const user = userEvent.setup()
      render(<TransactionForm ledgerId="test-ledger" />)

      await user.click(screen.getByTestId('type-income'))

      const fromSelect = screen.getByTestId('from-account-select') as HTMLSelectElement
      const fromOptionTexts = Array.from(fromSelect.querySelectorAll('option')).map(
        (o) => o.textContent
      )

      // INCOME: from should be INCOME only
      expect(fromOptionTexts.some((t) => t?.includes('Salary'))).toBe(true)
      expect(fromOptionTexts.some((t) => t?.includes('Cash'))).toBe(false)

      const toSelect = screen.getByTestId('to-account-select') as HTMLSelectElement
      const toOptionTexts = Array.from(toSelect.querySelectorAll('option')).map((o) => o.textContent)

      // INCOME: to should be ASSET or LIABILITY
      expect(toOptionTexts.some((t) => t?.includes('Cash'))).toBe(true)
      expect(toOptionTexts.some((t) => t?.includes('Bank'))).toBe(true)
      expect(toOptionTexts.some((t) => t?.includes('Credit Card'))).toBe(true)
    })

    it('should update account lists when type changes to TRANSFER', async () => {
      const user = userEvent.setup()
      render(<TransactionForm ledgerId="test-ledger" />)

      await user.click(screen.getByTestId('type-transfer'))

      const fromSelect = screen.getByTestId('from-account-select') as HTMLSelectElement
      const fromOptionTexts = Array.from(fromSelect.querySelectorAll('option')).map(
        (o) => o.textContent
      )

      // TRANSFER: from should be ASSET or LIABILITY
      expect(fromOptionTexts.some((t) => t?.includes('Cash'))).toBe(true)
      expect(fromOptionTexts.some((t) => t?.includes('Bank'))).toBe(true)
      expect(fromOptionTexts.some((t) => t?.includes('Credit Card'))).toBe(true)
    })

    it('should reset account selections when type changes', async () => {
      const user = userEvent.setup()
      render(<TransactionForm ledgerId="test-ledger" />)

      // Select accounts for EXPENSE
      const fromSelect = screen.getByTestId('from-account-select') as HTMLSelectElement
      await user.selectOptions(fromSelect, 'cash-id')
      expect(fromSelect.value).toBe('cash-id')

      // Change type to INCOME
      await user.click(screen.getByTestId('type-income'))

      // Accounts should be reset
      expect(fromSelect.value).toBe('')
    })
  })

  describe('form validation', () => {
    it('should require description field', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      const descriptionInput = screen.getByTestId('description-input') as HTMLInputElement
      expect(descriptionInput).toHaveAttribute('required')
    })

    it('should require amount field', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      const amountInput = screen.getByTestId('amount-input') as HTMLInputElement
      expect(amountInput).toHaveAttribute('required')
    })

    it('should require both account selects', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      const fromSelect = screen.getByTestId('from-account-select') as HTMLSelectElement
      const toSelect = screen.getByTestId('to-account-select') as HTMLSelectElement
      expect(fromSelect).toHaveAttribute('required')
      expect(toSelect).toHaveAttribute('required')
    })

    it('should show error when description is empty after form submission attempt', async () => {
      const user = userEvent.setup()
      const { container } = render(<TransactionForm ledgerId="test-ledger" />)

      // Fill all fields except description
      await user.type(screen.getByTestId('amount-input'), '100')
      fireEvent.blur(screen.getByTestId('amount-input'))
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
      await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

      // Use fireEvent.submit to bypass HTML5 validation and test JS validation
      const form = container.querySelector('form')
      if (form) {
        fireEvent.submit(form)
      }

      // JavaScript validation should show error
      await waitFor(
        () => {
          expect(screen.getByTestId('form-error')).toBeInTheDocument()
        },
        { timeout: 2000 }
      )
    })
  })

  describe('form submission', () => {
    it('should call createTransaction with correct data on submit', async () => {
      const user = userEvent.setup()
      const onSuccess = vi.fn()
      render(<TransactionForm ledgerId="test-ledger" onSuccess={onSuccess} />)

      const today = new Date().toISOString().split('T')[0]

      await user.type(screen.getByTestId('description-input'), 'Lunch expense')
      await user.type(screen.getByTestId('amount-input'), '150')
      fireEvent.blur(screen.getByTestId('amount-input'))
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
      await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

      await user.click(screen.getByTestId('submit-button'))

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            date: today,
            description: 'Lunch expense',
            amount: 150,
            from_account_id: 'cash-id',
            to_account_id: 'food-id',
            transaction_type: 'EXPENSE',
          })
        )
      })
    })

    it('should call onSuccess callback after successful submission', async () => {
      const user = userEvent.setup()
      const onSuccess = vi.fn()
      render(<TransactionForm ledgerId="test-ledger" onSuccess={onSuccess} />)

      await user.type(screen.getByTestId('description-input'), 'Test')
      await user.type(screen.getByTestId('amount-input'), '100')
      fireEvent.blur(screen.getByTestId('amount-input'))
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
      await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

      await user.click(screen.getByTestId('submit-button'))

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled()
      })
    })

    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup()
      const onCancel = vi.fn()
      render(<TransactionForm ledgerId="test-ledger" onCancel={onCancel} />)

      await user.click(screen.getByTestId('cancel-button'))

      expect(onCancel).toHaveBeenCalled()
    })

    it('should show error message on submission failure', async () => {
      mockMutateAsync.mockRejectedValue(new Error('Network error'))

      const user = userEvent.setup()
      render(<TransactionForm ledgerId="test-ledger" />)

      await user.type(screen.getByTestId('description-input'), 'Test')
      await user.type(screen.getByTestId('amount-input'), '100')
      fireEvent.blur(screen.getByTestId('amount-input'))
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
      await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

      await user.click(screen.getByTestId('submit-button'))

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
    })
  })

  describe('exclude selected account from to dropdown', () => {
    it('should not show selected from account in to dropdown', async () => {
      const user = userEvent.setup()
      render(<TransactionForm ledgerId="test-ledger" />)

      // Change to TRANSFER type where both dropdowns have same account types
      await user.click(screen.getByTestId('type-transfer'))

      // Select Cash as from account
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')

      // Check that Cash is not in to account options
      const toSelect = screen.getByTestId('to-account-select') as HTMLSelectElement
      const toOptions = Array.from(toSelect.options).map((o) => o.value)

      expect(toOptions).not.toContain('cash-id')
      expect(toOptions).toContain('bank-id')
    })
  })

  describe('notes field', () => {
    it('should render notes textarea', () => {
      render(<TransactionForm ledgerId="test-ledger" />)

      const notesInput = screen.getByTestId('notes-input')
      expect(notesInput).toBeInTheDocument()
      expect(notesInput.tagName).toBe('TEXTAREA')
    })

    it('should include notes in transaction data', async () => {
      const user = userEvent.setup()
      render(<TransactionForm ledgerId="test-ledger" />)

      await user.type(screen.getByTestId('description-input'), 'Test')
      await user.type(screen.getByTestId('amount-input'), '100')
      fireEvent.blur(screen.getByTestId('amount-input'))
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
      await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')
      await user.type(screen.getByTestId('notes-input'), 'Some notes here')

      await user.click(screen.getByTestId('submit-button'))

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            notes: 'Some notes here',
          })
        )
      })
    })
  })

  describe('amount expression', () => {
    it('should evaluate expression and include in transaction', async () => {
      const user = userEvent.setup()
      render(<TransactionForm ledgerId="test-ledger" />)

      await user.type(screen.getByTestId('description-input'), 'Split bill')
      await user.type(screen.getByTestId('amount-input'), '100/4')
      fireEvent.blur(screen.getByTestId('amount-input'))
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
      await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

      await user.click(screen.getByTestId('submit-button'))

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            amount: 25,
            amount_expression: '100/4',
          })
        )
      })
    })
  })
})

describe('TransactionForm - Zero Amount Edge Cases (T018A / DI-004)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockMutateAsync.mockResolvedValue({ id: 'new-transaction-id' })
  })

  it('should show confirmation dialog for zero amount (DI-004)', async () => {
    const user = userEvent.setup()
    render(<TransactionForm ledgerId="test-ledger" />)

    // Fill form with zero amount
    await user.type(screen.getByTestId('description-input'), 'Test transaction')
    await user.type(screen.getByTestId('amount-input'), '0')
    fireEvent.blur(screen.getByTestId('amount-input'))
    await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
    await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

    await user.click(screen.getByTestId('submit-button'))

    // Should show confirmation dialog instead of error
    await waitFor(
      () => {
        expect(screen.getByTestId('zero-amount-dialog')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )

    // Should not submit yet
    expect(mockMutateAsync).not.toHaveBeenCalled()
  })

  it('should cancel zero amount transaction when cancel clicked', async () => {
    const user = userEvent.setup()
    render(<TransactionForm ledgerId="test-ledger" />)

    // Fill form with zero amount
    await user.type(screen.getByTestId('description-input'), 'Test transaction')
    await user.type(screen.getByTestId('amount-input'), '0')
    fireEvent.blur(screen.getByTestId('amount-input'))
    await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
    await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

    await user.click(screen.getByTestId('submit-button'))

    // Wait for dialog
    await waitFor(() => {
      expect(screen.getByTestId('zero-amount-dialog')).toBeInTheDocument()
    })

    // Click cancel
    await user.click(screen.getByTestId('zero-amount-cancel'))

    // Dialog should close
    await waitFor(() => {
      expect(screen.queryByTestId('zero-amount-dialog')).not.toBeInTheDocument()
    })

    // Should not submit
    expect(mockMutateAsync).not.toHaveBeenCalled()
  })

  it('should submit zero amount transaction when confirmed', async () => {
    const user = userEvent.setup()
    const onSuccess = vi.fn()
    render(<TransactionForm ledgerId="test-ledger" onSuccess={onSuccess} />)

    // Fill form with zero amount
    await user.type(screen.getByTestId('description-input'), 'Zero amount transaction')
    await user.type(screen.getByTestId('amount-input'), '0')
    fireEvent.blur(screen.getByTestId('amount-input'))
    await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
    await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

    await user.click(screen.getByTestId('submit-button'))

    // Wait for dialog
    await waitFor(() => {
      expect(screen.getByTestId('zero-amount-dialog')).toBeInTheDocument()
    })

    // Click confirm
    await user.click(screen.getByTestId('zero-amount-confirm'))

    // Should submit with zero amount
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          amount: 0,
          description: 'Zero amount transaction',
        })
      )
    })

    expect(onSuccess).toHaveBeenCalled()
  })

  it('should not call createTransaction with invalid expression', async () => {
    const user = userEvent.setup()
    render(<TransactionForm ledgerId="test-ledger" />)

    await user.type(screen.getByTestId('description-input'), 'Test')
    await user.type(screen.getByTestId('amount-input'), 'invalid')
    fireEvent.blur(screen.getByTestId('amount-input'))
    await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
    await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

    await user.click(screen.getByTestId('submit-button'))

    await waitFor(
      () => {
        expect(screen.getByTestId('form-error')).toBeInTheDocument()
      },
      { timeout: 2000 }
    )

    expect(mockMutateAsync).not.toHaveBeenCalled()
  })
})
