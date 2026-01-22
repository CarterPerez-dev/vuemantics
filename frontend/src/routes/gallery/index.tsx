// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { useState } from 'react'
import { LuSearch, LuUpload, LuX } from 'react-icons/lu'
import { useSearchMutation, useUploads } from '@/api/hooks'
import type { SearchResult, UploadResponse } from '@/api/types'
import styles from './gallery.module.scss'

export function Component(): React.ReactElement {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null)
  const [selectedMedia, setSelectedMedia] = useState<UploadResponse | null>(null)

  const { data: uploads, isLoading } = useUploads({
    page: 1,
    page_size: 50,
    sort_by: 'created_at',
    sort_order: 'desc',
  })

  const searchMutation = useSearchMutation()

  const handleSearch = (e: React.FormEvent): void => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      setSearchResults(null)
      return
    }

    searchMutation.mutate(
      {
        query: searchQuery,
        limit: 50,
        similarity_threshold: 0.25,
      },
      {
        onSuccess: (data) => {
          setSearchResults(data.results)
        },
      }
    )
  }

  const handleClearSearch = (): void => {
    setSearchQuery('')
    setSearchResults(null)
  }

  const displayItems = searchResults
    ? searchResults.map((r) => r.upload)
    : uploads?.items ?? []

  const isSearching = searchResults !== null

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

          {isSearching && (
            <div className={styles.searchInfo}>
              <span className={styles.searchInfoText}>
                Found {searchResults.length} result{searchResults.length !== 1 ? 's' : ''}{' '}
                for "{searchQuery}"
              </span>
              <button
                type="button"
                className={styles.clearSearchBtn}
                onClick={handleClearSearch}
              >
                Clear search
              </button>
            </div>
          )}
        </div>

        {isLoading ? (
          <div className={styles.loading}>Loading your media...</div>
        ) : displayItems.length === 0 ? (
          <div className={styles.empty}>
            <LuUpload className={styles.emptyIcon} />
            <p className={styles.emptyText}>
              {isSearching ? 'No results found' : 'No uploads yet'}
            </p>
            <p className={styles.emptySubtext}>
              {isSearching
                ? 'Try a different search query'
                : 'Upload your first image or video to get started'}
            </p>
          </div>
        ) : (
          <div className={styles.grid}>
            {displayItems.map((upload) => (
              <div
                key={upload.id}
                className={styles.card}
                onClick={() => setSelectedMedia(upload)}
              >
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
                    <span className={styles.cardStatus}>{upload.processing_status}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedMedia && (
        <div className={styles.modal} onClick={() => setSelectedMedia(null)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
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
                <video src={selectedMedia.file_path} className={styles.modalVideo} controls />
              )}
            </div>

            <div className={styles.modalInfo}>
              <h3 className={styles.modalTitle}>{selectedMedia.filename}</h3>
              {selectedMedia.gemini_summary && (
                <p className={styles.modalDescription}>{selectedMedia.gemini_summary}</p>
              )}
              <div className={styles.modalMeta}>
                <span>Type: {selectedMedia.file_type}</span>
                <span>Status: {selectedMedia.processing_status}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

Component.displayName = 'Gallery'
