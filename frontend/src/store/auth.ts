// Pinia store for authentication and user state
import { defineStore } from 'pinia'
import type { UserResponse } from '../types/api'

interface AuthState {
  token: string | null
  is_admin: boolean
  user: UserResponse | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => {
    let token = null,
      is_admin = false,
      user = null
    try {
      const raw = localStorage.getItem('auth')
      if (raw) {
        const parsed = JSON.parse(raw)
        token = parsed.token || null
        is_admin = parsed.is_admin || false
        user = parsed.user || null
      }
    } catch {}
    return { token, is_admin, user }
  },
  actions: {
    setAuth(token: string, user: UserResponse) {
      this.token = token
      this.is_admin = user.is_admin
      this.user = user
      localStorage.setItem('auth', JSON.stringify({ token, is_admin: user.is_admin, user }))
    },
    clearAuth() {
      this.token = null
      this.is_admin = false
      this.user = null
      localStorage.removeItem('auth')
    },
  },
})
