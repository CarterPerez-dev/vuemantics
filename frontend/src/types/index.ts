/**
 * Central export for all TypeScript types
 * 
 * Usage:
 * import { User, Upload, SearchRequest } from '@/types'
 */

// Re-export everything from models
export * from './models'

// Re-export everything from api
export * from './api'

// Common type utilities
export type Nullable<T> = T | null
export type Optional<T> = T | undefined
export type AsyncFunction<T = void> = () => Promise<T>

// API Error type helper
export type ApiError = {
  response?: {
    data?: {
      detail?: string
      errors?: Array<{
        field: string
        message: string
        type: string
      }>
    }
    status?: number
  }
  message: string
}

// Form state helpers
export interface FormState<T> {
  data: T
  errors: Partial<Record<keyof T, string>>
  isSubmitting: boolean
}

// File validation constants (matching backend)
export const ALLOWED_IMAGE_TYPES = [
  'image/jpeg',
  'image/jpg', 
  'image/png',
  'image/webp',
  'image/heic',
  'image/heif',
] as const

export const ALLOWED_VIDEO_TYPES = [
  'video/mp4',
  'video/mpeg',
  'video/quicktime',
  'video/x-msvideo',
  'video/x-flv',
  'video/webm',
] as const

export const MAX_FILE_SIZE = 104_857_600 // 100MB in bytes

export type AllowedImageType = typeof ALLOWED_IMAGE_TYPES[number]
export type AllowedVideoType = typeof ALLOWED_VIDEO_TYPES[number]
export type AllowedMimeType = AllowedImageType | AllowedVideoType
