/** Keep local development convenient without shipping a localhost production API. */
export function apiBaseUrl(configured: string | undefined, fallback = ''): string {
  return configured?.trim() || fallback
}
