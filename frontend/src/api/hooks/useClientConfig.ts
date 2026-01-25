// ===================
// © AngelaMos | 2026
// useClientConfig.ts
// ===================

import { type UseQueryResult, useQuery } from '@tanstack/react-query'
import {
  CLIENT_CONFIG_ERROR_MESSAGES,
  type ClientConfigResponse,
  ClientConfigError,
  isValidClientConfigResponse,
} from '@/api/types'
import { API_ENDPOINTS, QUERY_CONFIG, QUERY_KEYS } from '@/config'
import { apiClient } from '@/core/api'

const fetchClientConfig = async (): Promise<ClientConfigResponse> => {
  const response = await apiClient.get<unknown>(API_ENDPOINTS.CLIENT_CONFIG)
  const data: unknown = response.data

  if (!isValidClientConfigResponse(data)) {
    throw new ClientConfigError(
      CLIENT_CONFIG_ERROR_MESSAGES.INVALID_RESPONSE,
      API_ENDPOINTS.CLIENT_CONFIG
    )
  }

  return data
}

export const useClientConfig = (): UseQueryResult<
  ClientConfigResponse,
  Error
> => {
  return useQuery({
    queryKey: QUERY_KEYS.CLIENT_CONFIG,
    queryFn: fetchClientConfig,
    staleTime: QUERY_CONFIG.STALE_TIME.STATIC,
    gcTime: QUERY_CONFIG.GC_TIME.LONG,
    retry: QUERY_CONFIG.RETRY.DEFAULT,
  })
}
