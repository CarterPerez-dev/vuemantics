// ===================
// © AngelaMos | 2026
// socket.client.ts
// ===================

import {
  type BatchProgressUpdate,
  type FileProgressUpdate,
  type ServerMessage,
  serverMessageSchema,
  type UploadCompleted,
  type UploadFailed,
  type UploadProgressUpdate,
  WEBSOCKET_ERROR_MESSAGES,
  WebSocketError,
} from './socket.types'

type ProgressHandler = (data: UploadProgressUpdate) => void
type CompletedHandler = (data: UploadCompleted) => void
type FailedHandler = (data: UploadFailed) => void
type BatchProgressHandler = (data: BatchProgressUpdate) => void
type FileProgressHandler = (data: FileProgressUpdate) => void
type ErrorHandler = (error: WebSocketError) => void

interface WebSocketConfig {
  url: string
  getToken: () => string | null
  onProgress?: ProgressHandler
  onCompleted?: CompletedHandler
  onFailed?: FailedHandler
  onBatchProgress?: BatchProgressHandler
  onFileProgress?: FileProgressHandler
  onError?: ErrorHandler
  onReconnect?: () => void
}

export class VuemanticWebSocket {
  private ws: WebSocket | null = null
  private config: WebSocketConfig
  private attempt = 0
  private maxRetries = 10
  private initialDelay = 1000
  private maxDelay = 30000
  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  private isIntentionallyClosed = false

  constructor(config: WebSocketConfig) {
    this.config = config
    this.connect()
  }

  private connect(): void {
    const token = this.config.getToken()
    if (!token) {
      this.config.onError?.(new WebSocketError(WEBSOCKET_ERROR_MESSAGES.NO_TOKEN))
      return
    }

    this.ws = new WebSocket(this.config.url)

    this.ws.onopen = () => {
      this.attempt = 0

      this.ws?.send(
        JSON.stringify({
          type: 'auth',
          token: token,
        })
      )

      this.startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      try {
        const rawData = JSON.parse(event.data)
        const result = serverMessageSchema.safeParse(rawData)

        if (!result.success) {
          return
        }

        const data: ServerMessage = result.data

        switch (data.action) {
          case 'auth_success':
            this.config.onReconnect?.()
            break

          case 'auth_error':
            this.config.onError?.(new WebSocketError(data.message))
            this.close()
            break

          case 'upload_progress':
            this.config.onProgress?.(data)
            break

          case 'upload_completed':
            this.config.onCompleted?.(data)
            break

          case 'upload_failed':
            this.config.onFailed?.(data)
            break

          case 'batch_progress':
            this.config.onBatchProgress?.(data)
            break

          case 'file_progress':
            this.config.onFileProgress?.(data)
            break

          case 'ping':
            this.ws?.send(JSON.stringify({ action: 'pong' }))
            break
        }
      } catch {
        // Invalid message format, silently ignore
      }
    }

    this.ws.onclose = (event) => {
      this.stopHeartbeat()

      if (this.isIntentionallyClosed) {
        return
      }

      if (event.code === 1000) {
        return
      }

      if (event.code >= 4001 && event.code <= 4004) {
        this.config.onError?.(
          new WebSocketError(WEBSOCKET_ERROR_MESSAGES.AUTH_FAILED, event.code)
        )
        return
      }

      this.scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.config.onError?.(
        new WebSocketError(WEBSOCKET_ERROR_MESSAGES.CONNECTION_FAILED)
      )
    }
  }

  private scheduleReconnect(): void {
    if (this.attempt >= this.maxRetries) {
      this.config.onError?.(
        new WebSocketError(WEBSOCKET_ERROR_MESSAGES.MAX_RETRIES)
      )
      return
    }

    this.attempt++

    const baseDelay = Math.min(
      this.initialDelay * 2 ** (this.attempt - 1),
      this.maxDelay
    )

    const jitter = Math.random() * 3000
    const delay = baseDelay + jitter

    this.reconnectTimer = window.setTimeout(() => {
      this.connect()
    }, delay)
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'ping' }))
      }
    }, 30000)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      window.clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  subscribeToUpload(uploadId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          action: 'subscribe_upload',
          upload_id: uploadId,
        })
      )
    }
  }

  unsubscribeFromUpload(uploadId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          action: 'unsubscribe_upload',
          upload_id: uploadId,
        })
      )
    }
  }

  close(): void {
    this.isIntentionallyClosed = true

    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.stopHeartbeat()

    if (this.ws) {
      this.ws.close(1000, 'Client closing connection')
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
