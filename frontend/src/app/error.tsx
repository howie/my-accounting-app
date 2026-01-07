'use client'

import { useEffect } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorPageProps {
  error: Error & { digest?: string }
  reset: () => void
}

/**
 * Global error page for unhandled errors.
 */
export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error('Global error:', error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 bg-background">
      <AlertTriangle className="h-16 w-16 text-yellow-500 mb-6" />
      <h1 className="text-2xl font-bold text-foreground mb-2">
        Something went wrong
      </h1>
      <p className="text-muted-foreground text-center max-w-md mb-6">
        An unexpected error occurred. Our team has been notified.
      </p>
      {error.message && (
        <p className="text-sm text-red-500 font-mono mb-6 p-3 bg-red-50 dark:bg-red-950 rounded-md">
          {error.message}
        </p>
      )}
      <div className="flex gap-4">
        <Button onClick={reset} variant="default">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
        <Button onClick={() => window.location.href = '/'} variant="outline">
          <Home className="h-4 w-4 mr-2" />
          Go Home
        </Button>
      </div>
    </div>
  )
}
