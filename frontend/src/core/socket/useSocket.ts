// ===================
// © AngelaMos | 2026
// useSocket.ts
// ===================

import { useCallback, useEffect, useRef, useState } from 'react'
import { WEBSOCKET_ENDPOINTS } from '@/config'
import { useAccessToken } from '@/core/lib/stores'
import { VuemanticWebSocket } from './socket.client'
import type {
  BatchProgressUpdate,
  FileProgressUpdate,
  UploadCompleted,
  UploadFailed,
  UploadProgressUpdate,
  WebSocketError,
} from './socket.types'

interface UseSocketOptions {
  enabled?: boolean
  onProgress?: (data: UploadProgressUpdate) => void
  onCompleted?: (data: UploadCompleted) => void
  onFailed?: (data: UploadFailed) => void
  onBatchProgress?: (data: BatchProgressUpdate) => void
  onFileProgress?: (data: FileProgressUpdate) => void
  onError?: (error: WebSocketError) => void
}

interface UseSocketReturn {
  isConnected: boolean
  subscribeToUpload: (uploadId: string) => void
  unsubscribeFromUpload: (uploadId: string) => void
}

export function useSocket(options: UseSocketOptions = {}): UseSocketReturn {
  const {
    enabled = true,
    onProgress,
    onCompleted,
    onFailed,
    onBatchProgress,
    onFileProgress,
    onError,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<VuemanticWebSocket | null>(null)
  const accessToken = useAccessToken()

  const accessTokenRef = useRef(accessToken)
  const onProgressRef = useRef(onProgress)
  const onCompletedRef = useRef(onCompleted)
  const onFailedRef = useRef(onFailed)
  const onBatchProgressRef = useRef(onBatchProgress)
  const onFileProgressRef = useRef(onFileProgress)
  const onErrorRef = useRef(onError)

  useEffect(() => {
    accessTokenRef.current = accessToken
    onProgressRef.current = onProgress
    onCompletedRef.current = onCompleted
    onFailedRef.current = onFailed
    onBatchProgressRef.current = onBatchProgress
    onFileProgressRef.current = onFileProgress
    onErrorRef.current = onError
  })

  const getToken = useCallback((): string | null => {
    return accessTokenRef.current
  }, [])

  const subscribeToUpload = useCallback((uploadId: string) => {
    wsRef.current?.subscribeToUpload(uploadId)
  }, [])

  const unsubscribeFromUpload = useCallback((uploadId: string) => {
    wsRef.current?.unsubscribeFromUpload(uploadId)
  }, [])

  useEffect(() => {
    if (!enabled) {
      return
    }

    if (!accessToken) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}${WEBSOCKET_ENDPOINTS.UPLOADS}`

    try {
      wsRef.current = new VuemanticWebSocket({
        url: wsUrl,
        getToken,
        onProgress: (data) => onProgressRef.current?.(data),
        onCompleted: (data) => onCompletedRef.current?.(data),
        onFailed: (data) => onFailedRef.current?.(data),
        onBatchProgress: (data) => onBatchProgressRef.current?.(data),
        onFileProgress: (data) => onFileProgressRef.current?.(data),
        onError: (error) => {
          onErrorRef.current?.(error)
        },
        onReconnect: () => setIsConnected(true),
      })
    } catch {
      return
    }

    const checkConnection = setInterval(() => {
      const connected = wsRef.current?.isConnected() ?? false
      setIsConnected(connected)
    }, 1000)

    return () => {
      clearInterval(checkConnection)
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      setIsConnected(false)
    }
  }, [enabled, accessToken, getToken])

  return {
    isConnected,
    subscribeToUpload,
    unsubscribeFromUpload,
  }
}
