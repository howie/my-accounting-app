import { getRequestConfig } from 'next-intl/server'

export default getRequestConfig(async () => {
  // Default to zh-TW (Traditional Chinese)
  const locale = 'zh-TW'

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  }
})
