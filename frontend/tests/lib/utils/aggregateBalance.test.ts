/**
 * T128 [US6a] Unit test for aggregateBalance calculation (recursive sum)
 *
 * Tests the aggregateBalance utility that calculates the total balance
 * for a parent account including all its descendants.
 */
import { describe, it, expect } from 'vitest'
import { aggregateBalance, buildAccountBalanceMap } from '@/lib/utils/aggregateBalance'
import type { SidebarAccountItem } from '@/types/dashboard'

describe('aggregateBalance', () => {
  describe('aggregateBalance function', () => {
    it('should return own balance for leaf account (no children)', () => {
      const account: SidebarAccountItem = {
        id: 'leaf-1',
        name: 'Checking Account',
        type: 'ASSET',
        balance: 1000,
        parent_id: null,
        depth: 1,
        children: [],
      }

      expect(aggregateBalance(account)).toBe(1000)
    })

    it('should sum own balance plus all child balances', () => {
      const account: SidebarAccountItem = {
        id: 'parent-1',
        name: 'Bank Accounts',
        type: 'ASSET',
        balance: 500, // Parent's own balance
        parent_id: null,
        depth: 1,
        children: [
          {
            id: 'child-1',
            name: 'Checking',
            type: 'ASSET',
            balance: 1000,
            parent_id: 'parent-1',
            depth: 2,
            children: [],
          },
          {
            id: 'child-2',
            name: 'Savings',
            type: 'ASSET',
            balance: 2000,
            parent_id: 'parent-1',
            depth: 2,
            children: [],
          },
        ],
      }

      // 500 + 1000 + 2000 = 3500
      expect(aggregateBalance(account)).toBe(3500)
    })

    it('should recursively sum grandchild balances (3-level hierarchy)', () => {
      const account: SidebarAccountItem = {
        id: 'root-1',
        name: 'Assets',
        type: 'ASSET',
        balance: 100,
        parent_id: null,
        depth: 1,
        children: [
          {
            id: 'parent-1',
            name: 'Bank Accounts',
            type: 'ASSET',
            balance: 200,
            parent_id: 'root-1',
            depth: 2,
            children: [
              {
                id: 'child-1',
                name: 'Checking',
                type: 'ASSET',
                balance: 1000,
                parent_id: 'parent-1',
                depth: 3,
                children: [],
              },
              {
                id: 'child-2',
                name: 'Savings',
                type: 'ASSET',
                balance: 2000,
                parent_id: 'parent-1',
                depth: 3,
                children: [],
              },
            ],
          },
        ],
      }

      // 100 + 200 + 1000 + 2000 = 3300
      expect(aggregateBalance(account)).toBe(3300)
    })

    it('should handle negative balances correctly', () => {
      const account: SidebarAccountItem = {
        id: 'liability-1',
        name: 'Loans',
        type: 'LIABILITY',
        balance: -5000,
        parent_id: null,
        depth: 1,
        children: [
          {
            id: 'loan-1',
            name: 'Car Loan',
            type: 'LIABILITY',
            balance: -15000,
            parent_id: 'liability-1',
            depth: 2,
            children: [],
          },
        ],
      }

      // -5000 + -15000 = -20000
      expect(aggregateBalance(account)).toBe(-20000)
    })

    it('should handle zero balances', () => {
      const account: SidebarAccountItem = {
        id: 'empty-1',
        name: 'Empty Parent',
        type: 'ASSET',
        balance: 0,
        parent_id: null,
        depth: 1,
        children: [
          {
            id: 'zero-child',
            name: 'Zero Child',
            type: 'ASSET',
            balance: 0,
            parent_id: 'empty-1',
            depth: 2,
            children: [],
          },
        ],
      }

      expect(aggregateBalance(account)).toBe(0)
    })

    it('should handle mixed positive and negative child balances', () => {
      const account: SidebarAccountItem = {
        id: 'mixed-1',
        name: 'Mixed',
        type: 'ASSET',
        balance: 1000,
        parent_id: null,
        depth: 1,
        children: [
          {
            id: 'pos-child',
            name: 'Positive',
            type: 'ASSET',
            balance: 500,
            parent_id: 'mixed-1',
            depth: 2,
            children: [],
          },
          {
            id: 'neg-child',
            name: 'Negative',
            type: 'ASSET',
            balance: -200,
            parent_id: 'mixed-1',
            depth: 2,
            children: [],
          },
        ],
      }

      // 1000 + 500 + (-200) = 1300
      expect(aggregateBalance(account)).toBe(1300)
    })

    it('should handle decimal balances with precision', () => {
      const account: SidebarAccountItem = {
        id: 'decimal-1',
        name: 'Decimal Parent',
        type: 'ASSET',
        balance: 100.5,
        parent_id: null,
        depth: 1,
        children: [
          {
            id: 'decimal-child',
            name: 'Decimal Child',
            type: 'ASSET',
            balance: 50.25,
            parent_id: 'decimal-1',
            depth: 2,
            children: [],
          },
        ],
      }

      expect(aggregateBalance(account)).toBeCloseTo(150.75)
    })
  })

  describe('buildAccountBalanceMap', () => {
    it('should build a map of account IDs to aggregated balances', () => {
      const accounts: SidebarAccountItem[] = [
        {
          id: 'parent-1',
          name: 'Bank Accounts',
          type: 'ASSET',
          balance: 100,
          parent_id: null,
          depth: 1,
          children: [
            {
              id: 'child-1',
              name: 'Checking',
              type: 'ASSET',
              balance: 1000,
              parent_id: 'parent-1',
              depth: 2,
              children: [],
            },
          ],
        },
        {
          id: 'leaf-1',
          name: 'Cash',
          type: 'ASSET',
          balance: 500,
          parent_id: null,
          depth: 1,
          children: [],
        },
      ]

      const map = buildAccountBalanceMap(accounts)

      expect(map.get('parent-1')).toBe(1100) // 100 + 1000
      expect(map.get('child-1')).toBe(1000) // leaf, own balance only
      expect(map.get('leaf-1')).toBe(500) // leaf, own balance only
    })

    it('should return empty map for empty array', () => {
      const map = buildAccountBalanceMap([])
      expect(map.size).toBe(0)
    })

    it('should handle deeply nested structure (3 levels)', () => {
      const accounts: SidebarAccountItem[] = [
        {
          id: 'root',
          name: 'Root',
          type: 'ASSET',
          balance: 10,
          parent_id: null,
          depth: 1,
          children: [
            {
              id: 'level2',
              name: 'Level 2',
              type: 'ASSET',
              balance: 20,
              parent_id: 'root',
              depth: 2,
              children: [
                {
                  id: 'level3',
                  name: 'Level 3',
                  type: 'ASSET',
                  balance: 30,
                  parent_id: 'level2',
                  depth: 3,
                  children: [],
                },
              ],
            },
          ],
        },
      ]

      const map = buildAccountBalanceMap(accounts)

      expect(map.get('root')).toBe(60) // 10 + 20 + 30
      expect(map.get('level2')).toBe(50) // 20 + 30
      expect(map.get('level3')).toBe(30) // leaf
    })
  })
})
