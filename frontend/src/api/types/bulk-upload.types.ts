// ===================
// © AngelaMos | 2026
// bulk-upload.types.ts
// ===================

import { z } from 'zod'

export const bulkUploadResultSchema = z.object({
  batch_id: z.string().uuid(),
  total_files: z.number().int().nonnegative(),
  queued: z.number().int().nonnegative(),
  failed: z.number().int().nonnegative(),
  upload_ids: z.array(z.string().uuid()),
  failed_files: z.array(
    z.object({
      filename: z.string(),
      error: z.string(),
    })
  ),
})

export const batchStatusResultSchema = z.object({
  batch_id: z.string().uuid(),
  status: z.enum(['pending', 'processing', 'completed', 'failed', 'cancelled']),
  total_uploads: z.number().int().nonnegative(),
  processed_uploads: z.number().int().nonnegative(),
  successful_uploads: z.number().int().nonnegative(),
  failed_uploads: z.number().int().nonnegative(),
  progress_percentage: z.number().min(0).max(100),
  created_at: z.string().nullable(),
  started_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  error_message: z.string().nullable(),
})

export const batchListResponseSchema = z.array(batchStatusResultSchema)

export type BulkUploadResult = z.infer<typeof bulkUploadResultSchema>
export type BatchStatusResult = z.infer<typeof batchStatusResultSchema>
export type BatchListResponse = z.infer<typeof batchListResponseSchema>

export const isValidBulkUploadResult = (
  data: unknown
): data is BulkUploadResult => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  try {
    const result = bulkUploadResultSchema.safeParse(data)
    return result.success
  } catch {
    return false
  }
}

export const isValidBatchStatusResult = (
  data: unknown
): data is BatchStatusResult => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  try {
    const result = batchStatusResultSchema.safeParse(data)
    return result.success
  } catch {
    return false
  }
}

export const isValidBatchListResponse = (
  data: unknown
): data is BatchListResponse => {
  if (data === null || data === undefined) return false
  if (!Array.isArray(data)) return false

  try {
    const result = batchListResponseSchema.safeParse(data)
    return result.success
  } catch {
    return false
  }
}

export class BulkUploadError extends Error {
  readonly endpoint?: string

  constructor(message: string, endpoint?: string) {
    super(message)
    this.name = 'BulkUploadError'
    this.endpoint = endpoint
    Object.setPrototypeOf(this, BulkUploadError.prototype)
  }
}

export const BULK_UPLOAD_ERROR_MESSAGES = {
  NO_FILES: 'No files selected',
  TOO_MANY_FILES: 'Too many files selected',
  FILES_TOO_LARGE: 'Total file size exceeds limit',
  UPLOAD_FAILED: 'Bulk upload failed',
  BATCH_NOT_FOUND: 'Batch not found',
  INVALID_BULK_UPLOAD_RESPONSE: 'Invalid bulk upload response from server',
  INVALID_BATCH_STATUS_RESPONSE: 'Invalid batch status response from server',
  INVALID_BATCH_LIST_RESPONSE: 'Invalid batch list response from server',
} as const

export const BULK_UPLOAD_SUCCESS_MESSAGES = {
  UPLOAD_STARTED: 'Batch upload started',
  UPLOAD_QUEUED: 'Files queued for processing',
  BATCH_COMPLETE: 'Batch processing complete',
} as const

export type BulkUploadErrorMessage =
  (typeof BULK_UPLOAD_ERROR_MESSAGES)[keyof typeof BULK_UPLOAD_ERROR_MESSAGES]
export type BulkUploadSuccessMessage =
  (typeof BULK_UPLOAD_SUCCESS_MESSAGES)[keyof typeof BULK_UPLOAD_SUCCESS_MESSAGES]
