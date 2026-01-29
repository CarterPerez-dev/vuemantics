// ===================
// © AngelaMos | 2026
// global-batch-progress.store.ts
// ===================

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface BatchProgress {
  status: string
  total: number
  processed: number
  successful: number
  failed: number
  progressPercentage: number
}

interface FileProgressState {
  uploadId: string
  fileName: string
  fileSize: number
  progress: number
  status: 'processing' | 'completed' | 'failed'
}

interface GlobalBatchProgressState {
  batchProgress: Record<string, BatchProgress>
  currentFile: FileProgressState | null
  setBatchProgress: (batchId: string, progress: BatchProgress) => void
  setCurrentFile: (file: FileProgressState | null) => void
  clearBatch: (batchId: string) => void
  hasActiveProcessing: () => boolean
  getActiveCount: () => { processed: number; total: number }
}

export const useGlobalBatchProgress = create<GlobalBatchProgressState>()(
  persist(
    (set, get) => ({
      batchProgress: {},
      currentFile: null,

      setBatchProgress: (batchId, progress) => {
        set((state) => ({
          batchProgress: {
            ...state.batchProgress,
            [batchId]: progress,
          },
        }))

        // Auto-clear completed batches after 5 seconds
        if (progress.status === 'completed' || progress.status === 'failed') {
          setTimeout(() => {
            set((state) => {
              const { [batchId]: _, ...rest } = state.batchProgress
              return { batchProgress: rest }
            })
          }, 5000)
        }
      },

      setCurrentFile: (file) => {
        set({ currentFile: file })
      },

      clearBatch: (batchId) => {
        set((state) => {
          const { [batchId]: _, ...rest } = state.batchProgress
          return { batchProgress: rest }
        })
      },

      hasActiveProcessing: () => {
        const batches = Object.values(get().batchProgress)
        return batches.some((b) => b.status === 'processing')
      },

      getActiveCount: () => {
        const batches = Object.values(get().batchProgress)
        const activeBatch = batches.find((b) => b.status === 'processing')
        return {
          processed: activeBatch?.processed || 0,
          total: activeBatch?.total || 0,
        }
      },
    }),
    {
      name: 'vuemantics-batch-progress',
      partialPersist: (state) => ({
        batchProgress: state.batchProgress,
      }),
    }
  )
)
