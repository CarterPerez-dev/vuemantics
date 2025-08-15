import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import Layout from '@/components/Layout/Layout'
import Home from '@/pages/Home/Home'
import Login from '@/pages/Login/Login'
import Register from '@/pages/Register/Register'
import Dashboard from '@/pages/Dashboard/Dashboard'
import Upload from '@/pages/Upload/Upload'
import NotFound from '@/pages/NotFound/NotFound'
import './App.css'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoadingUser } = useAuth()
  const location = useLocation()

  if (isLoadingUser) {
    return (
      <div className="pgv-loading-container">
        <div className="pgv-loading-spinner"></div>
        <p className="pgv-loading-text">Loading...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    // Redirect to login but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

// Public route wrapper (redirects to dashboard if already authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  
  if (isAuthenticated) {
    // Get the page they were trying to visit or default to dashboard
    const from = location.state?.from?.pathname || '/dashboard'
    return <Navigate to={from} replace />
  }

  return <>{children}</>
}

function App() {
  const { setupTokenRefresh } = useAuth()

  // Set up token auto-refresh
  useEffect(() => {
    const cleanup = setupTokenRefresh()
    return cleanup
  }, [setupTokenRefresh])

  return (
    <div className="app">
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Home />} />
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* Protected routes with layout */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  )
}

export default App
