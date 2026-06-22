// Auth API: Handles login and user info fetch
import api from './client'
import type { TokenRequest, TokenResponse, UserResponse, MySession } from '../types/api'

export async function loginWithIdToken(id_token: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>('/auth/login', { id_token } as TokenRequest)
  return data
}

export async function fetchMe(): Promise<UserResponse> {
  const { data } = await api.get<UserResponse>('/user/me')
  return data
}

export async function getMySessions(): Promise<MySession[]> {
  const { data } = await api.get<MySession[]>('/user/me/sessions')
  return data
}
