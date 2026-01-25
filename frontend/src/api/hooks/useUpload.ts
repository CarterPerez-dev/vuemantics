// ===================
// © AngelaMos | 2026
// useUpload.ts
// ===================

import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  isValidPaginatedUploadResponse,
  isValidUploadResponse,
  type PaginatedUploadResponse,
  UPLOAD_ERROR_MESSAGES,
  UPLOAD_SUCCESS_MESSAGES,
  type UploadListParams,
  type UploadResponse,
  UploadResponseError,
} from '@/api/types'
import { API_ENDPOINTS, QUERY_KEYS } from '@/config'
import { apiClient } from '@/core/api'

export const uploadQueries = {
  all: () => QUERY_KEYS.UPLOADS.ALL,
  list: (params: UploadListParams) =>
    [...QUERY_KEYS.UPLOADS.ALL, 'list', params] as const,
  detail: (id: string) => QUERY_KEYS.UPLOADS.BY_ID(id),
  metadata: (id: string) => QUERY_KEYS.UPLOADS.METADATA(id),
} as const

const fetchUploads = async (
  params: UploadListParams
): Promise<PaginatedUploadResponse> => {
  const response = await apiClient.get<unknown>(API_ENDPOINTS.UPLOADS.BASE, {
    params,
  })
  const data: unknown = response.data

  if (!isValidPaginatedUploadResponse(data)) {
    throw new UploadResponseError(
      UPLOAD_ERROR_MESSAGES.INVALID_UPLOAD_LIST_RESPONSE,
      API_ENDPOINTS.UPLOADS.BASE
    )
  }

  return data
}

const fetchUploadById = async (id: string): Promise<UploadResponse> => {
  const response = await apiClient.get<unknown>(API_ENDPOINTS.UPLOADS.BY_ID(id))
  const data: unknown = response.data

  if (!isValidUploadResponse(data)) {
    throw new UploadResponseError(
      UPLOAD_ERROR_MESSAGES.INVALID_UPLOAD_RESPONSE,
      API_ENDPOINTS.UPLOADS.BY_ID(id)
    )
  }

  return data
}

const createUpload = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post<unknown>(
    API_ENDPOINTS.UPLOADS.BASE,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  )

  const data: unknown = response.data

  if (!isValidUploadResponse(data)) {
    throw new UploadResponseError(
      UPLOAD_ERROR_MESSAGES.INVALID_UPLOAD_RESPONSE,
      API_ENDPOINTS.UPLOADS.BASE
    )
  }

  return data
}

const deleteUpload = async (id: string): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.UPLOADS.BY_ID(id))
}

const fetchUploadMetadata = async (
  id: string
): Promise<Record<string, unknown>> => {
  const response = await apiClient.get<Record<string, unknown>>(
    API_ENDPOINTS.UPLOADS.METADATA(id)
  )
  return response.data
}

export const useUploads = (
  params: UploadListParams
): UseQueryResult<PaginatedUploadResponse, Error> => {
  return useQuery({
    queryKey: uploadQueries.list(params),
    queryFn: () => fetchUploads(params),
  })
}

export const useUpload = (id: string): UseQueryResult<UploadResponse, Error> => {
  return useQuery({
    queryKey: uploadQueries.detail(id),
    queryFn: () => fetchUploadById(id),
    enabled: Boolean(id),
  })
}

export const useUploadMetadata = (
  id: string
): UseQueryResult<Record<string, unknown>, Error> => {
  return useQuery({
    queryKey: uploadQueries.metadata(id),
    queryFn: () => fetchUploadMetadata(id),
    enabled: Boolean(id),
  })
}

export const useCreateUpload = (): UseMutationResult<
  UploadResponse,
  Error,
  File
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createUpload,
    onSuccess: (_data: UploadResponse): void => {
      queryClient.invalidateQueries({ queryKey: uploadQueries.all() })
      toast.success(UPLOAD_SUCCESS_MESSAGES.UPLOAD_COMPLETE)
    },
    onError: (error: Error): void => {
      const message =
        error instanceof UploadResponseError
          ? error.message
          : UPLOAD_ERROR_MESSAGES.UPLOAD_FAILED
      toast.error(message)
    },
  })
}

export const useDeleteUpload = (): UseMutationResult<void, Error, string> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteUpload,
    onSuccess: (): void => {
      queryClient.invalidateQueries({ queryKey: uploadQueries.all() })
      toast.success(UPLOAD_SUCCESS_MESSAGES.DELETE_COMPLETE)
    },
    onError: (error: Error): void => {
      const message =
        error instanceof UploadResponseError
          ? error.message
          : UPLOAD_ERROR_MESSAGES.DELETE_FAILED
      toast.error(message)
    },
  })
}

const toggleUploadHidden = async (
  id: string,
  hidden: boolean
): Promise<UploadResponse> => {
  const response = await apiClient.patch<unknown>(
    API_ENDPOINTS.UPLOADS.HIDE(id),
    null,
    { params: { hidden } }
  )
  return response.data as UploadResponse
}

const bulkDeleteUploads = async (ids: string[]): Promise<{ deleted: number }> => {
  const response = await apiClient.post<{ deleted: number }>(
    API_ENDPOINTS.UPLOADS.BULK_DELETE,
    ids
  )
  return response.data
}

const bulkHideUploads = async (
  ids: string[],
  hidden: boolean
): Promise<{ updated: number }> => {
  const response = await apiClient.post<{ updated: number }>(
    API_ENDPOINTS.UPLOADS.BULK_HIDE,
    ids,
    { params: { hidden } }
  )
  return response.data
}

export const useToggleUploadHidden = (): UseMutationResult<
  UploadResponse,
  Error,
  { id: string; hidden: boolean }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, hidden }) => toggleUploadHidden(id, hidden),
    onSuccess: (data): void => {
      queryClient.invalidateQueries({ queryKey: uploadQueries.all() })
      toast.success(data.hidden ? 'Upload hidden' : 'Upload unhidden')
    },
    onError: (): void => {
      toast.error('Failed to update upload')
    },
  })
}

export const useBulkDeleteUploads = (): UseMutationResult<
  { deleted: number },
  Error,
  string[]
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: bulkDeleteUploads,
    onSuccess: (data): void => {
      queryClient.invalidateQueries({ queryKey: uploadQueries.all() })
      toast.success(
        `Deleted ${data.deleted} upload${data.deleted !== 1 ? 's' : ''}`
      )
    },
    onError: (): void => {
      toast.error('Failed to delete uploads')
    },
  })
}

export const useBulkHideUploads = (): UseMutationResult<
  { updated: number },
  Error,
  { ids: string[]; hidden: boolean }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ ids, hidden }) => bulkHideUploads(ids, hidden),
    onSuccess: (data, { hidden }): void => {
      queryClient.invalidateQueries({ queryKey: uploadQueries.all() })
      toast.success(
        `${hidden ? 'Hidden' : 'Unhidden'} ${data.updated} upload${data.updated !== 1 ? 's' : ''}`
      )
    },
    onError: (): void => {
      toast.error('Failed to update uploads')
    },
  })
}

const regenerateDescription = async (id: string): Promise<UploadResponse> => {
  const response = await apiClient.post<unknown>(
    API_ENDPOINTS.UPLOADS.REGENERATE(id)
  )
  const data: unknown = response.data

  if (!isValidUploadResponse(data)) {
    throw new UploadResponseError(
      UPLOAD_ERROR_MESSAGES.INVALID_UPLOAD_RESPONSE,
      API_ENDPOINTS.UPLOADS.REGENERATE(id)
    )
  }

  return data
}

export const useRegenerateDescription = (): UseMutationResult<
  UploadResponse,
  Error,
  string
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: regenerateDescription,
    onSuccess: (data): void => {
      queryClient.invalidateQueries({ queryKey: uploadQueries.detail(data.id) })
      queryClient.invalidateQueries({ queryKey: uploadQueries.all() })
      toast.success(UPLOAD_SUCCESS_MESSAGES.REGENERATE_STARTED)
    },
    onError: (error: Error): void => {
      const message =
        error instanceof UploadResponseError
          ? error.message
          : UPLOAD_ERROR_MESSAGES.REGENERATE_FAILED
      toast.error(message)
    },
  })
}
