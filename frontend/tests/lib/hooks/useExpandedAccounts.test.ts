/**
 * T131 [US6a] Test for expand/collapse state preservation in sessionStorage
 *
 * Tests the useExpandedAccounts hook that manages which parent accounts
 * are expanded in the sidebar, with persistence to sessionStorage.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useExpandedAccounts } from '@/lib/hooks/useExpandedAccounts'

// Mock sessionStorage
const mockSessionStorage = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
    get length() {
      return Object.keys(store).length
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  }
})()

describe('useExpandedAccounts', () => {
  beforeEach(() => {
    vi.stubGlobal('sessionStorage', mockSessionStorage)
    mockSessionStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('Initial state', () => {
    it('should return empty set when no stored state exists', () => {
      const { result } = renderHook(() => useExpandedAccounts())

      expect(result.current.expandedAccountIds).toEqual(new Set())
    })

    it('should load expanded accounts from sessionStorage on mount', () => {
      // Pre-populate sessionStorage
      const storedIds = ['account-1', 'account-2']
      mockSessionStorage.setItem('ledgerone-expanded-accounts', JSON.stringify(storedIds))

      const { result } = renderHook(() => useExpandedAccounts())

      expect(result.current.expandedAccountIds).toEqual(new Set(storedIds))
    })

    it('should handle invalid JSON in sessionStorage gracefully', () => {
      mockSessionStorage.setItem('ledgerone-expanded-accounts', 'invalid-json')

      const { result } = renderHook(() => useExpandedAccounts())

      // Should fall back to empty set on parse error
      expect(result.current.expandedAccountIds).toEqual(new Set())
    })
  })

  describe('isExpanded', () => {
    it('should return true for expanded account IDs', () => {
      const storedIds = ['account-1', 'account-2']
      mockSessionStorage.setItem('ledgerone-expanded-accounts', JSON.stringify(storedIds))

      const { result } = renderHook(() => useExpandedAccounts())

      expect(result.current.isExpanded('account-1')).toBe(true)
      expect(result.current.isExpanded('account-2')).toBe(true)
    })

    it('should return false for collapsed account IDs', () => {
      const storedIds = ['account-1']
      mockSessionStorage.setItem('ledgerone-expanded-accounts', JSON.stringify(storedIds))

      const { result } = renderHook(() => useExpandedAccounts())

      expect(result.current.isExpanded('account-2')).toBe(false)
      expect(result.current.isExpanded('unknown-id')).toBe(false)
    })
  })

  describe('toggleExpanded', () => {
    it('should expand a collapsed account', () => {
      const { result } = renderHook(() => useExpandedAccounts())

      expect(result.current.isExpanded('account-1')).toBe(false)

      act(() => {
        result.current.toggleExpanded('account-1')
      })

      expect(result.current.isExpanded('account-1')).toBe(true)
    })

    it('should collapse an expanded account', () => {
      const storedIds = ['account-1']
      mockSessionStorage.setItem('ledgerone-expanded-accounts', JSON.stringify(storedIds))

      const { result } = renderHook(() => useExpandedAccounts())

      expect(result.current.isExpanded('account-1')).toBe(true)

      act(() => {
        result.current.toggleExpanded('account-1')
      })

      expect(result.current.isExpanded('account-1')).toBe(false)
    })

    it('should persist changes to sessionStorage', () => {
      const { result } = renderHook(() => useExpandedAccounts())

      act(() => {
        result.current.toggleExpanded('account-1')
      })

      // Verify sessionStorage was updated
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'ledgerone-expanded-accounts',
        expect.any(String)
      )

      const storedValue = mockSessionStorage.getItem('ledgerone-expanded-accounts')
      const parsedIds = JSON.parse(storedValue as string)
      expect(parsedIds).toContain('account-1')
    })
  })

  describe('setExpanded', () => {
    it('should explicitly expand an account', () => {
      const { result } = renderHook(() => useExpandedAccounts())

      act(() => {
        result.current.setExpanded('account-1', true)
      })

      expect(result.current.isExpanded('account-1')).toBe(true)
    })

    it('should explicitly collapse an account', () => {
      const storedIds = ['account-1']
      mockSessionStorage.setItem('ledgerone-expanded-accounts', JSON.stringify(storedIds))

      const { result } = renderHook(() => useExpandedAccounts())

      act(() => {
        result.current.setExpanded('account-1', false)
      })

      expect(result.current.isExpanded('account-1')).toBe(false)
    })

    it('should not duplicate IDs when expanding already expanded account', () => {
      const storedIds = ['account-1']
      mockSessionStorage.setItem('ledgerone-expanded-accounts', JSON.stringify(storedIds))

      const { result } = renderHook(() => useExpandedAccounts())

      act(() => {
        result.current.setExpanded('account-1', true)
      })

      expect(result.current.expandedAccountIds.size).toBe(1)
    })
  })

  describe('expandAll / collapseAll', () => {
    it('should expand all provided account IDs', () => {
      const { result } = renderHook(() => useExpandedAccounts())

      const accountIds = ['account-1', 'account-2', 'account-3']

      act(() => {
        result.current.expandAll(accountIds)
      })

      expect(result.current.isExpanded('account-1')).toBe(true)
      expect(result.current.isExpanded('account-2')).toBe(true)
      expect(result.current.isExpanded('account-3')).toBe(true)
    })

    it('should collapse all accounts', () => {
      const storedIds = ['account-1', 'account-2']
      mockSessionStorage.setItem('ledgerone-expanded-accounts', JSON.stringify(storedIds))

      const { result } = renderHook(() => useExpandedAccounts())

      act(() => {
        result.current.collapseAll()
      })

      expect(result.current.expandedAccountIds.size).toBe(0)
      expect(result.current.isExpanded('account-1')).toBe(false)
      expect(result.current.isExpanded('account-2')).toBe(false)
    })
  })

  describe('Session persistence', () => {
    it('should preserve state across re-renders', () => {
      const { result, rerender } = renderHook(() => useExpandedAccounts())

      act(() => {
        result.current.toggleExpanded('account-1')
      })

      // Re-render the hook
      rerender()

      expect(result.current.isExpanded('account-1')).toBe(true)
    })

    it('should maintain separate state from category expansion (useSidebarState)', () => {
      // This hook is specifically for individual account expansion
      // It should use a different storage key than the category state
      const { result } = renderHook(() => useExpandedAccounts())

      act(() => {
        result.current.toggleExpanded('account-1')
      })

      // Verify the storage key is specific to account expansion
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'ledgerone-expanded-accounts',
        expect.any(String)
      )

      // Should NOT interfere with 'ledgerone-sidebar-state' (used by useSidebarState)
      expect(mockSessionStorage.getItem('ledgerone-sidebar-state')).toBeNull()
    })
  })

  describe('Hydration safety', () => {
    it('should provide isHydrated flag to prevent hydration mismatch', () => {
      const { result } = renderHook(() => useExpandedAccounts())

      // Initially should be hydrated after effect runs
      // The hook should provide an isHydrated flag for SSR safety
      expect(result.current.isHydrated).toBeDefined()
    })

    it('should return consistent values before and after hydration', () => {
      const storedIds = ['account-1']
      mockSessionStorage.setItem('ledgerone-expanded-accounts', JSON.stringify(storedIds))

      const { result } = renderHook(() => useExpandedAccounts())

      // After hydration, should have the stored values
      expect(result.current.isExpanded('account-1')).toBe(true)
    })
  })
})
