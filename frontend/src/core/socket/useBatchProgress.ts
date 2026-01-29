// ===================
// © AngelaMos | 2026
// useBatchProgress.ts
// ===================

import { useCallback, useState } from 'react'
import type { BatchProgressUpdate } from './socket.types'

interface BatchProgressState {
  status: string
  total: number
  processed: number
  successful: number
  failed: number
  progressPercentage: number
}

interface UseBatchProgressReturn {
  batchProgress: Record<string, BatchProgressState>
  handleBatchProgress: (data: BatchProgressUpdate) => void
  setBatchProgress: (batchId: string, progress: BatchProgressState) => void
  clearBatchProgress: (batchId: string) => void
  clearAllBatchProgress: () => void
}

export function useBatchProgress(): UseBatchProgressReturn {
  const [batchProgress, setBatchProgressState] = useState<
    Record<string, BatchProgressState>
  >({})

  const handleBatchProgress = useCallback((data: BatchProgressUpdate) => {
    const {
      batch_id,
      status,
      total,
      processed,
      successful,
      failed,
      progress_percentage,
    } = data.payload

    setBatchProgressState((prev) => ({
      ...prev,
      [batch_id]: {
        status,
        total,
        processed,
        successful,
        failed,
        progressPercentage: progress_percentage,
      },
    }))

    // Auto-clear completed batches after 5 seconds
    if (status === 'completed' || status === 'failed' || status === 'cancelled') {
      setTimeout(() => {
        setBatchProgressState((prev) => {
          const next = { ...prev }
          delete next[batch_id]
          return next
        })
      }, 5000)
    }
  }, [])

  const setBatchProgress = useCallback(
    (batchId: string, progress: BatchProgressState) => {
      setBatchProgressState((prev) => ({
        ...prev,
        [batchId]: progress,
      }))
    },
    []
  )

  const clearBatchProgress = useCallback((batchId: string) => {
    setBatchProgressState((prev) => {
      const next = { ...prev }
      delete next[batchId]
      return next
    })
  }, [])

  const clearAllBatchProgress = useCallback(() => {
    setBatchProgressState({})
  }, [])

  return {
    batchProgress,
    handleBatchProgress,
    setBatchProgress,
    clearBatchProgress,
    clearAllBatchProgress,
  }
}
