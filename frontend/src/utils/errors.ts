// Extract a human-readable message from an API error.
// FastAPI returns errors as { detail: "..." }; axios nests that under
// error.response.data.detail. Falls back to the Error message, then a generic.
export function apiErrorMessage(
  error: unknown,
  fallback = 'Something went wrong. Please try again.',
): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } })
      .response?.data?.detail
    if (typeof detail === 'string' && detail.trim()) return detail
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}
