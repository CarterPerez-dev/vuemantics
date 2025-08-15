import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '@/api/client'
import { useAuthStore } from '@/store/authStore'
import type {
  User,
  LoginCredentials,
  RegisterData,
  TokenResponse,
  RefreshTokenRequest,
  ApiError,
} from '@/types'

// Custom hook for authentication
export const useAuth = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { setAuth, logout: logoutStore, user } = useAuthStore()

  // Register mutation
  const register = useMutation<User, Error, RegisterData>({
    mutationFn: async (data) => {
      const response = await apiClient.post('/api/auth/register', data)
      return response.data
    },
    onSuccess: () => {
      // After successful registration, user needs to login
      navigate('/login')
    },
    onError: (error: any) => {
      console.error('Registration failed:', error.response?.data || error.message)
    },
  })

  // Login mutation
  const login = useMutation<TokenResponse, Error, LoginCredentials>({
    mutationFn: async (credentials) => {
      // OAuth2 expects form data, not JSON
      const formData = new URLSearchParams()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await apiClient.post('/api/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
      return response.data
    },
    onSuccess: async (data) => {
      // Store tokens
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)

      // Fetch user data
      try {
        const userResponse = await apiClient.get<User>('/api/auth/me')
        setAuth(userResponse.data, data.access_token)
        navigate('/dashboard')
      } catch (error) {
        console.error('Failed to fetch user data:', error)
      }
    },
    onError: (error: ApiError) => {
      console.error('Login failed:', error.response?.data || error.message)
    },
  })

  // Get current user query
  const { data: currentUser, isLoading: isLoadingUser } = useQuery<User>({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await apiClient.get('/api/auth/me')
      return response.data
    },
    enabled: !!localStorage.getItem('access_token'),
    retry: false,
    onError: () => {
      // If fetching user fails, clear auth
      logoutStore()
    },
  })

  // Refresh token mutation
  const refreshToken = useMutation<TokenResponse, Error, RefreshTokenRequest>({
    mutationFn: async (data) => {
      const response = await apiClient.post('/api/auth/token/refresh', data)
      return response.data
    },
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token)
      // Refresh token stays the same (30 day validity)
    },
  })

  // Logout function
  const logout = () => {
    logoutStore()
    queryClient.clear()
    navigate('/login')
  }

  // Auto-refresh logic
  const setupTokenRefresh = () => {
    // Check token expiry and refresh if needed
    const checkAndRefresh = async () => {
      const refreshTokenValue = localStorage.getItem('refresh_token')
      const accessToken = localStorage.getItem('access_token')
      
      if (!refreshTokenValue || !accessToken) return

      try {
        // Decode token to check expiry (without verification since we just need the exp claim)
        const payload = JSON.parse(atob(accessToken.split('.')[1]))
        const expiresAt = payload.exp * 1000 // Convert to milliseconds
        const now = Date.now()
        const timeUntilExpiry = expiresAt - now
        
        // Refresh if less than 5 minutes until expiry
        if (timeUntilExpiry < 5 * 60 * 1000) {
          console.log('Access token expiring soon, refreshing...')
          await refreshToken.mutateAsync({ refresh_token: refreshTokenValue })
        }
      } catch (error) {
        console.error('Token check/refresh failed:', error)
        // Don't logout on decode error, just skip this check
      }
    }

    // Check immediately on setup
    checkAndRefresh()

    // Then check every minute
    const refreshInterval = setInterval(checkAndRefresh, 60 * 1000) // 1 minute

    return () => clearInterval(refreshInterval)
  }

  return {
    // Auth state
    user: currentUser || user,
    isAuthenticated: !!localStorage.getItem('access_token'),
    isLoadingUser,

    // Auth actions
    register,
    login,
    logout,
    refreshToken,
    setupTokenRefresh,

    // Mutation states
    isRegistering: register.isPending,
    isLoggingIn: login.isPending,
    registerError: register.error,
    loginError: login.error,
  }
}
