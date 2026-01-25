// ===================
// © AngelaMos | 2026
// client-config.types.ts
// ===================

import { z } from 'zod'

export const clientConfigResponseSchema = z.object({
  search_default_similarity_threshold: z.number().min(0).max(1),
  similar_uploads_similarity_threshold: z.number().min(0).max(1),
  similar_uploads_default_limit: z.number().int().positive(),
  max_query_length: z.number().int().positive(),
  default_page_size: z.number().int().positive(),
  max_page_size: z.number().int().positive(),
  max_upload_size_mb: z.number().int().positive(),
})

export type ClientConfigResponse = z.infer<typeof clientConfigResponseSchema>

export const isValidClientConfigResponse = (
  data: unknown
): data is ClientConfigResponse => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const result = clientConfigResponseSchema.safeParse(data)
  if (!result.success) {
    // biome-ignore lint/suspicious/noConsole: Debugging validation errors
    console.error('Client config validation failed:', result.error.format())
  }
  return result.success
}

export class ClientConfigError extends Error {
  readonly endpoint?: string

  constructor(message: string, endpoint?: string) {
    super(message)
    this.name = 'ClientConfigError'
    this.endpoint = endpoint
    Object.setPrototypeOf(this, ClientConfigError.prototype)
  }
}

export const CLIENT_CONFIG_ERROR_MESSAGES = {
  INVALID_RESPONSE: 'Invalid client config from server',
  FETCH_FAILED: 'Failed to fetch client configuration',
} as const

export type ClientConfigErrorMessage =
  (typeof CLIENT_CONFIG_ERROR_MESSAGES)[keyof typeof CLIENT_CONFIG_ERROR_MESSAGES]
