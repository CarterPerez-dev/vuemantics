/**
 * Validation utilities for the application
 */

import { 
  ALLOWED_IMAGE_TYPES, 
  ALLOWED_VIDEO_TYPES, 
  MAX_FILE_SIZE 
} from '@/types'

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate password strength
 */
export function validatePassword(password: string): {
  isValid: boolean
  errors: string[]
} {
  const errors: string[] = []
  
  if (password.length < 8) {
    errors.push('At least 8 characters long')
  }
  if (password.length > 69) {
    errors.push('Maximum 69 characters')
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('One uppercase letter')
  }
  if (!/[a-z]/.test(password)) {
    errors.push('One lowercase letter')
  }
  if (!/\d/.test(password)) {
    errors.push('One number')
  }
  if (!/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password)) {
    errors.push('One special character')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Validate file type
 */
export function isValidFileType(file: File): boolean {
  const allowedTypes = [...ALLOWED_IMAGE_TYPES, ...ALLOWED_VIDEO_TYPES]
  return allowedTypes.includes(file.type as any)
}

/**
 * Validate file size
 */
export function isValidFileSize(file: File): boolean {
  return file.size <= MAX_FILE_SIZE
}

/**
 * Get file type category
 */
export function getFileTypeCategory(file: File): 'image' | 'video' | 'unknown' {
  if (ALLOWED_IMAGE_TYPES.includes(file.type as any)) return 'image'
  if (ALLOWED_VIDEO_TYPES.includes(file.type as any)) return 'video'
  return 'unknown'
}

/**
 * Validate multiple files
 */
export function validateFiles(files: File[]): {
  valid: File[]
  invalid: Array<{ file: File; error: string }>
} {
  const valid: File[] = []
  const invalid: Array<{ file: File; error: string }> = []
  
  for (const file of files) {
    if (!isValidFileType(file)) {
      invalid.push({ file, error: 'Unsupported file type' })
    } else if (!isValidFileSize(file)) {
      invalid.push({ file, error: 'File too large (max 100MB)' })
    } else {
      valid.push(file)
    }
  }
  
  return { valid, invalid }
}

/**
 * Validate search query
 */
export function isValidSearchQuery(query: string): boolean {
  const trimmed = query.trim()
  return trimmed.length > 0 && trimmed.length <= 500
}

/**
 * Sanitize filename
 */
export function sanitizeFilename(filename: string): string {
  // Remove any path components
  const name = filename.split(/[\\/]/).pop() || filename
  
  // Replace unsafe characters
  return name.replace(/[^a-zA-Z0-9._-]/g, '_')
}

/**
 * Check if string is UUID
 */
export function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  return uuidRegex.test(uuid)
}

/**
 * Validate date range
 */
export function isValidDateRange(from?: Date, to?: Date): boolean {
  if (!from || !to) return true
  return from <= to
}

/**
 * Validate URL
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * Check if value is empty (null, undefined, empty string, empty array)
 */
export function isEmpty(value: any): boolean {
  return (
    value === null ||
    value === undefined ||
    value === '' ||
    (Array.isArray(value) && value.length === 0) ||
    (typeof value === 'object' && Object.keys(value).length === 0)
  )
}

/**
 * Validate pagination parameters
 */
export function validatePagination(page?: number, pageSize?: number): {
  page: number
  pageSize: number
} {
  const validPage = page && page > 0 ? page : 1
  const validPageSize = pageSize && pageSize > 0 && pageSize <= 100 ? pageSize : 20
  
  return {
    page: validPage,
    pageSize: validPageSize
  }
}

/**
 * Check if file is an image
 */
export function isImageFile(file: File): boolean {
  return ALLOWED_IMAGE_TYPES.includes(file.type as any)
}

/**
 * Check if file is a video
 */
export function isVideoFile(file: File): boolean {
  return ALLOWED_VIDEO_TYPES.includes(file.type as any)
}

/**
 * Get file validation error message
 */
export function getFileValidationError(file: File): string | null {
  if (!isValidFileType(file)) {
    const ext = file.name.split('.').pop()?.toUpperCase() || 'Unknown'
    return `${ext} files are not supported`
  }
  
  if (!isValidFileSize(file)) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1)
    return `File too large (${sizeMB}MB). Maximum size is 100MB`
  }
  
  return null
}
