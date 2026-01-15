'use client'

import * as React from 'react'
import { format } from 'date-fns'
import { Calendar as CalendarIcon } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface DateRangePickerProps {
    className?: string
    startDate?: Date
    endDate?: Date
    onStartDateChange: (date: Date | undefined) => void
    onEndDateChange: (date: Date | undefined) => void
}

export function DateRangePicker({
    className,
    startDate,
    endDate,
    onStartDateChange,
    onEndDateChange,
}: DateRangePickerProps) {
    return (
        <div className={cn('flex items-center gap-2', className)}>
            <div className="relative">
                <Input
                    type="date"
                    value={startDate && !isNaN(startDate.getTime()) ? format(startDate, 'yyyy-MM-dd') : ''}
                    onChange={(e) => {
                        const date = e.target.value ? new Date(e.target.value) : undefined
                        onStartDateChange(date)
                    }}
                    className="w-[160px]"
                />
            </div>
            <span className="text-sm text-gray-500">-</span>
            <div className="relative">
                <Input
                    type="date"
                    value={endDate && !isNaN(endDate.getTime()) ? format(endDate, 'yyyy-MM-dd') : ''}
                    onChange={(e) => {
                        const date = e.target.value ? new Date(e.target.value) : undefined
                        onEndDateChange(date)
                    }}
                    className="w-[160px]"
                />
            </div>
        </div>
    )
}
