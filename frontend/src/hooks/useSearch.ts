import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { useState, useCallback, useRef } from 'react'
import debounce from 'lodash/debounce'
import type {
  SearchRequest,
  SearchResult,
  SearchResponse,
  SearchStats,
  BatchSearchResponse,
  ApiError,
} from '@/types'

// Custom hook for search functionality
export const useSearch = () => {
  const queryClient = useQueryClient()
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const suggestionsAbortController = useRef<AbortController>()

  // Main search mutation
  const search = useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: async (searchParams) => {
      const response = await apiClient.post('/api/search', searchParams)
      return response.data
    },
    onSuccess: (data) => {
      // Add to search history
      if (data.query && !searchHistory.includes(data.query)) {
        setSearchHistory(prev => [data.query, ...prev].slice(0, 10))
      }
    },
    onError: (error: ApiError) => {
      console.error('Search failed:', error.response?.data || error.message)
    },
  })

  // Find similar uploads query
  const useSimilarUploads = (uploadId: string | undefined, limit = 10, includeOwn = true) => {
    return useQuery<SearchResult[]>({
      queryKey: ['similar-uploads', uploadId, limit, includeOwn],
      queryFn: async () => {
        const response = await apiClient.get(`/api/search/similar/${uploadId}`, {
          params: { limit, include_own: includeOwn },
        })
        return response.data
      },
      enabled: !!uploadId,
    })
  }

  // Search suggestions query
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false)

  const fetchSuggestions = useCallback(
    debounce(async (partialQuery: string) => {
      if (partialQuery.length < 2) {
        setSuggestions([])
        return
      }

      // Cancel previous request
      if (suggestionsAbortController.current) {
        suggestionsAbortController.current.abort()
      }

      suggestionsAbortController.current = new AbortController()
      setIsLoadingSuggestions(true)

      try {
        const response = await apiClient.get('/api/search/suggestions', {
          params: { q: partialQuery },
          signal: suggestionsAbortController.current.signal,
        })
        setSuggestions(response.data)
      } catch (error: any) {
        if (error.code !== 'ERR_CANCELED' && error.name !== 'CanceledError') {
          console.error('Failed to fetch suggestions:', error)
          setSuggestions([])
        }
      } finally {
        setIsLoadingSuggestions(false)
      }
    }, 300),
    []
  )

  // Batch search mutation
  const batchSearch = useMutation<BatchSearchResponse, Error, string[]>({
    mutationFn: async (queries) => {
      const response = await apiClient.post('/api/search/batch', null, {
        params: { queries },
      })
      return response.data
    },
    onError: (error: ApiError) => {
      console.error('Batch search failed:', error.response?.data || error.message)
    },
  })

  // Search statistics query
  const useSearchStats = () => {
    return useQuery<SearchStats>({
      queryKey: ['search-stats'],
      queryFn: async () => {
        const response = await apiClient.get('/api/search/stats')
        return response.data
      },
    })
  }

  // Advanced search builder
  const buildSearchRequest = (
    query: string,
    options?: {
      onlyImages?: boolean
      onlyVideos?: boolean
      dateRange?: { from?: Date; to?: Date }
      minSimilarity?: number
      maxResults?: number
    }
  ): SearchRequest => {
    const request: SearchRequest = { query }

    if (options?.onlyImages) {
      request.file_types = ['image']
    } else if (options?.onlyVideos) {
      request.file_types = ['video']
    }

    if (options?.dateRange?.from) {
      request.date_from = options.dateRange.from.toISOString()
    }
    if (options?.dateRange?.to) {
      request.date_to = options.dateRange.to.toISOString()
    }

    if (options?.minSimilarity !== undefined) {
      request.similarity_threshold = options.minSimilarity
    }

    if (options?.maxResults !== undefined) {
      request.limit = options.maxResults
    }

    return request
  }

  // Clear search results
  const clearSearchResults = () => {
    queryClient.setQueryData(['search-results'], null)
  }

  // Format search time for display
  const formatSearchTime = (ms: number): string => {
    if (ms < 1000) {
      return `${Math.round(ms)}ms`
    }
    return `${(ms / 1000).toFixed(2)}s`
  }

  // Group search results by file type
  const groupResultsByType = (results: SearchResult[]) => {
    return results.reduce((acc, result) => {
      const type = result.upload.file_type
      if (!acc[type]) {
        acc[type] = []
      }
      acc[type].push(result)
      return acc
    }, {} as Record<string, SearchResult[]>)
  }

  return {
    // Search actions
    search,
    batchSearch,
    fetchSuggestions,
    clearSearchResults,

    // Query hooks
    useSimilarUploads,
    useSearchStats,

    // Search state
    isSearching: search.isPending,
    searchError: search.error,
    searchData: search.data,
    suggestions,
    isLoadingSuggestions,
    searchHistory,

    // Helpers
    buildSearchRequest,
    formatSearchTime,
    groupResultsByType,
  }
}
