// ===================
// © AngelaMos | 2026
// upload.ui.store.ts
// ===================

import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface PendingFile {
  name: string
  size: number
  type: string
}

interface UploadUIState {
  pendingFile: PendingFile | null
  dragActive: boolean
}

interface UploadUIActions {
  setPendingFile: (file: PendingFile | null) => void
  setDragActive: (active: boolean) => void
  clearPendingFile: () => void
}

type UploadUIStore = UploadUIState & UploadUIActions

export const useUploadUIStore = create<UploadUIStore>()(
  devtools(
    persist(
      (set) => ({
        pendingFile: null,
        dragActive: false,

        setPendingFile: (file) =>
          set({ pendingFile: file }, false, 'upload/setPendingFile'),

        setDragActive: (active) =>
          set({ dragActive: active }, false, 'upload/setDragActive'),

        clearPendingFile: () =>
          set({ pendingFile: null }, false, 'upload/clearPendingFile'),
      }),
      {
        name: 'upload-ui-storage',
        partialize: (state) => ({
          pendingFile: state.pendingFile,
        }),
      }
    ),
    { name: 'UploadUIStore' }
  )
)

export const usePendingFile = (): PendingFile | null =>
  useUploadUIStore((s) => s.pendingFile)
export const useDragActive = (): boolean => useUploadUIStore((s) => s.dragActive)
