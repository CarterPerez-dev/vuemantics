// ===================
// © AngelaMos | 2026
// gallery.ui.store.ts
// ===================

import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { UploadListParams } from '@/api/types'

interface GalleryUIState {
  selectMode: boolean
  selectedIds: string[]
  showFilters: boolean
  filters: UploadListParams
  selectedMediaId: string | null
  findSimilarId: string | null
  zoom: number
}

interface GalleryUIActions {
  setSelectMode: (mode: boolean) => void
  toggleSelectMode: () => void
  setSelectedIds: (ids: string[]) => void
  addSelectedId: (id: string) => void
  removeSelectedId: (id: string) => void
  toggleSelectedId: (id: string) => void
  clearSelectedIds: () => void
  setShowFilters: (show: boolean) => void
  toggleShowFilters: () => void
  setFilters: (filters: UploadListParams) => void
  updateFilters: (partial: Partial<UploadListParams>) => void
  setSelectedMediaId: (id: string | null) => void
  setFindSimilarId: (id: string | null) => void
  resetSearchState: () => void
  setZoom: (zoom: number) => void
}

type GalleryUIStore = GalleryUIState & GalleryUIActions

const DEFAULT_FILTERS: UploadListParams = {
  page: 1,
  page_size: 10000,
  sort_by: 'created_at',
  sort_order: 'desc',
  show_hidden: false,
}

const DEFAULT_ZOOM = 200

export const useGalleryUIStore = create<GalleryUIStore>()(
  devtools(
    persist(
      (set) => ({
        selectMode: false,
        selectedIds: [],
        showFilters: false,
        filters: DEFAULT_FILTERS,
        selectedMediaId: null,
        findSimilarId: null,
        zoom: DEFAULT_ZOOM,

        setSelectMode: (mode) =>
          set({ selectMode: mode }, false, 'gallery/setSelectMode'),

        toggleSelectMode: () =>
          set(
            (state) => ({
              selectMode: !state.selectMode,
              selectedIds: !state.selectMode ? [] : state.selectedIds,
            }),
            false,
            'gallery/toggleSelectMode'
          ),

        setSelectedIds: (ids) =>
          set({ selectedIds: ids }, false, 'gallery/setSelectedIds'),

        addSelectedId: (id) =>
          set(
            (state) => ({
              selectedIds: state.selectedIds.includes(id)
                ? state.selectedIds
                : [...state.selectedIds, id],
            }),
            false,
            'gallery/addSelectedId'
          ),

        removeSelectedId: (id) =>
          set(
            (state) => ({
              selectedIds: state.selectedIds.filter(
                (selectedId) => selectedId !== id
              ),
            }),
            false,
            'gallery/removeSelectedId'
          ),

        toggleSelectedId: (id) =>
          set(
            (state) => ({
              selectedIds: state.selectedIds.includes(id)
                ? state.selectedIds.filter((selectedId) => selectedId !== id)
                : [...state.selectedIds, id],
            }),
            false,
            'gallery/toggleSelectedId'
          ),

        clearSelectedIds: () =>
          set({ selectedIds: [] }, false, 'gallery/clearSelectedIds'),

        setShowFilters: (show) =>
          set({ showFilters: show }, false, 'gallery/setShowFilters'),

        toggleShowFilters: () =>
          set(
            (state) => ({ showFilters: !state.showFilters }),
            false,
            'gallery/toggleShowFilters'
          ),

        setFilters: (filters) => set({ filters }, false, 'gallery/setFilters'),

        updateFilters: (partial) =>
          set(
            (state) => ({ filters: { ...state.filters, ...partial } }),
            false,
            'gallery/updateFilters'
          ),

        setSelectedMediaId: (id) =>
          set({ selectedMediaId: id }, false, 'gallery/setSelectedMediaId'),

        setFindSimilarId: (id) =>
          set({ findSimilarId: id }, false, 'gallery/setFindSimilarId'),

        resetSearchState: () =>
          set({ findSimilarId: null }, false, 'gallery/resetSearchState'),

        setZoom: (zoom) =>
          set({ zoom }, false, 'gallery/setZoom'),
      }),
      {
        name: 'gallery-ui-storage',
      }
    ),
    { name: 'GalleryUIStore' }
  )
)

export const useSelectMode = (): boolean => useGalleryUIStore((s) => s.selectMode)
export const useSelectedIds = (): string[] =>
  useGalleryUIStore((s) => s.selectedIds)
export const useShowFilters = (): boolean =>
  useGalleryUIStore((s) => s.showFilters)
export const useGalleryFilters = (): UploadListParams =>
  useGalleryUIStore((s) => s.filters)
export const useSelectedMediaId = (): string | null =>
  useGalleryUIStore((s) => s.selectedMediaId)
export const useFindSimilarId = (): string | null =>
  useGalleryUIStore((s) => s.findSimilarId)
export const useZoom = (): number => useGalleryUIStore((s) => s.zoom)
