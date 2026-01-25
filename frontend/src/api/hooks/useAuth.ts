// ===================
// © AngelaMos | 2025
// useAuth.ts
// ===================

import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  AUTH_ERROR_MESSAGES,
  AUTH_SUCCESS_MESSAGES,
  AuthResponseError,
  isValidTokenResponse,
  isValidUserResponse,
  type LoginRequest,
  type RegisterRequest,
  type TokenResponse,
  type UserResponse,
} from '@/api/types'
import { API_ENDPOINTS, QUERY_KEYS, ROUTES } from '@/config'
import { apiClient, QUERY_STRATEGIES } from '@/core/api'
import { useAuthStore } from '@/core/lib'

export const authQueries = {
  all: () => QUERY_KEYS.AUTH.ALL,
  me: () => QUERY_KEYS.AUTH.ME(),
} as const

const fetchCurrentUser = async (): Promise<UserResponse> => {
  const response = await apiClient.get<unknown>(API_ENDPOINTS.AUTH.ME)
  const data: unknown = response.data

  if (!isValidUserResponse(data)) {
    throw new AuthResponseError(
      AUTH_ERROR_MESSAGES.INVALID_USER_RESPONSE,
      API_ENDPOINTS.AUTH.ME
    )
  }

  return data
}

export const useCurrentUser = (): UseQueryResult<UserResponse, Error> => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return useQuery({
    queryKey: authQueries.me(),
    queryFn: fetchCurrentUser,
    enabled: isAuthenticated,
    ...QUERY_STRATEGIES.auth,
  })
}

const performRegister = async (data: RegisterRequest): Promise<UserResponse> => {
  const response = await apiClient.post<unknown>(
    API_ENDPOINTS.AUTH.REGISTER,
    data
  )

  const responseData: unknown = response.data

  if (!isValidUserResponse(responseData)) {
    throw new AuthResponseError(
      AUTH_ERROR_MESSAGES.INVALID_USER_RESPONSE,
      API_ENDPOINTS.AUTH.REGISTER
    )
  }

  return responseData
}

export const useRegister = (): UseMutationResult<
  UserResponse,
  Error,
  RegisterRequest
> => {
  return useMutation({
    mutationFn: performRegister,
    onSuccess: (): void => {
      toast.success(AUTH_SUCCESS_MESSAGES.REGISTERED)
    },
    onError: (error: Error): void => {
      const message =
        error instanceof AuthResponseError ? error.message : 'Registration failed'
      toast.error(message)
    },
  })
}

const performLogin = async (
  credentials: LoginRequest
): Promise<TokenResponse> => {
  const formData = new URLSearchParams()
  formData.append('username', credentials.username)
  formData.append('password', credentials.password)

  const response = await apiClient.post<unknown>(
    API_ENDPOINTS.AUTH.LOGIN,
    formData,
    {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }
  )

  const data: unknown = response.data

  if (!isValidTokenResponse(data)) {
    throw new AuthResponseError(
      AUTH_ERROR_MESSAGES.INVALID_LOGIN_RESPONSE,
      API_ENDPOINTS.AUTH.LOGIN
    )
  }

  return data
}

export const useLogin = (): UseMutationResult<
  TokenResponse,
  Error,
  LoginRequest
> => {
  const queryClient = useQueryClient()
  const { login, setAccessToken, setRefreshToken } = useAuthStore()

  return useMutation({
    mutationFn: performLogin,
    onSuccess: async (data: TokenResponse): Promise<void> => {
      setAccessToken(data.access_token)
      setRefreshToken(data.refresh_token)

      const userResponse = await apiClient.get<unknown>(API_ENDPOINTS.AUTH.ME)
      const userData: unknown = userResponse.data

      if (isValidUserResponse(userData)) {
        login(userData, data.access_token)
        queryClient.setQueryData(authQueries.me(), userData)
        toast.success(AUTH_SUCCESS_MESSAGES.WELCOME_BACK)
      }
    },
    onError: (error: Error): void => {
      const message =
        error instanceof AuthResponseError ? error.message : 'Login failed'
      toast.error(message)
    },
  })
}

export const useLogout = (): (() => void) => {
  const queryClient = useQueryClient()
  const logout = useAuthStore((s) => s.logout)

  return (): void => {
    logout()
    queryClient.removeQueries({ queryKey: authQueries.all() })
    toast.success(AUTH_SUCCESS_MESSAGES.LOGOUT_SUCCESS)
    window.location.href = ROUTES.LOGIN
  }
}

export const useRefreshAuth = (): (() => Promise<void>) => {
  const queryClient = useQueryClient()
  const { setAccessToken, setRefreshToken, login, logout } = useAuthStore()

  return async (): Promise<void> => {
    try {
      const response = await apiClient.post<unknown>(API_ENDPOINTS.AUTH.REFRESH)
      const data: unknown = response.data

      if (!isValidTokenResponse(data)) {
        throw new AuthResponseError(
          AUTH_ERROR_MESSAGES.INVALID_TOKEN_RESPONSE,
          API_ENDPOINTS.AUTH.REFRESH
        )
      }

      setAccessToken(data.access_token)
      setRefreshToken(data.refresh_token)

      const userResponse = await apiClient.get<unknown>(API_ENDPOINTS.AUTH.ME)
      const userData: unknown = userResponse.data

      if (isValidUserResponse(userData)) {
        login(userData, data.access_token)
        queryClient.setQueryData(authQueries.me(), userData)
      }
    } catch {
      logout()
      queryClient.removeQueries({ queryKey: authQueries.all() })
    }
  }
}
