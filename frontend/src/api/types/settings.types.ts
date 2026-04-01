// ===================
// © AngelaMos | 2026
// settings.types.ts
// ===================

import { z } from 'zod'

export const geminiCostEstimateSchema = z.object({
  cost_per_image: z.number().nonnegative(),
  cost_per_video_frame: z.number().nonnegative(),
  max_frames_per_video: z.number().int().positive(),
  max_cost_per_video: z.number().nonnegative(),
  gemini_image_count: z.number().int().nonnegative(),
  gemini_video_count: z.number().int().nonnegative(),
  estimated_image_cost: z.number().nonnegative(),
  estimated_video_cost: z.number().nonnegative(),
  estimated_total_cost: z.number().nonnegative(),
})

export const providerResponseSchema = z.object({
  provider: z.enum(['local', 'gemini']),
  local_count: z.number().int().nonnegative(),
  gemini_count: z.number().int().nonnegative(),
  cost_estimate: geminiCostEstimateSchema.nullable().optional(),
})

export const reembedResponseSchema = z.object({
  status: z.string(),
  message: z.string(),
})

export type GeminiCostEstimate = z.infer<typeof geminiCostEstimateSchema>
export type ProviderResponse = z.infer<typeof providerResponseSchema>
export type ReembedResponse = z.infer<typeof reembedResponseSchema>
export type EmbeddingProvider = 'local' | 'gemini'
