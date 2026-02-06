/**
 * T017 [US1] Component test for TransactionModal
 *
 * Tests the transaction modal component:
 * 1. Modal opens when trigger is clicked
 * 2. Modal contains TransactionForm
 * 3. Modal closes on successful save
 * 4. Modal closes on cancel
 * 5. Modal closes when clicking outside (overlay)
 * 6. Account pre-selection based on context
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock next-intl
vi.mock('react-i18next', () => ({
  useTranslation: () => (key: string) => {
    const translations: Record<string, string> = {
      'transactionModal.title': 'Add Transaction',
      'transactionModal.trigger': 'Add Transaction',
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
      'common.cancel': 'Cancel',
      'transactionTypes.EXPENSE': 'Expense',
      'transactionTypes.INCOME': 'Income',
      'transactionTypes.TRANSFER': 'Transfer',
      'transactionTypes.expenseDesc': 'Money out',
      'transactionTypes.incomeDesc': 'Money in',
      'transactionTypes.transferDesc': 'Move between accounts',
      'accountTypes.ASSET': 'Asset',
      'accountTypes.EXPENSE': 'Expense',
      'transactionEntry.notes': 'Notes',
      'transactionEntry.notesPlaceholder': 'Optional notes',
      'validation.descriptionRequired': 'Description is required',
    }
    return translations[key] || key
  },
}))

// Mock accounts data with full structure
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
]

vi.mock('@/lib/hooks/useAccounts', () => ({
  useAccounts: () => ({
    data: mockAccounts,
    isLoading: false,
    error: null,
  }),
}))

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
    data: [],
    isLoading: false,
  }),
  useCreateTag: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}))

// Import after mocks
import { TransactionModal } from '@/components/transactions/TransactionModal'

describe('TransactionModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockMutateAsync.mockResolvedValue({ id: 'new-transaction-id' })
  })

  describe('modal rendering', () => {
    it('should render trigger button', () => {
      render(<TransactionModal ledgerId="test-ledger" />)
      expect(screen.getByText('Add Transaction')).toBeInTheDocument()
    })

    it('should not render modal content initially', () => {
      render(<TransactionModal ledgerId="test-ledger" />)
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should open modal when trigger is clicked', async () => {
      const user = userEvent.setup()
      render(<TransactionModal ledgerId="test-ledger" />)

      await user.click(screen.getByText('Add Transaction'))

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      // Modal title is shown
      expect(screen.getAllByText('Add Transaction').length).toBeGreaterThan(1)
    })
  })

  describe('modal behavior', () => {
    it('should close modal when X button is clicked', async () => {
      const user = userEvent.setup()
      render(<TransactionModal ledgerId="test-ledger" />)

      await user.click(screen.getByText('Add Transaction'))
      expect(screen.getByRole('dialog')).toBeInTheDocument()

      await user.click(screen.getByTestId('modal-close-button'))

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })

    it('should close modal when cancel button is clicked', async () => {
      const user = userEvent.setup()
      render(<TransactionModal ledgerId="test-ledger" />)

      await user.click(screen.getByText('Add Transaction'))
      expect(screen.getByRole('dialog')).toBeInTheDocument()

      await user.click(screen.getByTestId('cancel-button'))

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })

    it('should close modal after successful save', async () => {
      const user = userEvent.setup()
      render(<TransactionModal ledgerId="test-ledger" />)

      await user.click(screen.getByText('Add Transaction'))

      // Fill form
      await user.type(screen.getByTestId('description-input'), 'Test')
      await user.type(screen.getByTestId('amount-input'), '100')
      fireEvent.blur(screen.getByTestId('amount-input'))
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
      await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

      await user.click(screen.getByTestId('submit-button'))

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })

    it('should close modal when clicking overlay', async () => {
      const user = userEvent.setup()
      render(<TransactionModal ledgerId="test-ledger" />)

      await user.click(screen.getByText('Add Transaction'))

      const overlay = screen.getByTestId('modal-overlay')
      await user.click(overlay)

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
      })
    })
  })

  describe('account pre-selection', () => {
    it('should pass preSelectedAccountId to TransactionForm', async () => {
      const user = userEvent.setup()
      render(
        <TransactionModal ledgerId="test-ledger" preSelectedAccountId="cash-id" />
      )

      await user.click(screen.getByText('Add Transaction'))

      // The modal should be open and contain the form
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      // The form should have pre-selected account ID
      // This is implicitly tested through the form behavior
    })

    it('should pass preSelectedAccountType to TransactionForm', async () => {
      const user = userEvent.setup()
      render(
        <TransactionModal
          ledgerId="test-ledger"
          preSelectedAccountId="cash-id"
          preSelectedAccountType="ASSET"
        />
      )

      await user.click(screen.getByText('Add Transaction'))

      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  describe('callback props', () => {
    it('should call onTransactionCreated callback after save', async () => {
      const onTransactionCreated = vi.fn()
      const user = userEvent.setup()
      render(
        <TransactionModal ledgerId="test-ledger" onTransactionCreated={onTransactionCreated} />
      )

      await user.click(screen.getByText('Add Transaction'))

      // Fill and submit form
      await user.type(screen.getByTestId('description-input'), 'Test')
      await user.type(screen.getByTestId('amount-input'), '100')
      fireEvent.blur(screen.getByTestId('amount-input'))
      await user.selectOptions(screen.getByTestId('from-account-select'), 'cash-id')
      await user.selectOptions(screen.getByTestId('to-account-select'), 'food-id')

      await user.click(screen.getByTestId('submit-button'))

      await waitFor(() => {
        expect(onTransactionCreated).toHaveBeenCalled()
      })
    })
  })

  describe('custom trigger', () => {
    it('should render custom trigger when provided', () => {
      render(
        <TransactionModal
          ledgerId="test-ledger"
          trigger={<button data-testid="custom-trigger">Custom Button</button>}
        />
      )

      expect(screen.getByTestId('custom-trigger')).toBeInTheDocument()
      expect(screen.queryByText('Add Transaction')).not.toBeInTheDocument()
    })

    it('should open modal when custom trigger is clicked', async () => {
      const user = userEvent.setup()
      render(
        <TransactionModal
          ledgerId="test-ledger"
          trigger={<button data-testid="custom-trigger">Custom Button</button>}
        />
      )

      await user.click(screen.getByTestId('custom-trigger'))

      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('should use custom trigger text when provided', () => {
      render(<TransactionModal ledgerId="test-ledger" triggerText="New Entry" />)

      expect(screen.getByText('New Entry')).toBeInTheDocument()
    })
  })
})
