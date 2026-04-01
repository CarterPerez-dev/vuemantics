// ===================
// © AngelaMos | 2026
// useSettings.ts
// ===================

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/core/api'
import { API_ENDPOINTS, QUERY_KEYS } from '@/config'
import {
  providerResponseSchema,
  reembedResponseSchema,
  type EmbeddingProvider,
  type ProviderResponse,
  type ReembedResponse,
} from '@/api/types'

const fetchProvider = async (): Promise<ProviderResponse> => {
  const res = await apiClient.get(API_ENDPOINTS.SETTINGS.PROVIDER)
  return providerResponseSchema.parse(res.data)
}

const postSetProvider = async (provider: EmbeddingProvider): Promise<ProviderResponse> => {
  const res = await apiClient.post(API_ENDPOINTS.SETTINGS.PROVIDER, { provider })
  return providerResponseSchema.parse(res.data)
}

const postTriggerReembed = async (): Promise<ReembedResponse> => {
  const res = await apiClient.post(API_ENDPOINTS.SETTINGS.REEMBED)
  return reembedResponseSchema.parse(res.data)
}

export const useProviderSettings = () =>
  useQuery({
    queryKey: QUERY_KEYS.SETTINGS.PROVIDER(),
    queryFn: fetchProvider,
  })

export const useSetProvider = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (provider: EmbeddingProvider) => postSetProvider(provider),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.SETTINGS.ALL }),
  })
}

export const useTriggerReembed = () =>
  useMutation({ mutationFn: postTriggerReembed })
