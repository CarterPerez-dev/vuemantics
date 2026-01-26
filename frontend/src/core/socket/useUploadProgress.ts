// ===================
// © AngelaMos | 2026
// useUploadProgress.ts
// ===================

import { useCallback, useState } from 'react'
import type {
  UploadCompleted,
  UploadFailed,
  UploadProgressUpdate,
} from './socket.types'

interface ProgressState {
  percent: number
  stage: string
  message: string
}

interface UseUploadProgressReturn {
  uploadProgress: Record<string, ProgressState>
  handleProgress: (data: UploadProgressUpdate) => void
  handleCompleted: (
    data: UploadCompleted,
    onComplete?: () => void | Promise<void>
  ) => Promise<void>
  handleFailed: (data: UploadFailed, onFail?: () => void) => void
  setProgress: (uploadId: string, progress: ProgressState) => void
  clearProgress: (uploadId: string) => void
}

export function useUploadProgress(): UseUploadProgressReturn {
  const [uploadProgress, setUploadProgress] = useState<
    Record<string, ProgressState>
  >({})

  const handleProgress = useCallback((data: UploadProgressUpdate) => {
    const { upload_id, progress_percent, stage, message } = data.payload
    setUploadProgress((prev) => ({
      ...prev,
      [upload_id]: {
        percent: progress_percent,
        stage,
        message,
      },
    }))
  }, [])

  const handleCompleted = useCallback(
    async (data: UploadCompleted, onComplete?: () => void | Promise<void>) => {
      setUploadProgress((prev) => ({
        ...prev,
        [data.upload_id]: {
          percent: 100,
          stage: 'completed',
          message: 'Refreshing...',
        },
      }))

      if (onComplete) {
        await onComplete()
      }

      setUploadProgress((prev) => {
        const next = { ...prev }
        delete next[data.upload_id]
        return next
      })
    },
    []
  )

  const handleFailed = useCallback((data: UploadFailed, onFail?: () => void) => {
    setUploadProgress((prev) => {
      const next = { ...prev }
      delete next[data.upload_id]
      return next
    })

    if (onFail) {
      onFail()
    }
  }, [])

  const setProgress = useCallback((uploadId: string, progress: ProgressState) => {
    setUploadProgress((prev) => ({
      ...prev,
      [uploadId]: progress,
    }))
  }, [])

  const clearProgress = useCallback((uploadId: string) => {
    setUploadProgress((prev) => {
      const next = { ...prev }
      delete next[uploadId]
      return next
    })
  }, [])

  return {
    uploadProgress,
    handleProgress,
    handleCompleted,
    handleFailed,
    setProgress,
    clearProgress,
  }
}
