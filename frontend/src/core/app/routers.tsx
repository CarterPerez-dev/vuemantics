// ===================
// © AngelaMos | 2026
// routers.tsx
// ===================

import { createBrowserRouter, type RouteObject } from 'react-router-dom'
import { ROUTES } from '@/config'
import { ProtectedRoute } from './protected-route'
import { Shell } from './shell'

const routes: RouteObject[] = [
  {
    path: ROUTES.HOME,
    lazy: () => import('@/routes/landing'),
  },
  {
    path: ROUTES.LOGIN,
    lazy: () => import('@/routes/login'),
  },
  {
    path: ROUTES.REGISTER,
    lazy: () => import('@/routes/register'),
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <Shell />,
        children: [
          {
            path: ROUTES.UPLOAD,
            lazy: () => import('@/routes/upload'),
          },
          {
            path: ROUTES.GALLERY,
            lazy: () => import('@/routes/gallery'),
          },
        ],
      },
    ],
  },
  {
    path: '*',
    lazy: () => import('@/routes/landing'),
  },
]

export const router = createBrowserRouter(routes)
