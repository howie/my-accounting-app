'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import {
  gmailImportApi,
  GmailConnectionResponse,
  GmailConnectionStatus,
} from '@/lib/api/gmail-import'

interface GmailConnectButtonProps {
  ledgerId: string
  connection: GmailConnectionResponse | null
  onConnectionChange: () => void
}

export default function GmailConnectButton({
  ledgerId,
  connection,
  onConnectionChange,
}: GmailConnectButtonProps) {
  const t = useTranslations('gmailImport')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleConnect = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await gmailImportApi.initiateConnect(ledgerId)
      // Redirect to Google OAuth2 consent page
      window.location.href = response.auth_url
    } catch (err) {
      console.error('Failed to initiate Gmail connection:', err)
      setError(t('errors.connectFailed'))
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    if (!confirm(t('confirmDisconnect'))) {
      return
    }

    setLoading(true)
    setError(null)
    try {
      await gmailImportApi.disconnect(ledgerId)
      onConnectionChange()
    } catch (err) {
      console.error('Failed to disconnect Gmail:', err)
      setError(t('errors.disconnectFailed'))
    } finally {
      setLoading(false)
    }
  }

  const isConnected = connection?.status === GmailConnectionStatus.CONNECTED
  const isExpired = connection?.status === GmailConnectionStatus.EXPIRED

  if (isConnected) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-green-500" />
          <span className="text-sm text-gray-600">{t('connectedAs')}</span>
          <span className="font-medium">{connection.email_address}</span>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          onClick={handleDisconnect}
          disabled={loading}
          className="rounded-md border border-red-300 px-4 py-2 text-sm text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? t('disconnecting') : t('disconnect')}
        </button>
      </div>
    )
  }

  if (isExpired) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 rounded-full bg-yellow-500" />
          <span className="text-sm text-yellow-700">{t('connectionExpired')}</span>
        </div>
        <p className="text-sm text-gray-600">{connection?.email_address}</p>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          onClick={handleConnect}
          disabled={loading}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? t('reconnecting') : t('reconnect')}
        </button>
      </div>
    )
  }

  // Not connected
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600">{t('notConnected')}</p>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        onClick={handleConnect}
        disabled={loading}
        className="flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <svg className="h-5 w-5" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          />
        </svg>
        {loading ? t('connecting') : t('connectGmail')}
      </button>
    </div>
  )
}
