// ===========================
// ©AngelaMos | 2026
// App.tsx
// ===========================

import { useEffect } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { RouterProvider } from 'react-router-dom'
import { toast, Toaster } from 'sonner'

import { queryClient } from '@/core/api'
import { router } from '@/core/app/routers'
import '@/core/app/toast.module.scss'

export default function App(): React.ReactElement {
  useEffect(() => {
    const handleToastClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const toastElement = target.closest('[data-sonner-toast]')
      if (toastElement) {
        toast.dismiss()
      }
    }

    document.addEventListener('click', handleToastClick)
    return () => document.removeEventListener('click', handleToastClick)
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        <RouterProvider router={router} />
        <Toaster
          position="top-right"
          duration={1769}
          theme="dark"
          toastOptions={{
            style: {
              background: 'hsl(0, 0%, 12.2%)',
              border: '1px solid hsl(0, 0%, 18%)',
              color: 'hsl(0, 0%, 98%)',
            },
          }}
        />
      </div>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
