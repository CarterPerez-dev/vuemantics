// ===================
// © AngelaMos | 2026
// auth.store.ts
// ===================

import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { UserResponse } from '@/api/types'
import { STORAGE_KEYS } from '@/config'

interface AuthState {
  user: UserResponse | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthActions {
  login: (user: UserResponse, accessToken: string) => void
  logout: () => void
  setLoading: (loading: boolean) => void
  setAccessToken: (token: string | null) => void
  setRefreshToken: (token: string | null) => void
  updateUser: (updates: Partial<UserResponse>) => void
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,

        login: (user, accessToken) =>
          set(
            {
              user,
              accessToken,
              isAuthenticated: true,
              isLoading: false,
            },
            false,
            'auth/login'
          ),

        logout: () =>
          set(
            {
              user: null,
              accessToken: null,
              refreshToken: null,
              isAuthenticated: false,
              isLoading: false,
            },
            false,
            'auth/logout'
          ),

        setLoading: (loading) =>
          set({ isLoading: loading }, false, 'auth/setLoading'),

        setAccessToken: (token) =>
          set({ accessToken: token }, false, 'auth/setAccessToken'),

        setRefreshToken: (token) =>
          set({ refreshToken: token }, false, 'auth/setRefreshToken'),

        updateUser: (updates) =>
          set(
            (state) => ({
              user: state.user !== null ? { ...state.user, ...updates } : null,
            }),
            false,
            'auth/updateUser'
          ),
      }),
      {
        name: STORAGE_KEYS.AUTH,
        partialize: (state) => ({
          user: state.user,
          accessToken: state.accessToken,
          refreshToken: state.refreshToken,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'AuthStore' }
  )
)

export const useUser = (): UserResponse | null => useAuthStore((s) => s.user)
export const useIsAuthenticated = (): boolean =>
  useAuthStore((s) => s.isAuthenticated)
export const useIsAuthLoading = (): boolean => useAuthStore((s) => s.isLoading)
export const useAccessToken = (): string | null =>
  useAuthStore((s) => s.accessToken)
export const useRefreshToken = (): string | null =>
  useAuthStore((s) => s.refreshToken)

export const useIsAdmin = (): boolean => {
  return false
}
