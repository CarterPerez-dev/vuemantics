// ===================
// © AngelaMos | 2026
// useFileProgress.ts
// ===================

import { useCallback, useState } from 'react'
import type { FileProgressUpdate } from './socket.types'

interface FileProgressState {
  uploadId: string
  fileName: string
  fileSize: number
  progress: number
  status: 'processing' | 'completed' | 'failed'
}

interface UseFileProgressReturn {
  fileProgress: Record<string, FileProgressState>
  currentFile: FileProgressState | null
  handleFileProgress: (data: FileProgressUpdate) => void
  clearFileProgress: () => void
}

export function useFileProgress(): UseFileProgressReturn {
  const [fileProgress, setFileProgress] = useState<
    Record<string, FileProgressState>
  >({})
  const [currentFile, setCurrentFile] = useState<FileProgressState | null>(null)

  const handleFileProgress = useCallback((data: FileProgressUpdate) => {
    const { payload } = data
    const fileState: FileProgressState = {
      uploadId: payload.upload_id,
      fileName: payload.file_name,
      fileSize: payload.file_size,
      progress: payload.progress_percentage,
      status: payload.status,
    }

    // Update file progress map
    setFileProgress((prev) => ({
      ...prev,
      [payload.upload_id]: fileState,
    }))

    // Update current file if processing
    if (payload.status === 'processing') {
      setCurrentFile(fileState)
    } else if (payload.status === 'completed' || payload.status === 'failed') {
      // Clear current file after completion
      setCurrentFile(null)

      // Auto-clear completed/failed files after 5 seconds
      setTimeout(() => {
        setFileProgress((prev) => {
          const { [payload.upload_id]: _, ...rest } = prev
          return rest
        })
      }, 5000)
    }
  }, [])

  const clearFileProgress = useCallback(() => {
    setFileProgress({})
    setCurrentFile(null)
  }, [])

  return {
    fileProgress,
    currentFile,
    handleFileProgress,
    clearFileProgress,
  }
}
