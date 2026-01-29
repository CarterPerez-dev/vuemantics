/**
 * ©AngelaMos | 2025
 * shell.tsx
 */

import { Suspense } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import { GiExitDoor } from 'react-icons/gi'
import { GrCloudUpload } from 'react-icons/gr'
import { ImImages } from 'react-icons/im'
import { LuChevronLeft, LuChevronRight, LuMenu } from 'react-icons/lu'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useLogout } from '@/api/hooks'
import { ROUTES } from '@/config'
import { GlobalBatchIndicator } from '@/core/components'
import { useUIStore, useUser } from '@/core/lib/stores'
import styles from './shell.module.scss'

const NAV_ITEMS = [
  { path: ROUTES.UPLOAD, label: 'Upload', icon: GrCloudUpload },
  { path: ROUTES.GALLERY, label: 'Gallery', icon: ImImages },
]

function ShellErrorFallback({ error }: { error: unknown }): React.ReactElement {
  const errorMessage = error instanceof Error ? error.message : String(error)
  return (
    <div className={styles.error}>
      <h2>Something went wrong</h2>
      <pre>{errorMessage}</pre>
    </div>
  )
}

function ShellLoading(): React.ReactElement {
  return <div className={styles.loading}>Loading...</div>
}

function getPageTitle(pathname: string): string {
  const item = NAV_ITEMS.find((i) => i.path === pathname)
  return item?.label ?? 'Vuemantic'
}

export function Shell(): React.ReactElement {
  const location = useLocation()
  const { sidebarOpen, sidebarCollapsed, toggleSidebar, toggleSidebarCollapsed } =
    useUIStore()
  const logout = useLogout()
  const user = useUser()

  const pageTitle = getPageTitle(location.pathname)
  const avatarLetter = user?.email?.[0]?.toUpperCase() ?? 'U'

  return (
    <div className={styles.shell}>
      <aside
        className={`${styles.sidebar} ${sidebarOpen ? styles.open : ''} ${sidebarCollapsed ? styles.collapsed : ''}`}
      >
        <div className={styles.sidebarHeader}>
          <span className={styles.logo}>VueMantic</span>
          <button
            type="button"
            className={styles.collapseBtn}
            onClick={toggleSidebarCollapsed}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? <LuChevronRight /> : <LuChevronLeft />}
          </button>
        </div>

        <nav className={styles.nav}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
              onClick={() => sidebarOpen && toggleSidebar()}
            >
              <item.icon className={styles.navIcon} />
              <span className={styles.navLabel}>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <button
            type="button"
            className={styles.logoutBtn}
            onClick={() => logout()}
          >
            <GiExitDoor className={styles.logoutIcon} />
            <span className={styles.logoutText}>Logout</span>
          </button>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          type="button"
          className={styles.overlay}
          onClick={toggleSidebar}
          onKeyDown={(e) => e.key === 'Escape' && toggleSidebar()}
          aria-label="Close sidebar"
        />
      )}

      <div
        className={`${styles.main} ${sidebarCollapsed ? styles.collapsed : ''}`}
      >
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <button
              type="button"
              className={styles.menuBtn}
              onClick={toggleSidebar}
              aria-label="Toggle menu"
            >
              <LuMenu />
            </button>
            <h1 className={styles.pageTitle}>{pageTitle}</h1>
          </div>

          <div className={styles.headerRight}>
            <GlobalBatchIndicator />
            <div className={styles.avatar}>{avatarLetter}</div>
          </div>
        </header>

        <main className={styles.content}>
          <ErrorBoundary FallbackComponent={ShellErrorFallback}>
            <Suspense fallback={<ShellLoading />}>
              <Outlet />
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
