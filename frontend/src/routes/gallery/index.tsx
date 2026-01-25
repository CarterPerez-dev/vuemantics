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
  useSearchMutation,
  useSimilarUploads,
  useToggleUploadHidden,
  useUploads,
} from '@/api/hooks'
import type { SearchResult, UploadListParams, UploadResponse } from '@/api/types'
import styles from './gallery.module.scss'

export function Component(): React.ReactElement {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null)
  const [selectedMedia, setSelectedMedia] = useState<UploadResponse | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [selectMode, setSelectMode] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [similarResults, setSimilarResults] = useState<SearchResult[] | null>(
    null
  )
  const [findSimilarId, setFindSimilarId] = useState<string | null>(null)

  const { data: clientConfig } = useClientConfig()

  const [filters, setFilters] = useState<UploadListParams>({
    page: 1,
    page_size: 50, // Matches DEFAULT_PAGE_SIZE from backend
    sort_by: 'created_at',
    sort_order: 'desc',
    show_hidden: false,
  })

  const { data: uploads, isLoading } = useUploads(filters)

  const searchMutation = useSearchMutation()
  const deleteMutation = useDeleteUpload()
  const toggleHiddenMutation = useToggleUploadHidden()
  const bulkDeleteMutation = useBulkDeleteUploads()
  const bulkHideMutation = useBulkHideUploads()

  const { data: similarUploadsData, isLoading: isSimilarLoading } =
    useSimilarUploads(
      findSimilarId ?? '',
      clientConfig?.similar_uploads_default_limit ?? 10,
      true
    )

  const handleDelete = (id: string): void => {
    if (window.confirm('Delete this upload?')) {
      deleteMutation.mutate(id, {
        onSuccess: () => setSelectedMedia(null),
      })
    }
  }

  const handleToggleHidden = (id: string, currentlyHidden: boolean): void => {
    toggleHiddenMutation.mutate(
      { id, hidden: !currentlyHidden },
      { onSuccess: () => setSelectedMedia(null) }
    )
  }

  const handleSearch = (e: React.FormEvent): void => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      setSearchResults(null)
      return
    }

    searchMutation.mutate(
      {
        query: searchQuery,
        limit: clientConfig?.default_page_size ?? 50,
        similarity_threshold:
          clientConfig?.search_default_similarity_threshold ?? 0.25,
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

  useEffect(() => {
    if (similarUploadsData) {
      setSimilarResults(similarUploadsData)
    }
  }, [similarUploadsData])

  const toggleSelectMode = (): void => {
    setSelectMode(!selectMode)
    setSelectedIds(new Set())
  }

  const toggleSelectItem = (id: string): void => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const selectAll = (): void => {
    setSelectedIds(new Set(displayItems.map((item) => item.id)))
  }

  const deselectAll = (): void => {
    setSelectedIds(new Set())
  }

  const handleBulkDelete = (): void => {
    if (selectedIds.size === 0) return
    if (
      window.confirm(
        `Delete ${selectedIds.size} upload${selectedIds.size !== 1 ? 's' : ''}?`
      )
    ) {
      bulkDeleteMutation.mutate(Array.from(selectedIds), {
        onSuccess: () => {
          setSelectedIds(new Set())
          setSelectMode(false)
        },
      })
    }
  }

  const handleBulkHide = (hidden: boolean): void => {
    if (selectedIds.size === 0) return
    bulkHideMutation.mutate(
      { ids: Array.from(selectedIds), hidden },
      {
        onSuccess: () => {
          setSelectedIds(new Set())
          setSelectMode(false)
        },
      }
    )
  }

  const displayItems = similarResults
    ? similarResults.map((r) => r.upload)
    : searchResults
      ? searchResults.map((r) => r.upload)
      : (uploads?.items ?? [])

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
                {isSimilarMode ? (
                  <>
                    Found {similarResults.length} similar image
                    {similarResults.length !== 1 ? 's' : ''}
                  </>
                ) : (
                  <>
                    Found {searchResults.length} result
                    {searchResults.length !== 1 ? 's' : ''} for "{searchQuery}"
                  </>
                )}
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
              onClick={() => setShowFilters(!showFilters)}
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
                  setFilters({
                    ...filters,
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
                  const newSortBy = e.target.value as UploadListParams['sort_by']
                  const defaultOrder = newSortBy === 'filename' ? 'asc' : 'desc'
                  setFilters({
                    ...filters,
                    sort_by: newSortBy,
                    sort_order: defaultOrder,
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
                  setFilters({
                    ...filters,
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
                    setFilters({ ...filters, show_hidden: e.target.checked })
                  }
                />
                Show hidden
              </label>
            </div>
          </div>
        )}

        {isLoading || isSimilarLoading ? (
          <div className={styles.loading}>
            {isSimilarLoading ? 'Finding similar images...' : 'Loading your media...'}
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
                      : setSelectedMedia(upload)
                  }
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      selectMode
                        ? toggleSelectItem(upload.id)
                        : setSelectedMedia(upload)
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
                  onClick={() =>
                    setFilters({ ...filters, page: filters.page - 1 })
                  }
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
                  onClick={() =>
                    setFilters({ ...filters, page: filters.page + 1 })
                  }
                  disabled={filters.page === uploads.pages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {selectedMedia && (
        <div
          className={styles.modal}
          onClick={() => setSelectedMedia(null)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              setSelectedMedia(null)
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
              onClick={() => setSelectedMedia(null)}
              aria-label="Close"
            >
              <LuX />
            </button>

            <div className={styles.mediaWrapper}>
              {selectedMedia.file_type === 'image' ? (
                <img
                  src={selectedMedia.file_path}
                  alt={selectedMedia.filename}
                  className={styles.modalImg}
                />
              ) : (
                <video
                  src={selectedMedia.file_path}
                  className={styles.modalVideo}
                  controls
                />
              )}
            </div>

            <div className={styles.modalInfo}>
              <h3 className={styles.modalTitle}>{selectedMedia.filename}</h3>
              {selectedMedia.description && (
                <>
                  <p className={styles.modalDescription}>
                    {selectedMedia.description}
                  </p>
                  {selectedMedia.description_audit_score !== null && (
                    <div className={styles.confidenceScore}>
                      <span className={styles.confidenceLabel}>Description Quality:</span>
                      <span
                        className={`${styles.confidenceValue} ${
                          selectedMedia.description_audit_score >= 80
                            ? styles.scoreHigh
                            : selectedMedia.description_audit_score >= 60
                              ? styles.scoreMedium
                              : styles.scoreLow
                        }`}
                      >
                        {selectedMedia.description_audit_score}/100
                      </span>
                    </div>
                  )}
                </>
              )}
              <div className={styles.modalMeta}>
                <span>Type: {selectedMedia.file_type}</span>
                <span>Status: {selectedMedia.processing_status}</span>
                {selectedMedia.hidden && (
                  <span className={styles.hiddenTag}>Hidden</span>
                )}
              </div>
              <div className={styles.modalActions}>
                <button
                  type="button"
                  className={styles.actionBtn}
                  onClick={() => {
                    handleFindSimilar(selectedMedia)
                    setSelectedMedia(null)
                  }}
                  disabled={isSimilarLoading || !selectedMedia.has_embedding}
                >
                  <LuSparkles />
                  Find Similar
                </button>
                <button
                  type="button"
                  className={styles.actionBtn}
                  onClick={() =>
                    handleToggleHidden(selectedMedia.id, selectedMedia.hidden)
                  }
                  disabled={toggleHiddenMutation.isPending}
                >
                  {selectedMedia.hidden ? <LuEye /> : <LuEyeOff />}
                  {selectedMedia.hidden ? 'Unhide' : 'Hide'}
                </button>
                <button
                  type="button"
                  className={`${styles.actionBtn} ${styles.danger}`}
                  onClick={() => handleDelete(selectedMedia.id)}
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
