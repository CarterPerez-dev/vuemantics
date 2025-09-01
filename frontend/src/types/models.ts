/**
 * Core data models matching backend Pydantic schemas
 */

// User models
export interface User {
  id: string
  email: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// Upload models
export type FileType = 'image' | 'video'
export type ProcessingStatus = 'pending' | 'analyzing' | 'embedding' | 'completed' | 'failed'
export type SortBy = 'created_at' | 'updated_at' | 'file_size' | 'filename'
export type SortOrder = 'asc' | 'desc'

export interface Upload {
  id: string
  user_id: string
  filename: string
  file_path: string
  file_type: FileType
  file_size: number
  mime_type: string
  processing_status: ProcessingStatus
  gemini_summary: string | null
  has_embedding?: boolean
  thumbnail_path: string | null
  error_message: string | null
  metadata: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface UploadMetadata {
  // Image metadata
  width?: number
  height?: number
  format?: string
  mode?: string
  
  // Video metadata
  fps?: number
  frame_count?: number
  duration_seconds?: number
  
  // Common
  file_size_mb: number
}

// Search models
export interface SearchResult {
  upload: Upload
  similarity_score: number
  distance: number
  rank: number
}

export interface SearchStats {
  total_uploads: number
  searchable_uploads: number
  processing_uploads: number
  failed_uploads: number
  stats_by_status: Record<string, number>
}

// Generic models
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ErrorResponse {
  detail: string
  code?: string
  field?: string
}

export interface ValidationError {
  detail: string
  errors: Array<{
    field: string
    message: string
    type: string
  }>
}
