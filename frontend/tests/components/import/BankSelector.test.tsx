/**
 * T071 [US3] Component test for BankSelector
 *
 * Tests the bank selector component for credit card import:
 * 1. Loads and displays available banks from API
 * 2. Shows loading state while fetching banks
 * 3. Auto-selects first bank if none selected
 * 4. Handles API errors gracefully
 * 5. Supports disabled state
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextIntlClientProvider } from 'next-intl'

import BankSelector from '@/components/import/BankSelector'
import zhTW from '../../../messages/zh-TW.json'

// Mock the import API
const mockGetBanks = vi.fn()
vi.mock('@/lib/api/import', () => ({
  importApi: {
    getBanks: () => mockGetBanks(),
  },
}))

function createWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <NextIntlClientProvider locale="zh-TW" messages={zhTW}>
        {children}
      </NextIntlClientProvider>
    )
  }
}

describe('BankSelector', () => {
  const mockBanks = [
    { code: 'CTBC', name: '中國信託' },
    { code: 'CATHAY', name: '國泰世華' },
    { code: 'ESUN', name: '玉山銀行' },
  ]

  const defaultProps = {
    value: null,
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetBanks.mockResolvedValue({ banks: mockBanks })
  })

  describe('Loading State', () => {
    it('shows loading skeleton while fetching banks', () => {
      mockGetBanks.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ banks: mockBanks }), 100))
      )

      const { container } = render(<BankSelector {...defaultProps} />, {
        wrapper: createWrapper(),
      })

      expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
    })

    it('hides loading state after banks are loaded', async () => {
      const { container } = render(<BankSelector {...defaultProps} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(container.querySelector('.animate-pulse')).not.toBeInTheDocument()
      })
    })
  })

  describe('Rendering Banks', () => {
    it('renders select element with label', async () => {
      render(<BankSelector {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText(zhTW.import.selectBank)).toBeInTheDocument()
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })
    })

    it('displays all bank options', async () => {
      render(<BankSelector {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByRole('option', { name: '中國信託' })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: '國泰世華' })).toBeInTheDocument()
        expect(screen.getByRole('option', { name: '玉山銀行' })).toBeInTheDocument()
      })
    })

    it('includes placeholder option', async () => {
      render(<BankSelector {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        const placeholderOption = screen.getByRole('option', {
          name: new RegExp(`-- ${zhTW.import.selectBank} --`),
        })
        expect(placeholderOption).toBeInTheDocument()
        expect(placeholderOption).toBeDisabled()
      })
    })
  })

  describe('Selection Behavior', () => {
    it('auto-selects first bank when value is null', async () => {
      const onChange = vi.fn()
      render(<BankSelector value={null} onChange={onChange} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith('CTBC')
      })
    })

    it('does not auto-select when value is already set', async () => {
      const onChange = vi.fn()
      render(<BankSelector value="ESUN" onChange={onChange} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toHaveValue('ESUN')
      })

      expect(onChange).not.toHaveBeenCalled()
    })

    it('calls onChange when user selects a bank', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<BankSelector value="CTBC" onChange={onChange} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      await user.selectOptions(screen.getByRole('combobox'), 'CATHAY')

      expect(onChange).toHaveBeenCalledWith('CATHAY')
    })
  })

  describe('Error Handling', () => {
    it('displays error message when API fails', async () => {
      mockGetBanks.mockRejectedValueOnce(new Error('Network error'))

      render(<BankSelector {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Failed to load banks')).toBeInTheDocument()
      })
    })

    it('does not show select when error occurs', async () => {
      mockGetBanks.mockRejectedValueOnce(new Error('Network error'))

      render(<BankSelector {...defaultProps} />, { wrapper: createWrapper() })

      await waitFor(() => {
        expect(screen.getByText('Failed to load banks')).toBeInTheDocument()
      })

      expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    })
  })

  describe('Disabled State', () => {
    it('disables select when disabled prop is true', async () => {
      render(<BankSelector {...defaultProps} disabled={true} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeDisabled()
      })
    })

    it('enables select when disabled prop is false', async () => {
      render(<BankSelector {...defaultProps} disabled={false} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByRole('combobox')).not.toBeDisabled()
      })
    })
  })

  describe('Empty Banks', () => {
    it('handles empty banks list gracefully', async () => {
      mockGetBanks.mockResolvedValueOnce({ banks: [] })
      const onChange = vi.fn()

      render(<BankSelector value={null} onChange={onChange} />, {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      // Should not call onChange with undefined
      expect(onChange).not.toHaveBeenCalled()
    })
  })
})
