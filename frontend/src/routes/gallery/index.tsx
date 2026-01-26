// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { useEffect, useState } from 'react'
import {
  LuCheck,
  LuEye,
  LuEyeOff,
  LuFilter,
  LuRefreshCw,
  LuSearch,
  LuSparkles,
  LuTrash2,
  LuUpload,
  LuX,
} from 'react-icons/lu'
import {
  useBulkDeleteUploads,
  useBulkHideUploads,
  useClientConfig,
  useDeleteUpload,
  useRegenerateDescription,
  useSearchMutation,
  useSimilarUploads,
  useToggleUploadHidden,
  useUploads,
} from '@/api/hooks'
import type { SearchResult } from '@/api/types'
import { useGalleryUIStore } from '@/core/lib/stores'
import { useSocket, useUploadProgress } from '@/core/socket'
import styles from './gallery.module.scss'
import { useGalleryHandlers } from './useGalleryHandlers'

export function Component(): React.ReactElement {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null)
  const [similarResults, setSimilarResults] = useState<SearchResult[] | null>(
    null
  )

  const {
    selectMode,
    selectedIds: selectedIdsArray,
    showFilters,
    filters,
    selectedMediaId,
    findSimilarId,
    toggleSelectMode: storeToggleSelectMode,
    toggleSelectedId,
    setSelectedIds: setSelectedIdsArray,
    toggleShowFilters,
    updateFilters,
    setSelectedMediaId,
    setFindSimilarId,
  } = useGalleryUIStore()

  const { data: clientConfig } = useClientConfig()
  const {
    data: uploads,
    isLoading,
    refetch: refetchUploads,
  } = useUploads(filters)

  const searchMutation = useSearchMutation()
  const deleteMutation = useDeleteUpload()
  const toggleHiddenMutation = useToggleUploadHidden()
  const bulkDeleteMutation = useBulkDeleteUploads()
  const bulkHideMutation = useBulkHideUploads()
  const regenerateDescription = useRegenerateDescription()

  const {
    uploadProgress,
    handleProgress,
    handleCompleted,
    handleFailed,
    setProgress,
  } = useUploadProgress()

  const { subscribeToUpload } = useSocket({
    enabled: true,
    onProgress: handleProgress,
    onCompleted: async (data) => {
      await handleCompleted(data, async () => {
        await refetchUploads()
      })
    },
    onFailed: (data) => handleFailed(data),
  })

  const { data: similarUploadsData, isLoading: isSimilarLoading } =
    useSimilarUploads(
      findSimilarId ?? '',
      clientConfig?.similar_uploads_default_limit ?? 6,
      true
    )

  useEffect(() => {
    if (similarUploadsData) {
      setSimilarResults(similarUploadsData)
    }
  }, [similarUploadsData])

  const displayItems = similarResults
    ? similarResults.map((r) => r.upload)
    : searchResults
      ? searchResults.map((r) => r.upload)
      : (uploads?.items ?? [])

  const selectedIds = new Set(selectedIdsArray)

  const {
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
  } = useGalleryHandlers({
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
  })

  const currentUpload = selectedMediaId
    ? (displayItems.find((item) => item.id === selectedMediaId) ?? null)
    : null

  const isSearching = searchResults !== null
  const isSimilarMode = similarResults !== null

  const getOrderOptions = () => {
    switch (filters.sort_by) {
      case 'file_size':
        return [
          { value: 'desc', label: 'Largest to Smallest' },
          { value: 'asc', label: 'Smallest to Largest' },
        ]
      case 'filename':
        return [
          { value: 'asc', label: 'A-Z' },
          { value: 'desc', label: 'Z-A' },
        ]
      default:
        return [
          { value: 'desc', label: 'Newest first' },
          { value: 'asc', label: 'Oldest first' },
        ]
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.searchSection}>
          <form className={styles.searchForm} onSubmit={handleSearch}>
            <div className={styles.searchInputWrapper}>
              <LuSearch className={styles.searchIcon} />
              <input
                type="text"
                className={styles.searchInput}
                placeholder="Search your media... (e.g., 'sunset at the beach')"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className={styles.clearBtn}
                  onClick={handleClearSearch}
                  aria-label="Clear search"
                >
                  <LuX />
                </button>
              )}
            </div>
            <button
              type="submit"
              className={styles.searchBtn}
              disabled={!searchQuery.trim() || searchMutation.isPending}
            >
              {searchMutation.isPending ? 'Searching...' : 'Search'}
            </button>
          </form>

          {(isSearching || isSimilarMode) && (
            <div className={styles.searchInfo}>
              <span className={styles.searchInfoText}>
                {isSimilarMode && similarResults ? (
                  <>
                    Found {similarResults.length} similar image
                    {similarResults.length !== 1 ? 's' : ''}
                  </>
                ) : searchResults ? (
                  <>
                    Found {searchResults.length} result
                    {searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
                  </>
                ) : null}
              </span>
              <button
                type="button"
                className={styles.clearSearchBtn}
                onClick={handleClearSearch}
              >
                {isSimilarMode ? 'Clear similar' : 'Clear search'}
              </button>
            </div>
          )}
        </div>

        <div className={styles.toolbar}>
          <div className={styles.toolbarLeft}>
            <button
              type="button"
              className={`${styles.toolbarBtn} ${selectMode ? styles.active : ''}`}
              onClick={toggleSelectMode}
            >
              <LuCheck />
              {selectMode ? 'Cancel' : 'Select'}
            </button>
            <button
              type="button"
              className={`${styles.toolbarBtn} ${showFilters ? styles.active : ''}`}
              onClick={toggleShowFilters}
            >
              <LuFilter />
              Filters
            </button>
          </div>

          {selectMode && selectedIds.size > 0 && (
            <div className={styles.bulkActions}>
              <span className={styles.selectedCount}>
                {selectedIds.size} selected
              </span>
              <button
                type="button"
                className={styles.bulkBtn}
                onClick={() => handleBulkHide(true)}
              >
                <LuEyeOff />
                Hide
              </button>
              <button
                type="button"
                className={styles.bulkBtn}
                onClick={() => handleBulkHide(false)}
              >
                <LuEye />
                Unhide
              </button>
              <button
                type="button"
                className={`${styles.bulkBtn} ${styles.danger}`}
                onClick={handleBulkDelete}
              >
                <LuTrash2 />
                Delete
              </button>
            </div>
          )}

          {selectMode && (
            <div className={styles.toolbarRight}>
              <button
                type="button"
                className={styles.textBtn}
                onClick={selectAll}
              >
                Select all
              </button>
              <button
                type="button"
                className={styles.textBtn}
                onClick={deselectAll}
              >
                Deselect all
              </button>
            </div>
          )}
        </div>

        {showFilters && (
          <div className={styles.filterBar}>
            <div className={styles.filterGroup}>
              <label htmlFor="filter-type" className={styles.filterLabel}>
                Type
              </label>
              <select
                id="filter-type"
                className={styles.filterSelect}
                value={filters.file_type ?? ''}
                onChange={(e) =>
                  updateFilters({
                    file_type: e.target.value
                      ? (e.target.value as 'image' | 'video')
                      : undefined,
                  })
                }
              >
                <option value="">All</option>
                <option value="image">Images</option>
                <option value="video">Videos</option>
              </select>
            </div>

            <div className={styles.filterGroup}>
              <label htmlFor="filter-sort" className={styles.filterLabel}>
                Sort
              </label>
              <select
                id="filter-sort"
                className={styles.filterSelect}
                value={filters.sort_by}
                onChange={(e) => {
                  const newSortBy = e.target.value as
                    | 'created_at'
                    | 'updated_at'
                    | 'file_size'
                    | 'filename'
                  const defaultOrder = newSortBy === 'filename' ? 'asc' : 'desc'
                  updateFilters({
                    sort_by: newSortBy,
                    sort_order: defaultOrder as 'asc' | 'desc',
                  })
                }}
              >
                <option value="created_at">Date uploaded</option>
                <option value="updated_at">Date modified</option>
                <option value="file_size">File size</option>
                <option value="filename">Filename</option>
              </select>
            </div>

            <div className={styles.filterGroup}>
              <label htmlFor="filter-order" className={styles.filterLabel}>
                Order
              </label>
              <select
                id="filter-order"
                className={styles.filterSelect}
                value={filters.sort_order}
                onChange={(e) =>
                  updateFilters({
                    sort_order: e.target.value as 'asc' | 'desc',
                  })
                }
              >
                {getOrderOptions().map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.filterGroup}>
              <label className={styles.filterCheckbox}>
                <input
                  type="checkbox"
                  checked={filters.show_hidden}
                  onChange={(e) =>
                    updateFilters({ show_hidden: e.target.checked })
                  }
                />
                Show hidden
              </label>
            </div>
          </div>
        )}

        {isLoading || isSimilarLoading ? (
          <div className={styles.loading}>
            {isSimilarLoading
              ? 'Finding similar images...'
              : 'Loading your media...'}
          </div>
        ) : displayItems.length === 0 ? (
          <div className={styles.empty}>
            <LuUpload className={styles.emptyIcon} />
            <p className={styles.emptyText}>
              {isSimilarMode
                ? 'No similar images found'
                : isSearching
                  ? 'No results found'
                  : 'No uploads yet'}
            </p>
            <p className={styles.emptySubtext}>
              {isSimilarMode
                ? 'Try a different image'
                : isSearching
                  ? 'Try a different search query'
                  : 'Upload your first image or video to get started'}
            </p>
          </div>
        ) : (
          <>
            <div className={styles.grid}>
              {displayItems.map((upload) => (
                <div
                  key={upload.id}
                  className={`${styles.card} ${selectedIds.has(upload.id) ? styles.selected : ''} ${upload.hidden ? styles.hidden : ''}`}
                  onClick={() =>
                    selectMode
                      ? toggleSelectItem(upload.id)
                      : setSelectedMediaId(upload.id)
                  }
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      selectMode
                        ? toggleSelectItem(upload.id)
                        : setSelectedMediaId(upload.id)
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  {selectMode && (
                    <div className={styles.checkbox}>
                      {selectedIds.has(upload.id) && <LuCheck />}
                    </div>
                  )}
                  {upload.hidden && (
                    <div className={styles.hiddenBadge}>
                      <LuEyeOff />
                    </div>
                  )}
                  {!selectMode && upload.has_embedding && (
                    <button
                      type="button"
                      className={styles.similarBtn}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleFindSimilar(upload)
                      }}
                      aria-label="Find similar images"
                    >
                      <LuSparkles />
                    </button>
                  )}
                  <div className={styles.thumbnail}>
                    {upload.thumbnail_path ? (
                      <img
                        src={upload.thumbnail_path}
                        alt={upload.filename}
                        className={styles.thumbnailImg}
                      />
                    ) : (
                      <div className={styles.thumbnailPlaceholder}>
                        <LuUpload />
                      </div>
                    )}
                  </div>
                  <div className={styles.cardContent}>
                    <span className={styles.cardTitle}>{upload.filename}</span>
                    <div className={styles.cardMeta}>
                      <span className={styles.cardType}>{upload.file_type}</span>
                      <span className={styles.cardStatus}>
                        {upload.processing_status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {!isSearching && !isSimilarMode && uploads && uploads.pages > 1 && (
              <div className={styles.pagination}>
                <button
                  type="button"
                  className={styles.pageBtn}
                  onClick={() => updateFilters({ page: filters.page - 1 })}
                  disabled={filters.page === 1}
                >
                  Previous
                </button>
                <span className={styles.pageInfo}>
                  Page {uploads.page} of {uploads.pages} ({uploads.total} total)
                </span>
                <button
                  type="button"
                  className={styles.pageBtn}
                  onClick={() => updateFilters({ page: filters.page + 1 })}
                  disabled={filters.page === uploads.pages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {selectedMediaId && currentUpload && (
        <div
          className={styles.modal}
          onClick={() => setSelectedMediaId(null)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              setSelectedMediaId(null)
            }
          }}
          role="dialog"
          aria-modal="true"
        >
          <div
            className={styles.modalContent}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.stopPropagation()}
            role="document"
          >
            <button
              type="button"
              className={styles.modalClose}
              onClick={() => setSelectedMediaId(null)}
              aria-label="Close"
            >
              <LuX />
            </button>

            <div className={styles.mediaWrapper}>
              {currentUpload.file_type === 'image' ? (
                <img
                  src={currentUpload.file_path}
                  alt={currentUpload.filename}
                  className={styles.modalImg}
                />
              ) : (
                <video
                  src={currentUpload.file_path}
                  className={styles.modalVideo}
                  controls
                />
              )}
            </div>

            <div className={styles.modalInfo}>
              <h3 className={styles.modalTitle}>{currentUpload.filename}</h3>
              {uploadProgress[currentUpload.id] ? (
                <div className={styles.regenerating}>
                  <div className={styles.regeneratingProgress}>
                    <div className={styles.progressBar}>
                      <div
                        className={styles.progressFill}
                        style={{
                          width: `${uploadProgress[currentUpload.id].percent}%`,
                        }}
                      />
                    </div>
                    <div className={styles.regeneratingText}>
                      <span className={styles.regeneratingPercent}>
                        {uploadProgress[currentUpload.id].percent}%
                      </span>
                      <span className={styles.regeneratingMessage}>
                        {uploadProgress[currentUpload.id].message}
                      </span>
                    </div>
                  </div>
                </div>
              ) : currentUpload.description ? (
                <>
                  <p className={styles.modalDescription}>
                    {currentUpload.description}
                  </p>
                  {currentUpload.description_audit_score !== null && (
                    <div className={styles.confidenceScore}>
                      <span className={styles.confidenceLabel}>
                        Description Quality:
                      </span>
                      <span
                        className={`${styles.confidenceValue} ${
                          currentUpload.description_audit_score >= 80
                            ? styles.scoreHigh
                            : currentUpload.description_audit_score >= 60
                              ? styles.scoreMedium
                              : styles.scoreLow
                        }`}
                      >
                        {currentUpload.description_audit_score}/100
                      </span>
                    </div>
                  )}
                </>
              ) : null}
              <div className={styles.modalMeta}>
                <span>Type: {currentUpload.file_type}</span>
                <span>Status: {currentUpload.processing_status}</span>
                {currentUpload.hidden && (
                  <span className={styles.hiddenTag}>Hidden</span>
                )}
              </div>
              <div className={styles.modalActions}>
                <button
                  type="button"
                  className={styles.actionBtn}
                  onClick={() => {
                    handleFindSimilar(currentUpload)
                    setSelectedMediaId(null)
                  }}
                  disabled={isSimilarLoading || !currentUpload.has_embedding}
                >
                  <LuSparkles />
                  Find Similar
                </button>
                {currentUpload.processing_status === 'completed' && (
                  <button
                    type="button"
                    className={styles.actionBtn}
                    onClick={() => handleRegenerate(currentUpload.id)}
                    disabled={regenerateDescription.isPending}
                  >
                    <LuRefreshCw />
                    {regenerateDescription.isPending
                      ? 'Regenerating...'
                      : 'Regenerate'}
                  </button>
                )}
                <button
                  type="button"
                  className={styles.actionBtn}
                  onClick={() =>
                    handleToggleHidden(currentUpload.id, currentUpload.hidden)
                  }
                  disabled={toggleHiddenMutation.isPending}
                >
                  {currentUpload.hidden ? <LuEye /> : <LuEyeOff />}
                  {currentUpload.hidden ? 'Unhide' : 'Hide'}
                </button>
                <button
                  type="button"
                  className={`${styles.actionBtn} ${styles.danger}`}
                  onClick={() => handleDelete(currentUpload.id)}
                  disabled={deleteMutation.isPending}
                >
                  <LuTrash2 />
                  {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

Component.displayName = 'Gallery'
