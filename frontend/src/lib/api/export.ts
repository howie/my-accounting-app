const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'

export interface ExportParams {
  format: 'csv' | 'html'
  start_date?: string
  end_date?: string
  account_id?: string
}

export async function exportTransactions(params: ExportParams): Promise<void> {
  const queryParams = new URLSearchParams()
  queryParams.append('format', params.format)

  if (params.start_date) queryParams.append('start_date', params.start_date)
  if (params.end_date) queryParams.append('end_date', params.end_date)
  if (params.account_id) queryParams.append('account_id', params.account_id)

  const url = `/export/transactions?${queryParams.toString()}`

  // Direct fetch to handle Blob response
  const response = await fetch(`${API_BASE_URL}${url}`, {
    method: 'GET',
    headers: {
        // 'Authorization': ... (Add when auth is implemented)
    },
  })

  if (!response.ok) {
    throw new Error('Export failed')
  }

  const blob = await response.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = downloadUrl

  // Try to get filename from Content-Disposition
  const disposition = response.headers.get('content-disposition')
  let filename = `export_${new Date().toISOString().slice(0,10)}.${params.format}`
  if (disposition && disposition.includes('attachment')) {
    const filenameRegex = new RegExp('filename[^;=\\n]*=((["\"]).*?\\2|[^;\\n]*)')
    const matches = filenameRegex.exec(disposition)
    if (matches != null && matches[1]) {
      filename = matches[1].replace(/['"]/g, '')
    }
  }

  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(downloadUrl)
}
