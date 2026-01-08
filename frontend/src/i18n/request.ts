import { getRequestConfig } from 'next-intl/server'
import { cookies } from 'next/headers'
import { defaultLocale, locales, type Locale } from './config'

const LOCALE_COOKIE = 'NEXT_LOCALE'

export default getRequestConfig(async () => {
  // Read locale from cookie, fallback to default
  const cookieStore = await cookies()
  const cookieLocale = cookieStore.get(LOCALE_COOKIE)?.value as Locale | undefined

  // Validate the locale
  const locale = cookieLocale && locales.includes(cookieLocale) ? cookieLocale : defaultLocale

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  }
})
