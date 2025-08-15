import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { useState } from 'react'
import type {
  Upload,
  UploadListParams,
  UploadProgress,
  UploadMetadata,
  PaginatedResponse,
  ApiError,
} from '@/types'

// Custom hook for file uploads
export const useUpload = () => {
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState<Record<string, UploadProgress>>({})

  // Upload file mutation
  const uploadFile = useMutation<Upload, Error, File>({
    mutationFn: async (file) => {
      const formData = new FormData()
      formData.append('file', file)

      const tempId = `temp-${Date.now()}`
      
      const response = await apiClient.post('/api/uploads', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress(prev => ({
              ...prev,
              [tempId]: {
                loaded: progressEvent.loaded,
                total: progressEvent.total,
                percentage,
              }
            }))
          }
        },
      })

      // Clean up progress tracking
      setUploadProgress(prev => {
        const newProgress = { ...prev }
        delete newProgress[tempId]
        return newProgress
      })

      return response.data
    },
    onSuccess: () => {
      // Invalidate uploads list to refetch
      queryClient.invalidateQueries({ queryKey: ['uploads'] })
    },
    onError: (error: ApiError) => {
      console.error('Upload failed:', error.response?.data || error.message)
    },
  })

  // List uploads query hook
  const useUploadsList = (params: UploadListParams = {}) => {
    return useQuery<PaginatedResponse<Upload>>({
      queryKey: ['uploads', params],
      queryFn: async () => {
        const response = await apiClient.get('/api/uploads', { params })
        return response.data
      },
    })
  }

  // Get single upload query
  const useUploadDetails = (uploadId: string | undefined) => {
    return useQuery<Upload>({
      queryKey: ['upload', uploadId],
      queryFn: async () => {
        const response = await apiClient.get(`/api/uploads/${uploadId}`)
        return response.data
      },
      enabled: !!uploadId,
    })
  }

  // Get upload metadata query
  const useUploadMetadata = (uploadId: string | undefined) => {
    return useQuery<UploadMetadata>({
      queryKey: ['upload-metadata', uploadId],
      queryFn: async () => {
        const response = await apiClient.get(`/api/uploads/${uploadId}/metadata`)
        return response.data
      },
      enabled: !!uploadId,
    })
  }

  // Delete upload mutation
  const deleteUpload = useMutation<void, Error, string>({
    mutationFn: async (uploadId) => {
      await apiClient.delete(`/api/uploads/${uploadId}`)
    },
    onSuccess: (_, uploadId) => {
      // Remove from cache
      queryClient.invalidateQueries({ queryKey: ['uploads'] })
      queryClient.removeQueries({ queryKey: ['upload', uploadId] })
      queryClient.removeQueries({ queryKey: ['upload-metadata', uploadId] })
    },
    onError: (error: ApiError) => {
      console.error('Delete failed:', error.response?.data || error.message)
    },
  })

  // Batch upload function
  const uploadMultipleFiles = async (files: File[]) => {
    const results = await Promise.allSettled(
      files.map(file => uploadFile.mutateAsync(file))
    )

    const successful = results
      .filter((result): result is PromiseFulfilledResult<Upload> => 
        result.status === 'fulfilled'
      )
      .map(result => result.value)

    const failed = results
      .filter((result): result is PromiseRejectedResult => 
        result.status === 'rejected'
      )
      .map((result, index) => ({
        filename: files[index].name,
        error: result.reason.message || 'Upload failed',
      }))

    return { successful, failed }
  }

  // Check processing status periodically
  const useProcessingStatus = (uploadId: string | undefined, interval = 5000) => {
    const { data, refetch } = useUploadDetails(uploadId)

    // Auto-refetch while processing
    useQuery({
      queryKey: ['processing-check', uploadId],
      queryFn: async () => {
        if (data?.processing_status && 
            ['pending', 'analyzing', 'embedding'].includes(data.processing_status)) {
          await refetch()
        }
        return null
      },
      enabled: !!uploadId && !!data && 
               ['pending', 'analyzing', 'embedding'].includes(data.processing_status),
      refetchInterval: interval,
    })

    return data
  }

  // Helper to get file URL
  const getFileUrl = (relativePath: string) => {
    return `/files/${relativePath}`
  }

  // Helper to check if upload is ready for search
  const isSearchable = (upload: Upload) => {
    return upload.processing_status === 'completed' && upload.has_embedding
  }

  return {
    // Upload actions
    uploadFile,
    uploadMultipleFiles,
    deleteUpload,

    // Query hooks
    useUploadsList,
    useUploadDetails,
    useUploadMetadata,
    useProcessingStatus,

    // Upload state
    uploadProgress,
    isUploading: uploadFile.isPending,
    uploadError: uploadFile.error,

    // Helpers
    getFileUrl,
    isSearchable,
  }
}
