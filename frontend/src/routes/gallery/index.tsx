// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { useEffect, useRef, useState } from 'react'
import {
  LuCheck,
  LuDownload,
  LuEye,
  LuEyeOff,
  LuRefreshCw,
  LuSearch,
  LuSparkles,
  LuTrash2,
  LuUpload,
  LuX,
} from 'react-icons/lu'
import { TfiFaceSad } from 'react-icons/tfi'
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
import { useGalleryUIStore, useGlobalBatchProgress } from '@/core/lib/stores'
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
    zoom,
    toggleSelectMode: storeToggleSelectMode,
    toggleSelectedId,
    setSelectedIds: setSelectedIdsArray,
    toggleShowFilters,
    updateFilters,
    setSelectedMediaId,
    setFindSimilarId,
    setZoom,
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

  const { batchProgress } = useGlobalBatchProgress()
  const seenCompletedBatches = useRef<Set<string>>(new Set())

  useEffect(() => {
    const batches = Object.entries(batchProgress)
    let shouldRefetch = false

    batches.forEach(([batchId, batch]) => {
      if (
        batch.status === 'completed' &&
        !seenCompletedBatches.current.has(batchId)
      ) {
        seenCompletedBatches.current.add(batchId)
        shouldRefetch = true
      }
    })

    if (shouldRefetch) {
      refetchUploads()
    }
  }, [batchProgress, refetchUploads])

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
    handleDownload,
    toggleSelectMode,
    toggleSelectItem,
    selectAll,
    deselectAll,
    handleBulkDelete,
    handleBulkHide,
    handleBulkDownload,
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
          { value: 'desc', label: 'Largest' },
          { value: 'asc', label: 'Smallest' },
        ]
      case 'filename':
        return [
          { value: 'asc', label: 'A-Z' },
          { value: 'desc', label: 'Z-A' },
        ]
      default:
        return [
          { value: 'desc', label: 'Newest' },
          { value: 'asc', label: 'Oldest' },
        ]
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div className={styles.pageHeaderLeft}>
          <span className={styles.pageLabel}>MEDIA GALLERY</span>
          <span className={styles.pageMeta}>GAL—01</span>
        </div>
        <div className={styles.pageHeaderRight}>
          {uploads && (
            <span className={styles.pageMeta}>
              {uploads.total} ITEM{uploads.total !== 1 ? 'S' : ''}
            </span>
          )}
        </div>
      </div>

      <div className={styles.controls}>
        <form className={styles.searchForm} onSubmit={handleSearch}>
          <div className={styles.searchWrap}>
            <LuSearch className={styles.searchIcon} />
            <input
              type="text"
              className={styles.searchInput}
              placeholder="a cat sitting on a red couch..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                className={styles.clearBtn}
                onClick={handleClearSearch}
                aria-label="Clear"
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
            {searchMutation.isPending ? 'SEARCHING...' : 'SEARCH'}
          </button>
        </form>

        <div className={styles.toolbar}>
          <div className={styles.toolbarLeft}>
            <button
              type="button"
              className={`${styles.toolBtn} ${selectMode ? styles.toolBtnActive : ''}`}
              onClick={toggleSelectMode}
            >
              {selectMode ? 'CANCEL' : 'SELECT'}
            </button>
            <button
              type="button"
              className={`${styles.toolBtn} ${showFilters ? styles.toolBtnActive : ''}`}
              onClick={toggleShowFilters}
            >
              FILTER
            </button>
          </div>

          {selectMode && selectedIds.size > 0 && (
            <div className={styles.bulkActions}>
              <span className={styles.selectedCount}>
                {selectedIds.size} SELECTED
              </span>
              <button
                type="button"
                className={styles.bulkBtn}
                onClick={handleBulkDownload}
              >
                <LuDownload /> DL
              </button>
              <button
                type="button"
                className={styles.bulkBtn}
                onClick={() => handleBulkHide(true)}
              >
                <LuEyeOff /> HIDE
              </button>
              <button
                type="button"
                className={`${styles.bulkBtn} ${styles.bulkDanger}`}
                onClick={handleBulkDelete}
              >
                <LuTrash2 /> DEL
              </button>
            </div>
          )}

          <div className={styles.toolbarRight}>
            {selectMode ? (
              <>
                <button
                  type="button"
                  className={styles.textBtn}
                  onClick={selectAll}
                >
                  ALL
                </button>
                <button
                  type="button"
                  className={styles.textBtn}
                  onClick={deselectAll}
                >
                  NONE
                </button>
              </>
            ) : (
              <div className={styles.zoomWrap}>
                <span className={styles.zoomLabel}>ZOOM</span>
                <input
                  type="range"
                  className={styles.zoomSlider}
                  min={80}
                  max={400}
                  step={10}
                  value={zoom}
                  onChange={(e) => setZoom(Number(e.target.value))}
                />
              </div>
            )}
          </div>
        </div>

        {showFilters && (
          <div className={styles.filterBar}>
            <div className={styles.filterGroup}>
              <label className={styles.filterLabel} htmlFor="filter-type">
                TYPE
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
                <option value="image">Image</option>
                <option value="video">Video</option>
              </select>
            </div>

            <div className={styles.filterGroup}>
              <label className={styles.filterLabel} htmlFor="filter-sort">
                SORT
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
                <option value="created_at">Date</option>
                <option value="file_size">Size</option>
                <option value="filename">Name</option>
              </select>
            </div>

            <div className={styles.filterGroup}>
              <label className={styles.filterLabel} htmlFor="filter-order">
                ORDER
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

            <label className={styles.filterCheck}>
              <input
                type="checkbox"
                checked={filters.show_hidden}
                onChange={(e) =>
                  updateFilters({ show_hidden: e.target.checked })
                }
              />
              HIDDEN
            </label>
          </div>
        )}

        {(isSearching || isSimilarMode) && (
          <div className={styles.searchInfo}>
            <span>
              {isSimilarMode && similarResults
                ? `${similarResults.length} SIMILAR`
                : searchResults
                  ? `${searchResults.length} RESULTS FOR "${searchQuery}"`
                  : null}
            </span>
            <button
              type="button"
              className={styles.textBtn}
              onClick={handleClearSearch}
            >
              CLEAR
            </button>
          </div>
        )}
      </div>

      {isLoading || isSimilarLoading ? (
        <div className={styles.loading}>
          {isSimilarLoading ? 'FINDING SIMILAR...' : 'LOADING MEDIA...'}
        </div>
      ) : displayItems.length === 0 ? (
        <div className={styles.empty}>
          <LuUpload className={styles.emptyIcon} />
          <span className={styles.emptyText}>
            {isSimilarMode
              ? 'NO SIMILAR MEDIA FOUND'
              : isSearching
                ? 'NO RESULTS'
                : 'NO UPLOADS'}
          </span>
          <span className={styles.emptySub}>
            {isSimilarMode
              ? 'Try a different source'
              : isSearching
                ? 'Adjust your query'
                : 'Upload media to begin'}
          </span>
        </div>
      ) : (
        <div
          className={styles.grid}
          style={{ '--grid-col-min': `${zoom}px` } as React.CSSProperties}
        >
          {displayItems.map((upload) => (
              <div
                key={upload.id}
                className={`${styles.card} ${selectMode && selectedIds.has(upload.id) ? styles.cardSelected : ''} ${upload.hidden ? styles.cardHidden : ''}`}
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
                    aria-label="Find similar"
                  >
                    <LuSparkles />
                  </button>
                )}
                <div className={styles.thumb}>
                  {upload.thumbnail_path ? (
                    <img
                      src={upload.thumbnail_path}
                      alt={upload.filename}
                      className={styles.thumbImg}
                    />
                  ) : (
                    <div className={styles.thumbEmpty}>
                      <LuUpload />
                    </div>
                  )}
                </div>
                <div className={styles.cardInfo}>
                  <span className={styles.cardName}>{upload.filename}</span>
                  <div className={styles.cardMeta}>
                    {upload.processing_status !== 'completed' && (
                      <span className={styles.statusBad}>
                        {upload.processing_status}
                      </span>
                    )}
                    {upload.embedding_provider === 'gemini' && (
                      <span className={styles.providerTag}>GEM</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
        </div>
      )}

      {selectedMediaId && currentUpload && (
        <div
          className={styles.panel}
          onClick={() => setSelectedMediaId(null)}
          onKeyDown={(e) => e.key === 'Escape' && setSelectedMediaId(null)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className={styles.panelContent}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.stopPropagation()}
            role="document"
          >
            <div className={styles.panelHeader}>
              <span className={styles.panelLabel}>MEDIA DETAIL</span>
              <button
                type="button"
                className={styles.panelClose}
                onClick={() => setSelectedMediaId(null)}
                aria-label="Close"
              >
                <LuX />
              </button>
            </div>

            <div className={styles.mediaWrap}>
              {currentUpload.file_type === 'image' ? (
                <img
                  src={currentUpload.file_path}
                  alt={currentUpload.filename}
                  className={styles.mediaImg}
                />
              ) : currentUpload.video_codec === 'hevc' && !currentUpload.file_path.includes('playback') ? (
                <div className={styles.hevcWarn}>
                  <TfiFaceSad className={styles.hevcIcon} />
                  <p>HEVC codec — browser playback unsupported</p>
                  <p className={styles.hevcSub}>Download to play locally</p>
                </div>
              ) : (
                <video
                  src={currentUpload.file_path}
                  className={styles.mediaVideo}
                  controls
                />
              )}
            </div>

            <div className={styles.panelBody}>
              <h3 className={styles.mediaTitle}>{currentUpload.filename}</h3>

              {uploadProgress[currentUpload.id] ? (
                <div className={styles.regenProgress}>
                  <div className={styles.regenBar}>
                    <div
                      className={styles.regenFill}
                      style={{
                        width: `${uploadProgress[currentUpload.id].percent}%`,
                      }}
                    />
                  </div>
                  <div className={styles.regenText}>
                    <span>{uploadProgress[currentUpload.id].percent}%</span>
                    <span>{uploadProgress[currentUpload.id].message}</span>
                  </div>
                </div>
              ) : currentUpload.description ? (
                <>
                  <p className={styles.mediaDesc}>
                    {currentUpload.description}
                  </p>
                  {currentUpload.description_audit_score !== null && (
                    <div className={styles.auditScore}>
                      <span className={styles.auditLabel}>QUALITY</span>
                      <span
                        className={`${styles.auditValue} ${
                          currentUpload.description_audit_score >= 80
                            ? styles.auditHigh
                            : currentUpload.description_audit_score >= 60
                              ? styles.auditMid
                              : styles.auditLow
                        }`}
                      >
                        {currentUpload.description_audit_score}/100
                      </span>
                    </div>
                  )}
                </>
              ) : null}

              <div className={styles.mediaMeta}>
                <span>TYPE: {currentUpload.file_type}</span>
                <span>STATUS: {currentUpload.processing_status}</span>
                {currentUpload.hidden && <span>HIDDEN</span>}
              </div>

              <div className={styles.mediaActions}>
                <button
                  type="button"
                  className={styles.actBtn}
                  onClick={() => {
                    handleFindSimilar(currentUpload)
                    setSelectedMediaId(null)
                  }}
                  disabled={isSimilarLoading || !currentUpload.has_embedding}
                >
                  <LuSparkles /> SIMILAR
                </button>
                {currentUpload.processing_status === 'completed' &&
                  currentUpload.embedding_provider !== 'gemini' && (
                    <button
                      type="button"
                      className={styles.actBtn}
                      onClick={() => handleRegenerate(currentUpload.id)}
                      disabled={regenerateDescription.isPending}
                    >
                      <LuRefreshCw />
                      {regenerateDescription.isPending ? 'REGEN...' : 'REGEN'}
                    </button>
                  )}
                <button
                  type="button"
                  className={styles.actBtn}
                  onClick={() => handleDownload(currentUpload)}
                >
                  <LuDownload /> DL
                </button>
                <button
                  type="button"
                  className={styles.actBtn}
                  onClick={() =>
                    handleToggleHidden(currentUpload.id, currentUpload.hidden)
                  }
                  disabled={toggleHiddenMutation.isPending}
                >
                  {currentUpload.hidden ? <LuEye /> : <LuEyeOff />}
                  {currentUpload.hidden ? 'SHOW' : 'HIDE'}
                </button>
                <button
                  type="button"
                  className={`${styles.actBtn} ${styles.actDanger}`}
                  onClick={() => handleDelete(currentUpload.id)}
                  disabled={deleteMutation.isPending}
                >
                  <LuTrash2 />
                  {deleteMutation.isPending ? 'DEL...' : 'DEL'}
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
