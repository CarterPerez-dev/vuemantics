// ===================
// © AngelaMos | 2026
// bulk-upload.ui.store.ts
// ===================

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface QueuedFile {
  id: string // Unique ID for tracking
  file: File
  status: 'valid' | 'too-large' | 'unsupported' | 'duplicate'
  preview?: string // Object URL for image preview
  error?: string
}

interface BulkUploadUIState {
  fileQueue: QueuedFile[]
  dragActive: boolean
  currentBatchId: string | null
}

interface BulkUploadUIActions {
  addFiles: (files: QueuedFile[]) => void
  removeFile: (id: string) => void
  clearQueue: () => void
  setDragActive: (active: boolean) => void
  setCurrentBatchId: (batchId: string | null) => void
  updateFileStatus: (
    id: string,
    status: QueuedFile['status'],
    error?: string
  ) => void
}

type BulkUploadUIStore = BulkUploadUIState & BulkUploadUIActions

export const useBulkUploadUIStore = create<BulkUploadUIStore>()(
  devtools(
    (set) => ({
      fileQueue: [],
      dragActive: false,
      currentBatchId: null,

      addFiles: (files) =>
        set(
          (state) => ({
            fileQueue: [...state.fileQueue, ...files],
          }),
          false,
          'bulk-upload/addFiles'
        ),

      removeFile: (id) =>
        set(
          (state) => ({
            fileQueue: state.fileQueue.filter((f) => f.id !== id),
          }),
          false,
          'bulk-upload/removeFile'
        ),

      clearQueue: () =>
        set(
          { fileQueue: [], currentBatchId: null },
          false,
          'bulk-upload/clearQueue'
        ),

      setDragActive: (active) =>
        set({ dragActive: active }, false, 'bulk-upload/setDragActive'),

      setCurrentBatchId: (batchId) =>
        set({ currentBatchId: batchId }, false, 'bulk-upload/setCurrentBatchId'),

      updateFileStatus: (id, status, error) =>
        set(
          (state) => ({
            fileQueue: state.fileQueue.map((f) =>
              f.id === id ? { ...f, status, error } : f
            ),
          }),
          false,
          'bulk-upload/updateFileStatus'
        ),
    }),
    { name: 'BulkUploadUIStore' }
  )
)

export const useFileQueue = (): QueuedFile[] =>
  useBulkUploadUIStore((s) => s.fileQueue)
export const useBulkDragActive = (): boolean =>
  useBulkUploadUIStore((s) => s.dragActive)
export const useCurrentBatchId = (): string | null =>
  useBulkUploadUIStore((s) => s.currentBatchId)
