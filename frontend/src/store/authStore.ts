import { create } from 'zustand'

interface User {
  id: string
  email: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setAuth: (user: User, token: string) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  
  login: async (email: string, password: string) => {
    // Implementation will be added
  },
  
  logout: () => {
    localStorage.removeItem('access_token')
    set({ user: null, token: null, isAuthenticated: false })
  },
  
  setAuth: (user: User, token: string) => {
    localStorage.setItem('access_token', token)
    set({ user, token, isAuthenticated: true })
  },
}))
