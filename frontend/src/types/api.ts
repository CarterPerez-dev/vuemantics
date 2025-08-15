/**
 * API request and response types
 */

import { FileType, ProcessingStatus, SortBy, SortOrder, Upload, SearchResult } from './models'

// Auth types
export interface LoginCredentials {
  username: string // OAuth2 expects username field (email value)
  password: string
}

export interface RegisterData {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface PasswordChangeRequest {
  current_password: string
  new_password: string
}

// Upload types
export interface UploadListParams {
  page?: number
  page_size?: number
  file_type?: FileType
  processing_status?: ProcessingStatus
  sort_by?: SortBy
  sort_order?: SortOrder
}

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface BulkUploadResponse {
  successful: Upload[]
  failed: Array<{
    filename: string
    error: string
  }>
  total_processed: number
  total_successful: number
  total_failed: number
}

// Search types
export interface SearchRequest {
  query: string
  limit?: number
  similarity_threshold?: number
  file_types?: FileType[]
  date_from?: string
  date_to?: string
  user_id?: string
}

export interface SearchResponse {
  results: SearchResult[]
  total_found: number
  returned_count: number
  search_time_ms: number
  query: string
  query_embedding_generated: boolean
  applied_filters: Record<string, any> | null
}

export interface SimilarUploadsRequest {
  upload_id: string
  limit?: number
  similarity_threshold?: number
  include_same_user?: boolean
}

export interface SearchSuggestionsParams {
  q: string
  limit?: number
}

export interface BatchSearchResponse {
  [query: string]: SearchResponse
}

// Health check types
export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy'
  environment: string
  version: string
  checks: {
    database?: 'healthy' | 'unhealthy'
    redis?: 'healthy' | 'unhealthy'
    ai?: 'healthy' | 'unhealthy'
  }
}

export interface AIHealthResponse {
  status: 'healthy' | 'unhealthy'
  services: {
    gemini: boolean
    openai: boolean
  }
}
