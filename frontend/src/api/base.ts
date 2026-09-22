// Interceptor-free API transport.
//
// Unlike the other modules in `src/api/` (which mirror backend route
// groups), this one holds the low-level transport that must not go
// through `client.ts`: the shared base URL and the bare axios instance
// used to refresh tokens. Keeping it here makes the import graph
// one-way — `client.ts` -> `base.ts` — instead of a cycle between
// `client.ts` and `auth.ts`.
import axios from 'axios'
import type { RefreshRequest, TokenResponse } from '../types/api'

export const API_BASE = import.meta.env.VITE_API_BASE ?? ''

// Deliberately interceptor-free: a refresh must not have a Bearer token
// injected, and a failed refresh must not trigger the 401 redirect (that
// would recurse through this very call).
const bare = axios.create({
  baseURL: API_BASE + '/api/v1',
})

export async function refreshAccessToken(refresh_token: string): Promise<TokenResponse> {
  const { data } = await bare.post<TokenResponse>('/auth/refresh', {
    refresh_token,
  } as RefreshRequest)
  return data
}
