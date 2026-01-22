// ===================
// © AngelaMos | 2026
// search.types.ts
// ===================

import { z } from 'zod'
import { uploadResponseSchema } from './upload.types'

export const searchRequestSchema = z.object({
  query: z.string().min(1).max(500),
  limit: z.number().int().positive().max(100).default(20),
  similarity_threshold: z.number().min(0).max(1).default(0.25),
  file_types: z.array(z.enum(['image', 'video'])).nullable().optional(),
  date_from: z.string().nullable().optional(),
  date_to: z.string().nullable().optional(),
  user_id: z.string().uuid().nullable().optional(),
})

export const searchResultSchema = z.object({
  upload: uploadResponseSchema,
  similarity_score: z.number().min(0).max(1),
  distance: z.number().min(0),
  rank: z.number().int().positive(),
})

export const searchResponseSchema = z.object({
  results: z.array(searchResultSchema),
  total_found: z.number().int().nonnegative(),
  returned_count: z.number().int().nonnegative(),
  search_time_ms: z.number().nonnegative(),
  query: z.string(),
  query_embedding_generated: z.boolean().default(true),
  applied_filters: z.record(z.any()).nullable().optional(),
})

export type SearchRequest = z.infer<typeof searchRequestSchema>
export type SearchResult = z.infer<typeof searchResultSchema>
export type SearchResponse = z.infer<typeof searchResponseSchema>

export const isValidSearchResponse = (data: unknown): data is SearchResponse => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const result = searchResponseSchema.safeParse(data)
  return result.success
}

export class SearchResponseError extends Error {
  readonly endpoint?: string

  constructor(message: string, endpoint?: string) {
    super(message)
    this.name = 'SearchResponseError'
    this.endpoint = endpoint
    Object.setPrototypeOf(this, SearchResponseError.prototype)
  }
}

export const SEARCH_ERROR_MESSAGES = {
  INVALID_SEARCH_RESPONSE: 'Invalid search data from server',
  SEARCH_FAILED: 'Search failed',
  EMPTY_QUERY: 'Search query cannot be empty',
} as const

export const SEARCH_SUCCESS_MESSAGES = {
  SEARCH_COMPLETE: 'Search completed',
} as const

export type SearchErrorMessage =
  (typeof SEARCH_ERROR_MESSAGES)[keyof typeof SEARCH_ERROR_MESSAGES]
export type SearchSuccessMessage =
  (typeof SEARCH_SUCCESS_MESSAGES)[keyof typeof SEARCH_SUCCESS_MESSAGES]
