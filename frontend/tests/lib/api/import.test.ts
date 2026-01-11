/**
 * Tests for import API client
 *
 * Tests the API client functions for data import operations.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the API module
vi.mock('@/lib/api', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPostMultipart: vi.fn(),
}))

import { importApi, ImportType } from '@/lib/api/import'
import { apiGet, apiPost, apiPostMultipart } from '@/lib/api'

const mockApiGet = vi.mocked(apiGet)
const mockApiPost = vi.mocked(apiPost)
const mockApiPostMultipart = vi.mocked(apiPostMultipart)

describe('importApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createPreview', () => {
    const ledgerId = 'ledger-123'
    const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' })

    it('should call apiPostMultipart with correct endpoint and FormData for MyAB CSV', async () => {
      const mockResponse = {
        session_id: 'session-123',
        total_count: 10,
        date_range: { start: '2024-01-01', end: '2024-12-31' },
        transactions: [],
        duplicates: [],
        account_mappings: [],
        validation_errors: [],
        is_valid: true,
      }
      mockApiPostMultipart.mockResolvedValue(mockResponse)

      const result = await importApi.createPreview(ledgerId, mockFile, ImportType.MYAB_CSV)

      expect(mockApiPostMultipart).toHaveBeenCalledTimes(1)
      expect(mockApiPostMultipart).toHaveBeenCalledWith(
        `/ledgers/${ledgerId}/import/preview`,
        expect.any(FormData)
      )

      // Verify FormData contents
      const formData = mockApiPostMultipart.mock.calls[0][1] as FormData
      expect(formData.get('file')).toBe(mockFile)
      expect(formData.get('import_type')).toBe(ImportType.MYAB_CSV)
      expect(formData.get('bank_code')).toBeNull()

      expect(result).toEqual(mockResponse)
    })

    it('should include bank_code in FormData for credit card import', async () => {
      const mockResponse = {
        session_id: 'session-456',
        total_count: 5,
        date_range: { start: '2024-01-01', end: '2024-01-31' },
        transactions: [],
        duplicates: [],
        account_mappings: [],
        validation_errors: [],
        is_valid: true,
      }
      mockApiPostMultipart.mockResolvedValue(mockResponse)

      const bankCode = 'CATHAY'
      await importApi.createPreview(ledgerId, mockFile, ImportType.CREDIT_CARD, bankCode)

      const formData = mockApiPostMultipart.mock.calls[0][1] as FormData
      expect(formData.get('file')).toBe(mockFile)
      expect(formData.get('import_type')).toBe(ImportType.CREDIT_CARD)
      expect(formData.get('bank_code')).toBe(bankCode)
    })

    it('should propagate errors from apiPostMultipart', async () => {
      const error = new Error('Upload failed')
      mockApiPostMultipart.mockRejectedValue(error)

      await expect(importApi.createPreview(ledgerId, mockFile, ImportType.MYAB_CSV)).rejects.toThrow(
        'Upload failed'
      )
    })
  })

  describe('execute', () => {
    const ledgerId = 'ledger-123'
    const executeRequest = {
      session_id: 'session-123',
      account_mappings: [{ csv_name: 'E-餐飲', account_id: 'acc-1' }],
      skip_duplicate_rows: [2, 5],
    }

    it('should call apiPost with correct endpoint and data', async () => {
      const mockResponse = {
        success: true,
        imported_count: 10,
        skipped_count: 2,
        created_accounts: [],
      }
      mockApiPost.mockResolvedValue(mockResponse)

      const result = await importApi.execute(ledgerId, executeRequest)

      expect(mockApiPost).toHaveBeenCalledTimes(1)
      expect(mockApiPost).toHaveBeenCalledWith(
        `/ledgers/${ledgerId}/import/execute`,
        executeRequest
      )
      expect(result).toEqual(mockResponse)
    })

    it('should return created accounts when new accounts are created', async () => {
      const mockResponse = {
        success: true,
        imported_count: 8,
        skipped_count: 0,
        created_accounts: [
          { id: 'new-acc-1', name: '餐飲費', type: 'EXPENSE' },
          { id: 'new-acc-2', name: '交通費', type: 'EXPENSE' },
        ],
      }
      mockApiPost.mockResolvedValue(mockResponse)

      const result = await importApi.execute(ledgerId, executeRequest)

      expect(result.created_accounts).toHaveLength(2)
      expect(result.created_accounts[0].name).toBe('餐飲費')
    })

    it('should propagate errors from apiPost', async () => {
      const error = new Error('Import failed')
      mockApiPost.mockRejectedValue(error)

      await expect(importApi.execute(ledgerId, executeRequest)).rejects.toThrow('Import failed')
    })
  })

  describe('getHistory', () => {
    const ledgerId = 'ledger-123'

    it('should call apiGet with default pagination parameters', async () => {
      const mockResponse = {
        data: [
          { id: 'session-1', status: 'COMPLETED', imported_count: 10 },
          { id: 'session-2', status: 'COMPLETED', imported_count: 5 },
        ],
        total: 2,
      }
      mockApiGet.mockResolvedValue(mockResponse)

      const result = await importApi.getHistory(ledgerId)

      expect(mockApiGet).toHaveBeenCalledTimes(1)
      expect(mockApiGet).toHaveBeenCalledWith(`/ledgers/${ledgerId}/import/history?limit=20&offset=0`)
      expect(result).toEqual(mockResponse)
    })

    it('should call apiGet with custom pagination parameters', async () => {
      const mockResponse = { data: [], total: 0 }
      mockApiGet.mockResolvedValue(mockResponse)

      await importApi.getHistory(ledgerId, 50, 100)

      expect(mockApiGet).toHaveBeenCalledWith(`/ledgers/${ledgerId}/import/history?limit=50&offset=100`)
    })

    it('should propagate errors from apiGet', async () => {
      const error = new Error('Failed to fetch history')
      mockApiGet.mockRejectedValue(error)

      await expect(importApi.getHistory(ledgerId)).rejects.toThrow('Failed to fetch history')
    })
  })

  describe('getJobStatus', () => {
    it('should call apiGet with correct job endpoint', async () => {
      const jobId = 'job-123'
      const mockResponse = {
        status: 'PROCESSING',
        progress: { current: 50, total: 100 },
      }
      mockApiGet.mockResolvedValue(mockResponse)

      const result = await importApi.getJobStatus(jobId)

      expect(mockApiGet).toHaveBeenCalledTimes(1)
      expect(mockApiGet).toHaveBeenCalledWith(`/import/jobs/${jobId}`)
      expect(result).toEqual(mockResponse)
    })

    it('should return completed status with result', async () => {
      const jobId = 'job-456'
      const mockResponse = {
        status: 'COMPLETED',
        progress: { current: 100, total: 100 },
        result: {
          success: true,
          imported_count: 100,
          skipped_count: 0,
          created_accounts: [],
        },
      }
      mockApiGet.mockResolvedValue(mockResponse)

      const result = await importApi.getJobStatus(jobId)

      expect(result.status).toBe('COMPLETED')
      expect(result.result.imported_count).toBe(100)
    })

    it('should return failed status with error', async () => {
      const jobId = 'job-789'
      const mockResponse = {
        status: 'FAILED',
        error: 'Database connection failed',
      }
      mockApiGet.mockResolvedValue(mockResponse)

      const result = await importApi.getJobStatus(jobId)

      expect(result.status).toBe('FAILED')
      expect(result.error).toBe('Database connection failed')
    })
  })

  describe('getBanks', () => {
    it('should call apiGet with correct endpoint', async () => {
      const mockResponse = {
        banks: [
          { code: 'CATHAY', name: '國泰世華', encoding: 'utf-8' },
          { code: 'CTBC', name: '中國信託', encoding: 'utf-8' },
          { code: 'ESUN', name: '玉山銀行', encoding: 'utf-8' },
          { code: 'TAISHIN', name: '台新銀行', encoding: 'big5' },
          { code: 'FUBON', name: '富邦銀行', encoding: 'utf-8' },
        ],
      }
      mockApiGet.mockResolvedValue(mockResponse)

      const result = await importApi.getBanks()

      expect(mockApiGet).toHaveBeenCalledTimes(1)
      expect(mockApiGet).toHaveBeenCalledWith('/import/banks')
      expect(result.banks).toHaveLength(5)
    })

    it('should return bank configs with all required fields', async () => {
      const mockResponse = {
        banks: [{ code: 'CATHAY', name: '國泰世華', encoding: 'utf-8' }],
      }
      mockApiGet.mockResolvedValue(mockResponse)

      const result = await importApi.getBanks()

      expect(result.banks[0]).toEqual({
        code: 'CATHAY',
        name: '國泰世華',
        encoding: 'utf-8',
      })
    })

    it('should handle empty bank list', async () => {
      const mockResponse = { banks: [] }
      mockApiGet.mockResolvedValue(mockResponse)

      const result = await importApi.getBanks()

      expect(result.banks).toEqual([])
    })

    it('should propagate errors from apiGet', async () => {
      const error = new Error('Failed to fetch banks')
      mockApiGet.mockRejectedValue(error)

      await expect(importApi.getBanks()).rejects.toThrow('Failed to fetch banks')
    })
  })
})

describe('ImportType enum', () => {
  it('should have MYAB_CSV value', () => {
    expect(ImportType.MYAB_CSV).toBe('MYAB_CSV')
  })

  it('should have CREDIT_CARD value', () => {
    expect(ImportType.CREDIT_CARD).toBe('CREDIT_CARD')
  })
})
