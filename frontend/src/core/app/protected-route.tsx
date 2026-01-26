// ===================
// © AngelaMos | 2026
// protected-route.tsx
// ===================

import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { ROUTES } from '@/config'
import { useAuthStore } from '@/core/lib/stores'

interface ProtectedRouteProps {
  redirectTo?: string
}

export function ProtectedRoute({
  redirectTo = ROUTES.LOGIN,
}: ProtectedRouteProps): React.ReactElement {
  const location = useLocation()
  const { isAuthenticated, isLoading, accessToken } = useAuthStore()

  const hasToken = accessToken !== null && accessToken.length > 0

  if (isLoading) {
    return <div>Loading...</div>
  }

  // Allow access if authenticated OR if we have a valid token
  if (!isAuthenticated && !hasToken) {
    return (
      <Navigate
        to={redirectTo}
        state={{ from: location.pathname + location.search }}
        replace
      />
    )
  }

  return <Outlet />
}
