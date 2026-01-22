// ===================
// © AngelaMos | 2026
// upload.types.ts
// ===================

import { z } from 'zod'

export const uploadResponseSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  filename: z.string(),
  file_path: z.string(),
  file_type: z.enum(['image', 'video']),
  file_size: z.number().int().positive(),
  mime_type: z.string(),
  processing_status: z.enum(['pending', 'analyzing', 'embedding', 'completed', 'failed']),
  gemini_summary: z.string().nullable(),
  embedding_local: z.array(z.number()).nullable(),
  has_embedding: z.boolean(),
  thumbnail_path: z.string().nullable(),
  error_message: z.string().nullable(),
  metadata: z.record(z.any()).nullable(),
  created_at: z.string(),
  updated_at: z.string().nullable(),
})

export const uploadListParamsSchema = z.object({
  page: z.number().int().positive().default(1),
  page_size: z.number().int().positive().max(100).default(20),
  file_type: z.enum(['image', 'video']).optional(),
  processing_status: z.enum(['pending', 'analyzing', 'embedding', 'completed', 'failed']).optional(),
  sort_by: z.enum(['created_at', 'updated_at', 'file_size', 'filename']).default('created_at'),
  sort_order: z.enum(['asc', 'desc']).default('desc'),
})

export const paginatedUploadResponseSchema = z.object({
  items: z.array(uploadResponseSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive(),
  pages: z.number().int().nonnegative(),
})

export type UploadResponse = z.infer<typeof uploadResponseSchema>
export type UploadListParams = z.infer<typeof uploadListParamsSchema>
export type PaginatedUploadResponse = z.infer<typeof paginatedUploadResponseSchema>

export const isValidUploadResponse = (data: unknown): data is UploadResponse => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  try {
    const result = uploadResponseSchema.safeParse(data)
    if (!result.success) {
      console.error('Single upload validation failed:', result.error)
    }
    return result.success
  } catch (err) {
    console.error('Zod exception on single upload:', err)
    return true
  }
}

export const isValidPaginatedUploadResponse = (
  data: unknown
): data is PaginatedUploadResponse => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  try {
    const result = paginatedUploadResponseSchema.safeParse(data)
    if (!result.success) {
      console.error('Upload list validation failed:', result.error)
    }
    return result.success
  } catch (err) {
    console.error('Zod exception on upload list:', err)
    return true
  }
}

export class UploadResponseError extends Error {
  readonly endpoint?: string

  constructor(message: string, endpoint?: string) {
    super(message)
    this.name = 'UploadResponseError'
    this.endpoint = endpoint
    Object.setPrototypeOf(this, UploadResponseError.prototype)
  }
}

export const UPLOAD_ERROR_MESSAGES = {
  INVALID_UPLOAD_RESPONSE: 'Invalid upload data from server',
  INVALID_UPLOAD_LIST_RESPONSE: 'Invalid upload list data from server',
  FILE_TOO_LARGE: 'File is too large',
  UNSUPPORTED_FILE_TYPE: 'File type is not supported',
  UPLOAD_FAILED: 'Upload failed',
  DELETE_FAILED: 'Failed to delete upload',
  NOT_FOUND: 'Upload not found',
} as const

export const UPLOAD_SUCCESS_MESSAGES = {
  UPLOAD_COMPLETE: 'File uploaded successfully!',
  DELETE_COMPLETE: 'Upload deleted successfully',
  PROCESSING: 'Processing your file...',
} as const

export type UploadErrorMessage =
  (typeof UPLOAD_ERROR_MESSAGES)[keyof typeof UPLOAD_ERROR_MESSAGES]
export type UploadSuccessMessage =
  (typeof UPLOAD_SUCCESS_MESSAGES)[keyof typeof UPLOAD_SUCCESS_MESSAGES]
