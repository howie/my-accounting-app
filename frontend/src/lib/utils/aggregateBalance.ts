/**
 * Utility functions for calculating aggregated balances across account hierarchies.
 * Used by the Sidebar to display parent accounts with the sum of their children.
 *
 * T135 [US6a] - Implementation
 */
import type { SidebarAccountItem } from '@/types/dashboard'

/**
 * Recursively calculates the total balance for an account including all descendants.
 *
 * For leaf accounts (no children), returns the account's own balance.
 * For parent accounts, returns own balance + sum of all children's aggregated balances.
 *
 * @param account - The account to calculate aggregated balance for
 * @returns The total balance (self + all descendants)
 *
 * @example
 * // Parent (100) with children (1000, 2000) = 3100
 * const total = aggregateBalance(parentAccount);
 */
export function aggregateBalance(account: SidebarAccountItem): number {
  // Base case: leaf account (no children)
  if (!account.children || account.children.length === 0) {
    return account.balance
  }

  // Recursive case: sum own balance + all children's aggregated balances
  const childrenTotal = account.children.reduce((sum, child) => {
    return sum + aggregateBalance(child)
  }, 0)

  return account.balance + childrenTotal
}

/**
 * Builds a map of account IDs to their aggregated balances.
 *
 * Useful for efficient lookups when rendering the sidebar,
 * avoiding repeated recursive calculations.
 *
 * @param accounts - Array of root-level accounts (may have nested children)
 * @returns Map of account ID to aggregated balance
 *
 * @example
 * const balanceMap = buildAccountBalanceMap(categories[0].accounts);
 * const totalForAccount = balanceMap.get('account-id');
 */
export function buildAccountBalanceMap(accounts: SidebarAccountItem[]): Map<string, number> {
  const balanceMap = new Map<string, number>()

  function processAccount(account: SidebarAccountItem): number {
    const aggregated = aggregateBalance(account)
    balanceMap.set(account.id, aggregated)

    // Process children recursively to populate the map
    if (account.children) {
      account.children.forEach((child) => processAccount(child))
    }

    return aggregated
  }

  accounts.forEach((account) => processAccount(account))

  return balanceMap
}

/**
 * Checks if an account has any children (is a parent account).
 *
 * @param account - The account to check
 * @returns true if the account has children, false otherwise
 */
export function hasChildren(account: SidebarAccountItem): boolean {
  return account.children !== undefined && account.children.length > 0
}
