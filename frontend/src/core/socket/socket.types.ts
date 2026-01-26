// ===================
// © AngelaMos | 2026
// socket.types.ts
// ===================

import { z } from 'zod'

export const processingStatusSchema = z.enum([
  'pending',
  'analyzing',
  'embedding',
  'completed',
  'failed',
])

export const processingStageSchema = z.enum([
  'queued',
  'extracting_frames',
  'vision_analysis',
  'description_audit',
  'embedding_generation',
  'indexing',
  'completed',
  'failed',
])

export const uploadProgressPayloadSchema = z.object({
  upload_id: z.string().uuid(),
  status: processingStatusSchema,
  stage: processingStageSchema,
  progress_percent: z.number().int().min(0).max(100),
  message: z.string(),
  error_message: z.string().nullable(),
  description_audit_score: z.number().int().min(0).max(100).nullable(),
})

export const uploadProgressUpdateSchema = z.object({
  action: z.literal('upload_progress'),
  payload: uploadProgressPayloadSchema,
  timestamp: z.string(),
})

export const uploadCompletedSchema = z.object({
  action: z.literal('upload_completed'),
  upload_id: z.string().uuid(),
  description: z.string(),
  audit_score: z.number().int().min(0).max(100),
  timestamp: z.string(),
})

export const uploadFailedSchema = z.object({
  action: z.literal('upload_failed'),
  upload_id: z.string().uuid(),
  error_message: z.string(),
  timestamp: z.string(),
})

export const authSuccessSchema = z.object({
  action: z.literal('auth_success'),
  user_id: z.string(),
})

export const authErrorSchema = z.object({
  action: z.literal('auth_error'),
  message: z.string(),
})

export const heartbeatSchema = z.object({
  action: z.literal('ping'),
})

export const serverMessageSchema = z.discriminatedUnion('action', [
  uploadProgressUpdateSchema,
  uploadCompletedSchema,
  uploadFailedSchema,
  authSuccessSchema,
  authErrorSchema,
  heartbeatSchema,
])

export const authMessageSchema = z.object({
  type: z.literal('auth'),
  token: z.string(),
})

export const subscribeUploadSchema = z.object({
  action: z.literal('subscribe_upload'),
  upload_id: z.string().uuid(),
})

export const unsubscribeUploadSchema = z.object({
  action: z.literal('unsubscribe_upload'),
  upload_id: z.string().uuid(),
})

export const pongSchema = z.object({
  action: z.literal('pong'),
})

export const clientMessageSchema = z.discriminatedUnion('action', [
  subscribeUploadSchema,
  unsubscribeUploadSchema,
  pongSchema,
])

export type ProcessingStatus = z.infer<typeof processingStatusSchema>
export type ProcessingStage = z.infer<typeof processingStageSchema>
export type UploadProgressPayload = z.infer<typeof uploadProgressPayloadSchema>
export type UploadProgressUpdate = z.infer<typeof uploadProgressUpdateSchema>
export type UploadCompleted = z.infer<typeof uploadCompletedSchema>
export type UploadFailed = z.infer<typeof uploadFailedSchema>
export type AuthSuccess = z.infer<typeof authSuccessSchema>
export type AuthError = z.infer<typeof authErrorSchema>
export type Heartbeat = z.infer<typeof heartbeatSchema>
export type ServerMessage = z.infer<typeof serverMessageSchema>
export type AuthMessage = z.infer<typeof authMessageSchema>
export type SubscribeUpload = z.infer<typeof subscribeUploadSchema>
export type UnsubscribeUpload = z.infer<typeof unsubscribeUploadSchema>
export type Pong = z.infer<typeof pongSchema>
export type ClientMessage = z.infer<typeof clientMessageSchema>

export const isValidServerMessage = (data: unknown): data is ServerMessage => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const result = serverMessageSchema.safeParse(data)
  return result.success
}

export class WebSocketError extends Error {
  readonly code?: number

  constructor(message: string, code?: number) {
    super(message)
    this.name = 'WebSocketError'
    this.code = code
    Object.setPrototypeOf(this, WebSocketError.prototype)
  }
}

export const WEBSOCKET_ERROR_MESSAGES = {
  NO_TOKEN: 'No authentication token available',
  AUTH_FAILED: 'WebSocket authentication failed',
  CONNECTION_FAILED: 'WebSocket connection failed',
  MAX_RETRIES: 'Max reconnection attempts reached',
  NOT_CONNECTED: 'WebSocket is not connected',
} as const

export const WEBSOCKET_SUCCESS_MESSAGES = {
  CONNECTED: 'WebSocket connected',
  AUTHENTICATED: 'WebSocket authenticated',
  SUBSCRIBED: 'Subscribed to upload',
  UNSUBSCRIBED: 'Unsubscribed from upload',
} as const

export type WebSocketErrorMessage =
  (typeof WEBSOCKET_ERROR_MESSAGES)[keyof typeof WEBSOCKET_ERROR_MESSAGES]
export type WebSocketSuccessMessage =
  (typeof WEBSOCKET_SUCCESS_MESSAGES)[keyof typeof WEBSOCKET_SUCCESS_MESSAGES]
