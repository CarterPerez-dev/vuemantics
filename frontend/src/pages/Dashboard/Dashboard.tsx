import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUpload, useSearch } from '@/hooks'
import { 
  MagnifyingGlassIcon,
  PlusIcon,
  AdjustmentsHorizontalIcon,
  PhotoIcon,
  VideoCameraIcon,
  ChevronDownIcon,
  ViewColumnsIcon
} from '@heroicons/react/24/outline'
import { debounce } from 'lodash'
import type { Upload } from '@/types'
import './Dashboard.css'

// Scale presets for the grid
const SCALE_PRESETS = [
  { name: 'Small', value: 150, cols: 'grid-cols-6 lg:grid-cols-8 xl:grid-cols-10' },
  { name: 'Medium', value: 200, cols: 'grid-cols-4 lg:grid-cols-6 xl:grid-cols-8' },
  { name: 'Large', value: 250, cols: 'grid-cols-3 lg:grid-cols-4 xl:grid-cols-6' },
  { name: 'Extra Large', value: 300, cols: 'grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' },
]

// Sort options
const SORT_OPTIONS = [
  { value: 'created_at_desc', label: 'Newest First', sortBy: 'created_at', order: 'desc' },
  { value: 'created_at_asc', label: 'Oldest First', sortBy: 'created_at', order: 'asc' },
  { value: 'filename_asc', label: 'Name (A-Z)', sortBy: 'filename', order: 'asc' },
  { value: 'filename_desc', label: 'Name (Z-A)', sortBy: 'filename', order: 'desc' },
  { value: 'file_size_desc', label: 'Size (Large-Small)', sortBy: 'file_size', order: 'desc' },
  { value: 'file_size_asc', label: 'Size (Small-Large)', sortBy: 'file_size', order: 'asc' },
]

function Dashboard() {
  const navigate = useNavigate()
  const { useUploadsList, getFileUrl } = useUpload()
  const { search, isSearching, searchData } = useSearch()
  
  // State
  const [searchQuery, setSearchQuery] = useState('')
  const [scaleIndex, setScaleIndex] = useState(1) // Default to Medium
  const [sortValue, setSortValue] = useState('created_at_desc')
  const [isFilterMenuOpen, setIsFilterMenuOpen] = useState(false)
  const [displayItems, setDisplayItems] = useState<Upload[]>([])
  const [isTransitioning, setIsTransitioning] = useState(false)
  const previousItemsRef = useRef<Upload[]>([])
  
  // Get current sort option
  const currentSort = SORT_OPTIONS.find(opt => opt.value === sortValue) || SORT_OPTIONS[0]
  const currentScale = SCALE_PRESETS[scaleIndex]
  
  // Fetch uploads with current sort
  const { data: uploads, isLoading } = useUploadsList({
    sort_by: currentSort.sortBy,
    sort_order: currentSort.order,
    page_size: 100,
  })
  
  // Debounced search function - faster for smooth feel
  const debouncedSearch = useCallback(
    debounce(async (query: string) => {
      if (query.trim() && query.length >= 3) { // Only search for 3+ characters to reduce OpenAI calls
        await search.mutateAsync({ query, limit: 100 })
      }
    }, 150), // Reduced from 300ms to 150ms for snappier feel
    []
  )
  
  // Handle search input change - smooth like state dropdown
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value
    setSearchQuery(query)
    
    if (query.trim()) {
      debouncedSearch(query)
    }
    // Note: When query is empty, the useEffect will automatically show all uploads
  }
  
  // Sort function
  const sortItems = useCallback((items: Upload[]) => {
    if (!items || items.length === 0) return []
    
    const sortedItems = [...items].sort((a, b) => {
      switch (currentSort.sortBy) {
        case 'created_at':
          const dateA = new Date(a.created_at).getTime()
          const dateB = new Date(b.created_at).getTime()
          return currentSort.order === 'desc' ? dateB - dateA : dateA - dateB
          
        case 'updated_at':
          const updatedA = new Date(a.updated_at).getTime()
          const updatedB = new Date(b.updated_at).getTime()
          return currentSort.order === 'desc' ? updatedB - updatedA : updatedA - updatedB
          
        case 'filename':
          const nameA = a.filename.toLowerCase()
          const nameB = b.filename.toLowerCase()
          return currentSort.order === 'desc' ? nameB.localeCompare(nameA) : nameA.localeCompare(nameB)
          
        case 'file_size':
          return currentSort.order === 'desc' ? b.file_size - a.file_size : a.file_size - b.file_size
          
        default:
          return 0
      }
    })
    
    return sortedItems
  }, [currentSort])

  // Update display items based on search results or uploads - smooth like state dropdown
  useEffect(() => {
    let newItems: Upload[] = []
    
    if (searchQuery.trim() && searchData) {
      // Use search results but apply frontend sorting, filter out failed uploads
      newItems = sortItems(searchData.results.map(result => result.upload).filter(upload => upload.processing_status !== 'failed'))
    } else if (!searchQuery.trim()) {
      // Use regular uploads when no search query, filter out failed uploads
      newItems = sortItems((uploads?.items || []).filter(upload => upload.processing_status !== 'failed'))
    } else {
      // Keep previous items while search is loading (prevents flicker)
      newItems = displayItems
    }
    
    // Update immediately for smooth transitions (like state dropdown)
    const itemsChanged = JSON.stringify(newItems.map(item => item.id)) !== 
                        JSON.stringify(previousItemsRef.current.map(item => item.id))
    
    if (itemsChanged) {
      // Update immediately for real-time feel
      previousItemsRef.current = newItems
      setDisplayItems(newItems)
    }
  }, [searchQuery, searchData, uploads, currentSort, sortItems, displayItems])
  
  // Calculate display count (excluding failed uploads)
  const displayCount = searchQuery.trim() 
    ? displayItems.length 
    : (uploads?.items || []).filter(upload => upload.processing_status !== 'failed').length
  
  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1048576).toFixed(1) + ' MB'
  }
  
  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="dashboard-gallery">
      {/* Fixed Header Container */}
      <div className="fixed-header-container">
        {/* Search Bar Section */}
        <div className="search-section">
          <div className="search-container max-w-7xl mx-auto px-4 py-4">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                className="search-input w-full pl-12 pr-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-white/30 focus:bg-black/50 transition-all duration-200"
                placeholder="Search your media with semantics..."
                value={searchQuery}
                onChange={handleSearchChange}
                autoComplete="off"
              />
              {isSearching && searchQuery.trim() && (
                <div className="absolute right-4 top-1/2 transform -translate-y-1/2 opacity-60">
                  <div className="search-spinner w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                </div>
              )}
            </div>
            {searchQuery && searchData && (
              <p className="search-status text-sm text-gray-400 mt-2">
                Found {searchData.returned_count} results in {searchData.search_time_ms.toFixed(0)}ms
              </p>
            )}
          </div>
        </div>

        {/* Controls Bar */}
        <div className="controls-bar">
          <div className="controls-container max-w-7xl mx-auto px-4 py-4 flex items-center justify-between gap-4 flex-wrap">
            {/* Left: Count Display */}
            <div className="count-display flex items-center gap-2">
              <span className="text-lg font-semibold text-white">{displayCount}</span>
              <span className="text-gray-400">
                {searchQuery ? 'results' : 'items'}
              </span>
            </div>

            {/* Right: Controls */}
            <div className="controls-group flex items-center gap-4">
              {/* Scale Control */}
              <div className="scale-control flex items-center gap-2">
                <ViewColumnsIcon className="w-5 h-5 text-gray-400" />
                <div className="scale-slider flex items-center gap-1">
                  {SCALE_PRESETS.map((preset, index) => (
                    <button
                      key={preset.name}
                      className={`scale-dot w-2 h-2 rounded-full transition-all duration-200 ${
                        index === scaleIndex
                          ? 'bg-white w-6'
                          : index < scaleIndex
                          ? 'bg-gray-400'
                          : 'bg-gray-600 hover:bg-gray-500'
                      }`}
                      onClick={() => setScaleIndex(index)}
                      title={preset.name}
                    />
                  ))}
                </div>
              </div>

              {/* Sort Dropdown */}
              <div className="sort-control relative">
                <button
                  className="sort-button flex items-center gap-2 px-4 py-2 bg-black/30 border border-white/10 rounded-lg text-white hover:bg-black/50 transition-all duration-200"
                  onClick={() => setIsFilterMenuOpen(!isFilterMenuOpen)}
                >
                  <AdjustmentsHorizontalIcon className="w-4 h-4" />
                  <span className="text-sm font-medium">{currentSort.label}</span>
                  <ChevronDownIcon className={`w-4 h-4 transition-transform duration-200 ${isFilterMenuOpen ? 'rotate-180' : ''}`} />
                </button>
                
                {isFilterMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setIsFilterMenuOpen(false)}
                    />
                    <div className="sort-dropdown absolute right-0 top-full mt-2 w-56 pgv-glass-heavy rounded-lg shadow-lg z-20 overflow-hidden pgv-fade-in">
                      {SORT_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          className={`sort-option w-full px-4 py-3 text-left text-sm hover:bg-white/10 transition-colors duration-200 ${
                            sortValue === option.value ? 'bg-white/10 text-white font-medium' : 'text-gray-300'
                          }`}
                          onClick={() => {
                            setSortValue(option.value)
                            setIsFilterMenuOpen(false)
                          }}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Media Grid with proper spacing */}
      <div className="media-gallery-wrapper">
        <div className="media-gallery max-w-7xl mx-auto px-4 pb-8">
          {isLoading ? (
            <div className="loading-state flex items-center justify-center py-20">
              <div className="pgv-loading-spinner"></div>
            </div>
          ) : displayItems.length === 0 && searchQuery ? (
            <div className="empty-search-state text-center py-20">
              <MagnifyingGlassIcon className="w-16 h-16 mx-auto text-gray-600 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No results found</h3>
              <p className="text-gray-400">Try a different search term or clear the search</p>
            </div>
          ) : (
            <div className={`media-grid grid ${currentScale.cols} ${isTransitioning ? 'is-transitioning' : ''}`}>
              {/* Quick Upload Box - Always First */}
              <button
                className="quick-upload-box media-grid-item pgv-glass border-2 border-dashed border-white/20 hover:border-white/40 rounded-xl flex flex-col items-center justify-center gap-3 transition-all duration-300 group"
                onClick={() => navigate('/upload')}
              >
                <div className="upload-icon-wrapper p-4 rounded-full bg-white/10 group-hover:bg-white/20 transition-colors duration-200">
                  <PlusIcon className="w-8 h-8 text-white" />
                </div>
                <span className="text-sm font-medium text-gray-300 group-hover:text-white">Quick Upload</span>
              </button>

              {/* Media Items */}
              {displayItems.map((item, index) => (
                <div
                  key={item.id}
                  className="media-item media-grid-item group relative pgv-glass rounded-xl overflow-hidden cursor-pointer transition-all duration-300"
                  style={{ 
                    animationDelay: `${Math.min(index * 20, 200)}ms`
                  }}
                >
                  {/* Thumbnail or Placeholder */}
                  {item.thumbnail_path ? (
                    <img
                      src={getFileUrl(item.thumbnail_path)}
                      alt={item.filename}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
                      {item.file_type === 'image' ? (
                        <PhotoIcon className="w-12 h-12 text-gray-600" />
                      ) : (
                        <VideoCameraIcon className="w-12 h-12 text-gray-600" />
                      )}
                    </div>
                  )}

                  {/* Processing Status Badge */}
                  {item.processing_status !== 'completed' && (
                    <div className="absolute top-2 right-2">
                      <span className={`status-badge px-2 py-1 rounded-md text-xs font-medium backdrop-blur-md ${
                        item.processing_status === 'failed' ? 'bg-red-500/80 text-white' :
                        item.processing_status === 'pending' ? 'bg-yellow-500/80 text-white' :
                        'bg-blue-500/80 text-white'
                      }`}>
                        {item.processing_status}
                      </span>
                    </div>
                  )}

                  {/* Video Duration (if applicable) */}
                  {item.file_type === 'video' && item.metadata?.duration_seconds && (
                    <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/70 backdrop-blur-sm rounded text-xs text-white">
                      {Math.floor(item.metadata.duration_seconds / 60)}:{(item.metadata.duration_seconds % 60).toString().padStart(2, '0')}
                    </div>
                  )}

                  {/* Hover Overlay */}
                  <div className="media-overlay absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="absolute bottom-0 left-0 right-0 p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
                      <p className="text-white font-medium text-sm truncate mb-1">{item.filename}</p>
                      <div className="flex items-center justify-between text-xs text-gray-300">
                        <span>{formatDate(item.created_at)}</span>
                        <span>{formatFileSize(item.file_size)}</span>
                      </div>
                      {item.gemini_summary && (
                        <p className="text-xs text-gray-400 mt-2 line-clamp-2">{item.gemini_summary}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
