// Axios instance with JWT injection, silent token refresh and 401 handling
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../store/auth'
import { API_BASE, refreshAccessToken } from './base'

// Refresh the access token this long before it actually expires.
const REFRESH_SKEW_MS = 60_000

// Requests that must never trigger a refresh of their own.
const AUTH_PATHS = ['/auth/login', '/auth/refresh']

const api = axios.create({
  baseURL: API_BASE + '/api/v1',
})

// A request we have already retried once after a refresh; the flag stops
// a failing endpoint from looping through refresh forever.
interface RetriedRequestConfig extends InternalAxiosRequestConfig {
  _retried?: boolean
}

// Single shared in-flight refresh, so N parallel requests result in
// exactly one call to /auth/refresh and all of them wait on it.
let refreshInFlight: Promise<string | null> | null = null

function isAuthPath(url: string | undefined): boolean {
  return url !== undefined && AUTH_PATHS.some((path) => url.includes(path))
}

// Resolves to the new access token, or null when the session is genuinely
// dead — no refresh token stored, or /auth/refresh answered 401.
//
// Any other failure (network drop, 5xx, cold-start 502, timeout) is
// rethrown rather than reported as a dead session: the stored refresh
// token stays valid and the caller sees an ordinary request failure.
async function runRefresh(): Promise<string | null> {
  const auth = useAuthStore()
  const refresh_token = auth.refresh_token
  if (!refresh_token) return null
  // Captured before awaiting: if the user logs out (or logs in again)
  // while the refresh is in flight, the epoch changes and the tokens we
  // get back must be thrown away instead of re-authenticating them.
  const epoch = auth.session_epoch
  try {
    const tokens = await refreshAccessToken(refresh_token)
    if (auth.session_epoch !== epoch) return null
    auth.setTokens(tokens)
    return tokens.access_token
  } catch (e) {
    if (axios.isAxiosError(e) && e.response?.status === 401) return null
    throw e
  }
}

function ensureFreshToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = runRefresh().finally(() => {
      refreshInFlight = null
    })
  }
  return refreshInFlight
}

function logout(): void {
  refreshInFlight = null
  useAuthStore().clearAuth()
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

// Request interceptor: refresh a missing/expired/expiring token first,
// then inject the JWT
api.interceptors.request.use(async (config) => {
  const auth = useAuthStore()
  if (!isAuthPath(config.url) && auth.accessTokenNeedsRefresh(REFRESH_SKEW_MS)) {
    const token = await ensureFreshToken()
    if (!token) {
      logout()
      // A cancellation, not an error: the redirect to /login is the whole
      // user-visible outcome, so views must not flash a red banner.
      throw new axios.CanceledError('Session expired')
    }
  }
  if (auth.token) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${auth.token}`
  }
  return config
})

// Response interceptor: on a 401, refresh once and retry the request
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetriedRequestConfig | undefined
    if (error.response?.status !== 401 || !config || isAuthPath(config.url)) {
      return Promise.reject(error)
    }
    if (!config._retried) {
      config._retried = true
      const auth = useAuthStore()
      const sent = config.headers?.['Authorization']
      // A parallel request may already have refreshed while this one was
      // in flight; replay with the stored token instead of refreshing
      // a second time for nothing.
      if (
        auth.token &&
        sent !== `Bearer ${auth.token}` &&
        !auth.accessTokenNeedsRefresh(0)
      ) {
        return api(config)
      }
      const token = await ensureFreshToken()
      if (token) {
        return api(config)
      }
    }
    logout()
    // Same as the request interceptor: the redirect to /login is the
    // whole user-visible outcome, so reject silently.
    return Promise.reject(new axios.CanceledError('Session expired'))
  },
)

export default api
