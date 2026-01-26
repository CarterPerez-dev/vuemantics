// ===================
// © AngelaMos | 2026
// config.ts
// ===================

export const API_ENDPOINTS = {
  AUTH: {
    REGISTER: `/auth/register`,
    LOGIN: `/auth/token`,
    REFRESH: `/auth/token/refresh`,
    ME: `/auth/me`,
  },
  UPLOADS: {
    BASE: `/uploads`,
    BY_ID: (id: string) => `/uploads/${id}`,
    METADATA: (id: string) => `/uploads/${id}/metadata`,
    HIDE: (id: string) => `/uploads/${id}/hide`,
    REGENERATE: (id: string) => `/uploads/${id}/regenerate-description`,
    BULK_DELETE: `/uploads/bulk/delete`,
    BULK_HIDE: `/uploads/bulk/hide`,
  },
  SEARCH: {
    BASE: `/search`,
    SIMILAR: (uploadId: string) => `/search/similar/${uploadId}`,
    SUGGESTIONS: `/search/suggestions`,
    BATCH: `/search/batch`,
    STATS: `/search/stats`,
  },
  CLIENT_CONFIG: `/client-config`,
  HEALTH: `/health`,
} as const

export const WEBSOCKET_ENDPOINTS = {
  UPLOADS: `/api/ws/uploads`,
} as const

export const QUERY_KEYS = {
  AUTH: {
    ALL: ['auth'] as const,
    ME: () => [...QUERY_KEYS.AUTH.ALL, 'me'] as const,
  },
  UPLOADS: {
    ALL: ['uploads'] as const,
    LIST: () => [...QUERY_KEYS.UPLOADS.ALL, 'list'] as const,
    BY_ID: (id: string) => [...QUERY_KEYS.UPLOADS.ALL, 'detail', id] as const,
    METADATA: (id: string) =>
      [...QUERY_KEYS.UPLOADS.ALL, 'metadata', id] as const,
  },
  SEARCH: {
    ALL: ['search'] as const,
    QUERY: (query: string) => [...QUERY_KEYS.SEARCH.ALL, 'query', query] as const,
    SIMILAR: (uploadId: string) =>
      [...QUERY_KEYS.SEARCH.ALL, 'similar', uploadId] as const,
    SUGGESTIONS: (query: string) =>
      [...QUERY_KEYS.SEARCH.ALL, 'suggestions', query] as const,
    STATS: () => [...QUERY_KEYS.SEARCH.ALL, 'stats'] as const,
  },
  CLIENT_CONFIG: ['client-config'] as const,
} as const

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  UPLOAD: '/upload',
  GALLERY: '/gallery',
} as const

export const STORAGE_KEYS = {
  AUTH: 'auth-storage',
  UI: 'ui-storage',
} as const

export const QUERY_CONFIG = {
  STALE_TIME: {
    USER: 1000 * 60 * 5,
    STATIC: Infinity,
    FREQUENT: 1000 * 30,
  },
  GC_TIME: {
    DEFAULT: 1000 * 60 * 30,
    LONG: 1000 * 60 * 60,
  },
  RETRY: {
    DEFAULT: 3,
    NONE: 0,
  },
} as const

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER: 500,
} as const

export const PASSWORD_CONSTRAINTS = {
  MIN_LENGTH: 8,
  MAX_LENGTH: 72,
} as const

export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_SIZE: 20,
  MAX_SIZE: 100,
} as const

export type ApiEndpoint = typeof API_ENDPOINTS
export type QueryKey = typeof QUERY_KEYS
export type Route = typeof ROUTES
