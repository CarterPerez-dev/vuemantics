// ===================
// © AngelaMos | 2026
// useBulkUpload.ts
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
  type BatchListResponse,
  type BatchStatusResult,
  BULK_UPLOAD_ERROR_MESSAGES,
  BULK_UPLOAD_SUCCESS_MESSAGES,
  BulkUploadError,
  type BulkUploadResult,
  isValidBatchListResponse,
  isValidBatchStatusResult,
  isValidBulkUploadResult,
} from '@/api/types'
import { API_ENDPOINTS, QUERY_KEYS } from '@/config'
import { apiClient } from '@/core/api'

export const bulkUploadQueries = {
  batches: () => QUERY_KEYS.UPLOADS.BATCHES(),
  batch: (batchId: string) => QUERY_KEYS.UPLOADS.BATCH(batchId),
} as const

const createBulkUpload = async (files: File[]): Promise<BulkUploadResult> => {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  const response = await apiClient.post<unknown>(
    API_ENDPOINTS.UPLOADS.BULK_UPLOAD,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  )

  const data: unknown = response.data

  if (!isValidBulkUploadResult(data)) {
    throw new BulkUploadError(
      BULK_UPLOAD_ERROR_MESSAGES.INVALID_BULK_UPLOAD_RESPONSE,
      API_ENDPOINTS.UPLOADS.BULK_UPLOAD
    )
  }

  return data
}

const fetchBatchStatus = async (batchId: string): Promise<BatchStatusResult> => {
  const response = await apiClient.get<unknown>(
    API_ENDPOINTS.UPLOADS.BATCH(batchId)
  )
  const data: unknown = response.data

  if (!isValidBatchStatusResult(data)) {
    throw new BulkUploadError(
      BULK_UPLOAD_ERROR_MESSAGES.INVALID_BATCH_STATUS_RESPONSE,
      API_ENDPOINTS.UPLOADS.BATCH(batchId)
    )
  }

  return data
}

const fetchBatches = async (
  limit = 20,
  offset = 0
): Promise<BatchListResponse> => {
  const response = await apiClient.get<unknown>(API_ENDPOINTS.UPLOADS.BATCHES, {
    params: { limit, offset },
  })
  const data: unknown = response.data

  if (!isValidBatchListResponse(data)) {
    throw new BulkUploadError(
      BULK_UPLOAD_ERROR_MESSAGES.INVALID_BATCH_LIST_RESPONSE,
      API_ENDPOINTS.UPLOADS.BATCHES
    )
  }

  return data
}

export const useCreateBulkUpload = (): UseMutationResult<
  BulkUploadResult,
  Error,
  File[]
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createBulkUpload,
    onSuccess: (data): void => {
      queryClient.invalidateQueries({ queryKey: bulkUploadQueries.batches() })
      if (data.failed > 0) {
        toast.warning(
          `${data.failed} file${data.failed !== 1 ? 's' : ''} failed validation`
        )
      }
    },
    onError: (error: Error): void => {
      const message =
        error instanceof BulkUploadError
          ? error.message
          : BULK_UPLOAD_ERROR_MESSAGES.UPLOAD_FAILED
      toast.error(message)
    },
  })
}

export const useBatchStatus = (
  batchId: string
): UseQueryResult<BatchStatusResult, Error> => {
  return useQuery({
    queryKey: bulkUploadQueries.batch(batchId),
    queryFn: () => fetchBatchStatus(batchId),
    enabled: Boolean(batchId),
    refetchInterval: (data) => {
      // Stop polling if batch is complete or failed
      if (!data?.state.data) return false
      const status = data.state.data.status
      if (
        status === 'completed' ||
        status === 'failed' ||
        status === 'cancelled'
      ) {
        return false
      }
      return 2000 // Poll every 2 seconds while processing
    },
  })
}

export const useBatches = (
  limit = 20,
  offset = 0
): UseQueryResult<BatchListResponse, Error> => {
  return useQuery({
    queryKey: [...bulkUploadQueries.batches(), limit, offset],
    queryFn: () => fetchBatches(limit, offset),
  })
}
