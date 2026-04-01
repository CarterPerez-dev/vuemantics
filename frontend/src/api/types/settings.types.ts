// ===================
// © AngelaMos | 2026
// settings.types.ts
// ===================

import { z } from 'zod'

export const providerResponseSchema = z.object({
  provider: z.enum(['local', 'gemini']),
  local_count: z.number().int().nonnegative(),
  gemini_count: z.number().int().nonnegative(),
})

export const reembedResponseSchema = z.object({
  status: z.string(),
  message: z.string(),
})

export type ProviderResponse = z.infer<typeof providerResponseSchema>
export type ReembedResponse = z.infer<typeof reembedResponseSchema>
export type EmbeddingProvider = 'local' | 'gemini'
