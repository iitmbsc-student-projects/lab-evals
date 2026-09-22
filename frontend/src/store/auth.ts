// Pinia store for authentication and user state
import { defineStore } from 'pinia'
import type { TokenResponse, UserResponse } from '../types/api'

interface AuthState {
  token: string | null
  refresh_token: string | null
  // Access-token expiry as epoch milliseconds, read from the JWT `exp`
  // claim (and persisted, so a token whose `exp` we cannot decode still
  // has its `expires_in` fallback after a reload).
  expires_at: number | null
  is_admin: boolean
  user: UserResponse | null
  // Bumped on every clearAuth. An async refresh captures it before
  // awaiting and discards its result if it changed meanwhile, so a
  // logout can never be undone by a refresh that was already in flight.
  session_epoch: number
}

interface PersistedAuth {
  token?: unknown
  refresh_token?: unknown
  expires_at?: unknown
  is_admin?: unknown
  user?: unknown
}

// Reads the `exp` claim of a JWT and returns it as epoch milliseconds.
// Returns null for anything that is not a decodable JWT with an `exp`.
function jwtExpiryMs(token: string): number | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    const claims: unknown = JSON.parse(json)
    if (typeof claims !== 'object' || claims === null) return null
    const exp = (claims as { exp?: unknown }).exp
    return typeof exp === 'number' ? exp * 1000 : null
  } catch {
    return null
  }
}

function readStoredAuth(): string | null {
  try {
    return localStorage.getItem('auth')
  } catch {
    return null
  }
}

type HydratedAuth = Pick<
  AuthState,
  'token' | 'refresh_token' | 'expires_at' | 'is_admin' | 'user'
>

const EMPTY_AUTH: HydratedAuth = {
  token: null,
  refresh_token: null,
  expires_at: null,
  is_admin: false,
  user: null,
}

// Parses a persisted `auth` blob. A blob written before refresh tokens
// existed has no refresh_token, so it cannot be refreshed — but its
// expires_at is still recovered from the old access token's `exp`, so the
// session stays usable until that token nears expiry and only then forces
// one clean re-login.
function hydrate(raw: string | null): HydratedAuth {
  if (!raw) return { ...EMPTY_AUTH }
  try {
    const parsed: PersistedAuth = JSON.parse(raw)
    const token = typeof parsed.token === 'string' ? parsed.token : null
    return {
      token,
      refresh_token: typeof parsed.refresh_token === 'string' ? parsed.refresh_token : null,
      // Prefer the token's own `exp`; fall back to the persisted value,
      // which is where an `expires_in`-derived expiry survives a reload.
      expires_at:
        (token ? jwtExpiryMs(token) : null) ??
        (typeof parsed.expires_at === 'number' ? parsed.expires_at : null),
      is_admin: parsed.is_admin === true,
      user: (parsed.user as UserResponse | null) ?? null,
    }
  } catch {
    return { ...EMPTY_AUTH }
  }
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    ...hydrate(readStoredAuth()),
    session_epoch: 0,
  }),
  getters: {
    // True when there is no usable access token, or it expires within
    // `skewMs` and should be refreshed ahead of the next request.
    accessTokenNeedsRefresh:
      (state) =>
      (skewMs: number): boolean => {
        if (!state.token) return true
        if (state.expires_at === null) return true
        return state.expires_at - skewMs <= Date.now()
      },
  },
  actions: {
    persist() {
      localStorage.setItem(
        'auth',
        JSON.stringify({
          token: this.token,
          refresh_token: this.refresh_token,
          expires_at: this.expires_at,
          is_admin: this.is_admin,
          user: this.user,
        }),
      )
    },
    setTokens(tokens: TokenResponse) {
      this.token = tokens.access_token
      this.refresh_token = tokens.refresh_token
      this.expires_at = jwtExpiryMs(tokens.access_token) ?? Date.now() + tokens.expires_in * 1000
      this.persist()
    },
    setAuth(user: UserResponse) {
      this.is_admin = user.is_admin
      this.user = user
      this.persist()
    },
    clearAuth() {
      this.token = null
      this.refresh_token = null
      this.expires_at = null
      this.is_admin = false
      this.user = null
      this.session_epoch += 1
      localStorage.removeItem('auth')
    },
    // Adopts an `auth` blob written by another tab. Deliberately does not
    // re-persist: the value already is what is in localStorage.
    adoptStoredAuth(raw: string) {
      Object.assign(this, hydrate(raw))
    },
  },
})

// Cross-tab sync, registered once at module load: without it a second tab
// keeps a stale token forever — still issuing authenticated requests after
// tab A logged out, or refreshing with an already-rotated refresh token.
// The store is resolved lazily inside the handler, by which time pinia is
// installed (storage events only fire long after app start).
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key !== 'auth') return
    const auth = useAuthStore()
    if (event.newValue === null) {
      auth.clearAuth()
      return
    }
    auth.adoptStoredAuth(event.newValue)
  })
}
