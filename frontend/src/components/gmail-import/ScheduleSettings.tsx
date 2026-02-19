'use client'

import { useCallback, useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { gmailImportApi, ScheduleFrequency, ScheduleSettingsResponse } from '@/lib/api/gmail-import'

interface ScheduleSettingsProps {
  ledgerId: string
}

const DAYS_OF_WEEK = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
  'sunday',
] as const

export default function ScheduleSettings({ ledgerId }: ScheduleSettingsProps) {
  const t = useTranslations('gmailImport')

  const [schedule, setSchedule] = useState<ScheduleSettingsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [frequency, setFrequency] = useState<ScheduleFrequency | ''>('')
  const [hour, setHour] = useState<number>(6)
  const [dayOfWeek, setDayOfWeek] = useState<number>(0)

  const fetchSchedule = useCallback(async () => {
    try {
      setLoading(true)
      const response = await gmailImportApi.getSchedule(ledgerId)
      setSchedule(response)
      setFrequency(response.frequency || '')
      setHour(response.hour ?? 6)
      setDayOfWeek(response.day_of_week ?? 0)
    } catch {
      setError(t('schedule.fetchError'))
    } finally {
      setLoading(false)
    }
  }, [ledgerId, t])

  useEffect(() => {
    fetchSchedule()
  }, [fetchSchedule])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const data = frequency
        ? {
            frequency: frequency as ScheduleFrequency,
            hour,
            day_of_week: frequency === ScheduleFrequency.WEEKLY ? dayOfWeek : undefined,
          }
        : { frequency: null as ScheduleFrequency | null }

      const response = await gmailImportApi.updateSchedule(ledgerId, data)
      setSchedule(response)
    } catch {
      setError(t('schedule.saveError'))
    } finally {
      setSaving(false)
    }
  }

  const handleDisable = async () => {
    setSaving(true)
    setError(null)
    try {
      const response = await gmailImportApi.updateSchedule(ledgerId, {
        frequency: null as ScheduleFrequency | null,
      })
      setSchedule(response)
      setFrequency('')
    } catch {
      setError(t('schedule.saveError'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-10 rounded-lg bg-gray-200" />
        <div className="h-10 rounded-lg bg-gray-200" />
      </div>
    )
  }

  const hasChanges =
    (frequency || '') !== (schedule?.frequency || '') ||
    (frequency && hour !== (schedule?.hour ?? 6)) ||
    (frequency === ScheduleFrequency.WEEKLY && dayOfWeek !== (schedule?.day_of_week ?? 0))

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3">
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* Frequency selection */}
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">
          {t('schedule.frequency')}
        </label>
        <select
          value={frequency}
          onChange={(e) => setFrequency(e.target.value as ScheduleFrequency | '')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">{t('schedule.disabled')}</option>
          <option value={ScheduleFrequency.DAILY}>{t('schedule.daily')}</option>
          <option value={ScheduleFrequency.WEEKLY}>{t('schedule.weekly')}</option>
        </select>
      </div>

      {/* Hour selection */}
      {frequency && (
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            {t('schedule.hour')}
          </label>
          <select
            value={hour}
            onChange={(e) => setHour(parseInt(e.target.value, 10))}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {Array.from({ length: 24 }, (_, i) => (
              <option key={i} value={i}>
                {String(i).padStart(2, '0')}:00
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Day of week selection (weekly only) */}
      {frequency === ScheduleFrequency.WEEKLY && (
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            {t('schedule.dayOfWeek')}
          </label>
          <select
            value={dayOfWeek}
            onChange={(e) => setDayOfWeek(parseInt(e.target.value, 10))}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {DAYS_OF_WEEK.map((day, i) => (
              <option key={day} value={i}>
                {t(`schedule.days.${day}`)}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Next scan info */}
      {schedule?.next_scan_at && (
        <div className="flex items-center gap-2 rounded-lg border border-blue-100 bg-blue-50 p-3">
          <svg
            className="h-4 w-4 text-blue-600"
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
          <span className="text-sm text-blue-800">
            {t('schedule.nextScan')}: {new Date(schedule.next_scan_at).toLocaleString()}
          </span>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !hasChanges}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? t('schedule.saving') : t('schedule.save')}
        </button>
        {schedule?.frequency && (
          <button
            onClick={handleDisable}
            disabled={saving}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {t('schedule.disable')}
          </button>
        )}
      </div>
    </div>
  )
}
