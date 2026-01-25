// ===================
// © AngelaMos | 2026
// auth.types.ts
// ===================

import { z } from 'zod'
import { PASSWORD_CONSTRAINTS } from '@/config'

export const userResponseSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  is_active: z.boolean(),
  created_at: z.string(),
  updated_at: z.string().nullable(),
})

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
})

export const loginRequestSchema = z.object({
  username: z.string().email(),
  password: z
    .string()
    .min(PASSWORD_CONSTRAINTS.MIN_LENGTH)
    .max(PASSWORD_CONSTRAINTS.MAX_LENGTH),
})

export const registerRequestSchema = z.object({
  email: z.string().email(),
  password: z
    .string()
    .min(PASSWORD_CONSTRAINTS.MIN_LENGTH)
    .max(PASSWORD_CONSTRAINTS.MAX_LENGTH),
})

export const passwordChangeRequestSchema = z.object({
  current_password: z.string(),
  new_password: z
    .string()
    .min(PASSWORD_CONSTRAINTS.MIN_LENGTH)
    .max(PASSWORD_CONSTRAINTS.MAX_LENGTH),
})

export type UserResponse = z.infer<typeof userResponseSchema>
export type TokenResponse = z.infer<typeof tokenResponseSchema>
export type LoginRequest = z.infer<typeof loginRequestSchema>
export type RegisterRequest = z.infer<typeof registerRequestSchema>
export type PasswordChangeRequest = z.infer<typeof passwordChangeRequestSchema>

export const isValidUserResponse = (data: unknown): data is UserResponse => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const result = userResponseSchema.safeParse(data)
  return result.success
}

export const isValidTokenResponse = (data: unknown): data is TokenResponse => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const result = tokenResponseSchema.safeParse(data)
  return result.success
}

export class AuthResponseError extends Error {
  readonly endpoint?: string

  constructor(message: string, endpoint?: string) {
    super(message)
    this.name = 'AuthResponseError'
    this.endpoint = endpoint
    Object.setPrototypeOf(this, AuthResponseError.prototype)
  }
}

export const AUTH_ERROR_MESSAGES = {
  INVALID_USER_RESPONSE: 'Invalid user data from server',
  INVALID_LOGIN_RESPONSE: 'Invalid login response from server',
  INVALID_TOKEN_RESPONSE: 'Invalid token response from server',
  NO_REFRESH_TOKEN: 'No refresh token available',
  SESSION_EXPIRED: 'Session expired',
} as const

export const AUTH_SUCCESS_MESSAGES = {
  WELCOME_BACK: 'Welcome back!',
  LOGOUT_SUCCESS: 'Logged out successfully',
  PASSWORD_CHANGED: 'Password changed successfully',
  REGISTERED: 'Account created successfully! You can now log in.',
} as const

export type AuthErrorMessage =
  (typeof AUTH_ERROR_MESSAGES)[keyof typeof AUTH_ERROR_MESSAGES]
export type AuthSuccessMessage = typeof AUTH_SUCCESS_MESSAGES
