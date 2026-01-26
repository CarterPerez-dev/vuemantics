// ===================
// © AngelaMos | 2026
// useGalleryHandlers.ts
// ===================

import type { UseMutationResult } from '@tanstack/react-query'
import type { SearchResult, UploadResponse } from '@/api/types'

interface GalleryHandlersDeps {
  // Mutations
  deleteMutation: UseMutationResult<void, Error, string, unknown>
  toggleHiddenMutation: UseMutationResult<
    UploadResponse,
    Error,
    { id: string; hidden: boolean },
    unknown
  >
  regenerateDescription: UseMutationResult<UploadResponse, Error, string, unknown>
  searchMutation: UseMutationResult<
    { results: SearchResult[] },
    Error,
    {
      query: string
      limit: number
      similarity_threshold: number
    },
    unknown
  >
  bulkDeleteMutation: UseMutationResult<
    { deleted: number },
    Error,
    string[],
    unknown
  >
  bulkHideMutation: UseMutationResult<
    { updated: number },
    Error,
    { ids: string[]; hidden: boolean },
    unknown
  >

  // State setters
  setSelectedMediaId: (id: string | null) => void
  setProgress: (
    uploadId: string,
    progress: { percent: number; stage: string; message: string }
  ) => void
  setSearchQuery: (query: string) => void
  setSearchResults: (results: SearchResult[] | null) => void
  setSimilarResults: (results: SearchResult[] | null) => void
  setFindSimilarId: (id: string | null) => void
  setSelectedIdsArray: (ids: string[]) => void

  // Store actions
  storeToggleSelectMode: () => void
  toggleSelectedId: (id: string) => void

  // Data
  searchQuery: string
  clientConfig:
    | {
        default_page_size?: number
        search_default_similarity_threshold?: number
      }
    | undefined
  displayItems: UploadResponse[]
  selectedIdsArray: string[]
  selectedIds: Set<string>

  // Functions
  subscribeToUpload: (uploadId: string) => void
}

interface GalleryHandlers {
  // Single Upload Operations
  handleDelete: (id: string) => void
  handleToggleHidden: (id: string, currentlyHidden: boolean) => void
  handleRegenerate: (uploadId: string) => void

  // Search Operations
  handleSearch: (e: React.FormEvent) => void
  handleClearSearch: () => void
  handleFindSimilar: (upload: UploadResponse) => void

  // Selection/Bulk Operations
  toggleSelectMode: () => void
  toggleSelectItem: (id: string) => void
  selectAll: () => void
  deselectAll: () => void
  handleBulkDelete: () => void
  handleBulkHide: (hidden: boolean) => void
}

export function useGalleryHandlers(deps: GalleryHandlersDeps): GalleryHandlers {
  const {
    deleteMutation,
    toggleHiddenMutation,
    regenerateDescription,
    searchMutation,
    bulkDeleteMutation,
    bulkHideMutation,
    setSelectedMediaId,
    setProgress,
    setSearchQuery,
    setSearchResults,
    setSimilarResults,
    setFindSimilarId,
    setSelectedIdsArray,
    storeToggleSelectMode,
    toggleSelectedId,
    searchQuery,
    clientConfig,
    displayItems,
    selectedIdsArray,
    selectedIds,
    subscribeToUpload,
  } = deps

  // Single Upload Operations
  const handleDelete = (id: string): void => {
    if (window.confirm('Delete this upload?')) {
      setSelectedMediaId(null)
      deleteMutation.mutate(id)
    }
  }

  const handleToggleHidden = (id: string, currentlyHidden: boolean): void => {
    setSelectedMediaId(null)
    toggleHiddenMutation.mutate({ id, hidden: !currentlyHidden })
  }

  const handleRegenerate = (uploadId: string): void => {
    setProgress(uploadId, {
      percent: 0,
      stage: 'starting',
      message: 'Starting regeneration...',
    })

    regenerateDescription.mutate(uploadId, {
      onSuccess: () => {
        subscribeToUpload(uploadId)
      },
    })
  }

  // Search Operations
  const handleSearch = (e: React.FormEvent): void => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      setSearchResults(null)
      return
    }

    searchMutation.mutate(
      {
        query: searchQuery,
        limit: clientConfig?.default_page_size ?? 48,
        similarity_threshold:
          clientConfig?.search_default_similarity_threshold ?? 0.48,
      },
      { onSuccess: (data) => setSearchResults(data.results) }
    )
  }

  const handleClearSearch = (): void => {
    setSearchQuery('')
    setSearchResults(null)
    setSimilarResults(null)
    setFindSimilarId(null)
  }

  const handleFindSimilar = (upload: UploadResponse): void => {
    setFindSimilarId(upload.id)
    setSearchQuery('')
    setSearchResults(null)
  }

  // Selection/Bulk Operations
  const toggleSelectMode = (): void => {
    storeToggleSelectMode()
  }

  const toggleSelectItem = (id: string): void => {
    toggleSelectedId(id)
  }

  const selectAll = (): void => {
    setSelectedIdsArray(displayItems.map((item) => item.id))
  }

  const deselectAll = (): void => {
    setSelectedIdsArray([])
  }

  const handleBulkDelete = (): void => {
    if (selectedIds.size === 0) return
    if (
      window.confirm(
        `Delete ${selectedIds.size} upload${selectedIds.size !== 1 ? 's' : ''}?`
      )
    ) {
      bulkDeleteMutation.mutate(selectedIdsArray, {
        onSuccess: () => {
          setSelectedIdsArray([])
          storeToggleSelectMode()
        },
      })
    }
  }

  const handleBulkHide = (hidden: boolean): void => {
    if (selectedIds.size === 0) return
    bulkHideMutation.mutate(
      { ids: selectedIdsArray, hidden },
      {
        onSuccess: () => {
          setSelectedIdsArray([])
          storeToggleSelectMode()
        },
      }
    )
  }

  return {
    handleDelete,
    handleToggleHidden,
    handleRegenerate,
    handleSearch,
    handleClearSearch,
    handleFindSimilar,
    toggleSelectMode,
    toggleSelectItem,
    selectAll,
    deselectAll,
    handleBulkDelete,
    handleBulkHide,
  }
}
