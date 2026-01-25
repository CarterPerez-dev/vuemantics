// ===================
// © AngelaMos | 2026
// useSearch.ts
// ===================

import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
} from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  isValidSearchResponse,
  SEARCH_ERROR_MESSAGES,
  type SearchRequest,
  type SearchResponse,
  SearchResponseError,
  type SearchResult,
} from '@/api/types'
import { API_ENDPOINTS, QUERY_KEYS } from '@/config'
import { apiClient } from '@/core/api'

export const searchQueries = {
  all: () => QUERY_KEYS.SEARCH.ALL,
  query: (query: string) => QUERY_KEYS.SEARCH.QUERY(query),
  similar: (uploadId: string) => QUERY_KEYS.SEARCH.SIMILAR(uploadId),
  suggestions: (query: string) => QUERY_KEYS.SEARCH.SUGGESTIONS(query),
  stats: () => QUERY_KEYS.SEARCH.STATS(),
} as const

const performSearch = async (
  searchRequest: SearchRequest
): Promise<SearchResponse> => {
  const response = await apiClient.post<unknown>(
    API_ENDPOINTS.SEARCH.BASE,
    searchRequest
  )
  const data: unknown = response.data

  if (!isValidSearchResponse(data)) {
    throw new SearchResponseError(
      SEARCH_ERROR_MESSAGES.INVALID_SEARCH_RESPONSE,
      API_ENDPOINTS.SEARCH.BASE
    )
  }

  return data
}

const fetchSimilarUploads = async (
  uploadId: string,
  limit: number = 10,
  includeOwn: boolean = true
): Promise<SearchResult[]> => {
  const response = await apiClient.get<SearchResult[]>(
    API_ENDPOINTS.SEARCH.SIMILAR(uploadId),
    {
      params: { limit, include_own: includeOwn },
    }
  )

  return response.data
}

const fetchSearchSuggestions = async (query: string): Promise<string[]> => {
  if (query.length < 2) return []

  const response = await apiClient.get<string[]>(
    API_ENDPOINTS.SEARCH.SUGGESTIONS,
    {
      params: { q: query },
    }
  )

  return response.data
}

const fetchSearchStats = async (): Promise<Record<string, number>> => {
  const response = await apiClient.get<Record<string, number>>(
    API_ENDPOINTS.SEARCH.STATS
  )
  return response.data
}

export const useSearch = (
  searchRequest: SearchRequest,
  options?: { enabled?: boolean }
): UseQueryResult<SearchResponse, Error> => {
  return useQuery({
    queryKey: searchQueries.query(searchRequest.query),
    queryFn: () => performSearch(searchRequest),
    enabled: options?.enabled !== false && Boolean(searchRequest.query),
  })
}

export const useSearchMutation = (): UseMutationResult<
  SearchResponse,
  Error,
  SearchRequest
> => {
  return useMutation({
    mutationFn: performSearch,
    onError: (error: Error): void => {
      const message =
        error instanceof SearchResponseError
          ? error.message
          : SEARCH_ERROR_MESSAGES.SEARCH_FAILED
      toast.error(message)
    },
  })
}

export const useSimilarUploads = (
  uploadId: string,
  limit: number = 10,
  includeOwn: boolean = true
): UseQueryResult<SearchResult[], Error> => {
  return useQuery({
    queryKey: searchQueries.similar(uploadId),
    queryFn: () => fetchSimilarUploads(uploadId, limit, includeOwn),
    enabled: Boolean(uploadId),
  })
}

export const useSearchSuggestions = (
  query: string
): UseQueryResult<string[], Error> => {
  return useQuery({
    queryKey: searchQueries.suggestions(query),
    queryFn: () => fetchSearchSuggestions(query),
    enabled: query.length >= 2,
    staleTime: 1000 * 60 * 5,
  })
}

export const useSearchStats = (): UseQueryResult<
  Record<string, number>,
  Error
> => {
  return useQuery({
    queryKey: searchQueries.stats(),
    queryFn: fetchSearchStats,
  })
}
