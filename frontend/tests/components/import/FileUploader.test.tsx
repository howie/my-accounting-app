/**
 * T071 [US1] Component test for FileUploader
 *
 * Tests the file upload component for data import:
 * 1. Displays import type selector (MyAB CSV / Credit Card)
 * 2. Shows file input for CSV upload
 * 3. Shows BankSelector when Credit Card type selected
 * 4. Validates file before upload
 * 5. Calls API on upload and passes preview data
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import FileUploader from '@/components/import/FileUploader'
import { ImportType } from '@/lib/api/import'

// Mock the import API
const mockCreatePreview = vi.fn()
vi.mock('@/lib/api/import', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api/import')>()
  return {
    ...actual,
    importApi: {
      createPreview: (...args: unknown[]) => mockCreatePreview(...args),
      getBanks: vi.fn().mockResolvedValue({
        banks: [
          { code: 'CTBC', name: '中國信託' },
          { code: 'CATHAY', name: '國泰世華' },
        ],
      }),
    },
  }
})

// Mock BankSelector to simplify testing
vi.mock('@/components/import/BankSelector', () => ({
  default: ({ value, onChange, disabled }: { value: string | null; onChange: (v: string) => void; disabled?: boolean }) => (
    <select
      data-testid="bank-selector"
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
    >
      <option value="">Select Bank</option>
      <option value="CTBC">中國信託</option>
      <option value="CATHAY">國泰世華</option>
    </select>
  ),
}))

describe('FileUploader', () => {
  const defaultProps = {
    ledgerId: 'ledger-123',
    onPreviewLoaded: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Helper to get import type select (first combobox)
  const getImportTypeSelect = () => screen.getAllByRole('combobox')[0]

  // Helper to get file input
  const getFileInput = () => {
    const inputs = document.querySelectorAll('input[type="file"]')
    return inputs[0] as HTMLInputElement
  }

  describe('Rendering', () => {
    it('renders upload section with title', () => {
      render(<FileUploader {...defaultProps} />)

      expect(screen.getByText('1. Upload File')).toBeInTheDocument()
    })

    it('renders import type selector with MyAB CSV as default', () => {
      render(<FileUploader {...defaultProps} />)

      expect(screen.getByText('Import Type')).toBeInTheDocument()
      const select = getImportTypeSelect()
      expect(select).toBeInTheDocument()
      expect(select).toHaveValue(ImportType.MYAB_CSV)
    })

    it('renders file input for CSV files', () => {
      render(<FileUploader {...defaultProps} />)

      expect(screen.getByText('Select File')).toBeInTheDocument()
      const fileInput = getFileInput()
      expect(fileInput).toBeInTheDocument()
      expect(fileInput).toHaveAttribute('accept', '.csv')
    })

    it('renders upload button disabled when no file selected', () => {
      render(<FileUploader {...defaultProps} />)

      const button = screen.getByRole('button', { name: /generate preview/i })
      expect(button).toBeDisabled()
    })
  })

  describe('Import Type Selection', () => {
    it('does not show bank selector for MyAB CSV type', () => {
      render(<FileUploader {...defaultProps} />)

      expect(screen.queryByTestId('bank-selector')).not.toBeInTheDocument()
    })

    it('shows bank selector when Credit Card type is selected', async () => {
      const user = userEvent.setup()
      render(<FileUploader {...defaultProps} />)

      const typeSelect = getImportTypeSelect()
      await user.selectOptions(typeSelect, ImportType.CREDIT_CARD)

      expect(screen.getByTestId('bank-selector')).toBeInTheDocument()
    })

    it('hides bank selector when switching back to MyAB CSV', async () => {
      const user = userEvent.setup()
      render(<FileUploader {...defaultProps} />)

      const typeSelect = getImportTypeSelect()
      await user.selectOptions(typeSelect, ImportType.CREDIT_CARD)
      expect(screen.getByTestId('bank-selector')).toBeInTheDocument()

      await user.selectOptions(typeSelect, ImportType.MYAB_CSV)
      expect(screen.queryByTestId('bank-selector')).not.toBeInTheDocument()
    })
  })

  describe('File Selection', () => {
    it('enables upload button when file is selected', async () => {
      const user = userEvent.setup()
      render(<FileUploader {...defaultProps} />)

      const file = new File(['date,amount'], 'test.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file)

      const button = screen.getByRole('button', { name: /generate preview/i })
      expect(button).not.toBeDisabled()
    })

    it('clears error when new file is selected', async () => {
      const user = userEvent.setup()
      mockCreatePreview.mockRejectedValueOnce(new Error('Invalid format'))

      render(<FileUploader {...defaultProps} />)

      // Upload first file and trigger error
      const file1 = new File(['bad data'], 'test1.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file1)

      const button = screen.getByRole('button', { name: /generate preview/i })
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText('Invalid format')).toBeInTheDocument()
      })

      // Upload second file - error should clear
      const file2 = new File(['good data'], 'test2.csv', { type: 'text/csv' })
      await user.upload(fileInput, file2)

      expect(screen.queryByText('Invalid format')).not.toBeInTheDocument()
    })
  })

  describe('Upload Behavior', () => {
    it('calls API with correct parameters for MyAB CSV', async () => {
      const user = userEvent.setup()
      const mockPreview = {
        session_id: 'session-123',
        total_count: 10,
        transactions: [],
        duplicates: [],
        account_mappings: [],
        validation_errors: [],
        is_valid: true,
      }
      mockCreatePreview.mockResolvedValueOnce(mockPreview)

      render(<FileUploader {...defaultProps} />)

      const file = new File(['date,amount\n2024/01/01,100'], 'test.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file)

      const button = screen.getByRole('button', { name: /generate preview/i })
      await user.click(button)

      await waitFor(() => {
        expect(mockCreatePreview).toHaveBeenCalledWith(
          'ledger-123',
          expect.any(File),
          ImportType.MYAB_CSV,
          undefined
        )
      })
    })

    it('calls API with bank code for Credit Card import', async () => {
      const user = userEvent.setup()
      const mockPreview = {
        session_id: 'session-123',
        total_count: 5,
        transactions: [],
        duplicates: [],
        account_mappings: [],
        validation_errors: [],
        is_valid: true,
      }
      mockCreatePreview.mockResolvedValueOnce(mockPreview)

      render(<FileUploader {...defaultProps} />)

      // Select Credit Card type
      const typeSelect = getImportTypeSelect()
      await user.selectOptions(typeSelect, ImportType.CREDIT_CARD)

      // Select bank
      const bankSelect = screen.getByTestId('bank-selector')
      await user.selectOptions(bankSelect, 'CTBC')

      // Upload file
      const file = new File(['date,amount\n2024/01/01,100'], 'card.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file)

      const button = screen.getByRole('button', { name: /generate preview/i })
      await user.click(button)

      await waitFor(() => {
        expect(mockCreatePreview).toHaveBeenCalledWith(
          'ledger-123',
          expect.any(File),
          ImportType.CREDIT_CARD,
          'CTBC'
        )
      })
    })

    it('shows loading state while uploading', async () => {
      const user = userEvent.setup()
      mockCreatePreview.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<FileUploader {...defaultProps} />)

      const file = new File(['data'], 'test.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file)

      const button = screen.getByRole('button', { name: /generate preview/i })
      await user.click(button)

      expect(screen.getByText('Analyzing...')).toBeInTheDocument()
    })

    it('calls onPreviewLoaded on successful upload', async () => {
      const user = userEvent.setup()
      const mockPreview = {
        session_id: 'session-123',
        total_count: 10,
        transactions: [],
        duplicates: [],
        account_mappings: [],
        validation_errors: [],
        is_valid: true,
      }
      mockCreatePreview.mockResolvedValueOnce(mockPreview)

      render(<FileUploader {...defaultProps} />)

      const file = new File(['data'], 'test.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file)

      const button = screen.getByRole('button', { name: /generate preview/i })
      await user.click(button)

      await waitFor(() => {
        expect(defaultProps.onPreviewLoaded).toHaveBeenCalledWith(mockPreview)
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message on upload failure', async () => {
      const user = userEvent.setup()
      mockCreatePreview.mockRejectedValueOnce(new Error('File too large'))

      render(<FileUploader {...defaultProps} />)

      const file = new File(['data'], 'test.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file)

      const button = screen.getByRole('button', { name: /generate preview/i })
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText('File too large')).toBeInTheDocument()
      })
    })

    it('shows error when Credit Card selected without bank', async () => {
      const user = userEvent.setup()
      render(<FileUploader {...defaultProps} />)

      // Select Credit Card type but don't select bank
      const typeSelect = getImportTypeSelect()
      await user.selectOptions(typeSelect, ImportType.CREDIT_CARD)

      // Upload file
      const file = new File(['data'], 'test.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file)

      // Button should be disabled without bank selection
      const button = screen.getByRole('button', { name: /generate preview/i })
      expect(button).toBeDisabled()
    })
  })

  describe('Disabled State', () => {
    it('disables all inputs while loading', async () => {
      const user = userEvent.setup()
      mockCreatePreview.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      )

      render(<FileUploader {...defaultProps} />)

      const file = new File(['data'], 'test.csv', { type: 'text/csv' })
      const fileInput = getFileInput()
      await user.upload(fileInput, file)

      const button = screen.getByRole('button', { name: /generate preview/i })
      await user.click(button)

      const typeSelect = getImportTypeSelect()
      expect(typeSelect).toBeDisabled()
      expect(fileInput).toBeDisabled()
    })
  })
})
