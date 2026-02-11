'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import GmailConnectButton from '@/components/gmail-import/GmailConnectButton';
import { gmailImportApi, GmailConnectionResponse } from '@/lib/api/gmail-import';

export default function GmailImportSettingsPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const t = useTranslations('gmailImport');
  const ledgerId = (params?.ledgerId ?? '') as string;
  const idValue = Array.isArray(ledgerId) ? ledgerId[0] : ledgerId;

  const [connection, setConnection] = useState<GmailConnectionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check for success/error from OAuth callback
  const connected = searchParams?.get('connected');
  const authError = searchParams?.get('error');

  const fetchConnection = async () => {
    try {
      setLoading(true);
      const response = await gmailImportApi.getConnection();
      setConnection(response);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch Gmail connection:', err);
      setError(t('errors.fetchFailed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnection();
  }, []);

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Link href={`/ledgers/${idValue}`} className="hover:text-gray-700">
            {t('ledger')}
          </Link>
          <span>/</span>
          <span>{t('gmailImport')}</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">{t('settingsTitle')}</h1>
        <p className="text-gray-500">{t('settingsSubtitle')}</p>
      </div>

      {/* Success message from OAuth callback */}
      {connected === 'true' && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span className="text-green-800">{t('connectionSuccess')}</span>
          </div>
        </div>
      )}

      {/* Error message from OAuth callback */}
      {authError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            <span className="text-red-800">
              {t('authError')}: {authError}
            </span>
          </div>
        </div>
      )}

      {/* Gmail Connection Section */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('gmailConnection')}</h2>

        {loading ? (
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-10 bg-gray-200 rounded w-40"></div>
          </div>
        ) : error ? (
          <div className="text-red-600">{error}</div>
        ) : (
          <GmailConnectButton
            ledgerId={idValue}
            connection={connection}
            onConnectionChange={fetchConnection}
          />
        )}
      </div>

      {/* Quick Actions */}
      {connection && (
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('quickActions')}</h2>
          <div className="space-y-3">
            <Link
              href={`/${params?.locale}/ledgers/${idValue}/gmail-import`}
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <svg
                className="w-5 h-5 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <div>
                <div className="font-medium text-gray-900">{t('scanStatements')}</div>
                <div className="text-sm text-gray-500">{t('scanStatementsDesc')}</div>
              </div>
            </Link>

            <Link
              href={`/${params?.locale}/ledgers/${idValue}/gmail-import/history`}
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <svg
                className="w-5 h-5 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <div className="font-medium text-gray-900">{t('viewHistory')}</div>
                <div className="text-sm text-gray-500">{t('viewHistoryDesc')}</div>
              </div>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
