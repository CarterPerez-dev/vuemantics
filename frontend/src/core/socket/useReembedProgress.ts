// ===================
// © AngelaMos | 2026
// useReembedProgress.ts
// ===================

import { useCallback, useState } from 'react'
import type { ReembedComplete, ReembedProgress } from './socket.types'

export interface ReembedState {
  active: boolean
  processed: number
  total: number
  skipped: number
  failed: number
  complete: boolean
}

const INITIAL_STATE: ReembedState = {
  active: false,
  processed: 0,
  total: 0,
  skipped: 0,
  failed: 0,
  complete: false,
}

export interface UseReembedProgressReturn {
  reembedState: ReembedState
  handleReembedProgress: (data: ReembedProgress) => void
  handleReembedComplete: (data: ReembedComplete) => void
  resetReembed: () => void
}

export function useReembedProgress(): UseReembedProgressReturn {
  const [reembedState, setReembedState] = useState<ReembedState>(INITIAL_STATE)

  const handleReembedProgress = useCallback((data: ReembedProgress) => {
    setReembedState({
      active: true,
      processed: data.processed,
      total: data.total,
      skipped: data.skipped,
      failed: data.failed,
      complete: false,
    })
  }, [])

  const handleReembedComplete = useCallback((data: ReembedComplete) => {
    setReembedState((prev) => ({
      ...prev,
      active: false,
      complete: true,
      processed: data.processed,
      skipped: data.skipped,
      failed: data.failed,
    }))
  }, [])

  const resetReembed = useCallback(() => {
    setReembedState(INITIAL_STATE)
  }, [])

  return {
    reembedState,
    handleReembedProgress,
    handleReembedComplete,
    resetReembed,
  }
}
