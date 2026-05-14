// ===================
// © AngelaMos | 2026
// shell.tsx
// ===================

import { Suspense, useState } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import { LuMenu, LuX } from 'react-icons/lu'
import { NavLink, Outlet } from 'react-router-dom'
import { useLogout } from '@/api/hooks'
import { ROUTES } from '@/config'
import { GlobalBatchIndicator } from '@/core/components'
import { useUser } from '@/core/lib/stores'
import styles from './shell.module.scss'

const NAV_ITEMS = [
  { path: ROUTES.UPLOAD, label: 'UPLOAD' },
  { path: ROUTES.GALLERY, label: 'GALLERY' },
  { path: ROUTES.SETTINGS, label: 'CONFIG' },
]

function ShellErrorFallback({ error }: { error: unknown }): React.ReactElement {
  const errorMessage = error instanceof Error ? error.message : String(error)
  return (
    <div className={styles.error}>
      <div className={styles.errorHeader}>
        <span>SYSTEM ERROR</span>
        <span>ERR—01</span>
      </div>
      <pre className={styles.errorPre}>{errorMessage}</pre>
    </div>
  )
}

function ShellLoading(): React.ReactElement {
  return <div className={styles.loading}>LOADING...</div>
}

export function Shell(): React.ReactElement {
  const logout = useLogout()
  const user = useUser()
  const avatarLetter = user?.email?.[0]?.toUpperCase() ?? 'U'
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  return (
    <div className={styles.shell}>
      <div className={styles.grain} aria-hidden="true">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="100%"
          height="100%"
          preserveAspectRatio="none"
        >
          <filter id="grain-shell">
            <feTurbulence
              type="turbulence"
              baseFrequency="1.15"
              numOctaves="4"
              seed="2"
              stitchTiles="stitch"
            >
              <animate
                attributeName="seed"
                from="0"
                to="100"
                dur="2.67s"
                repeatCount="indefinite"
              />
            </feTurbulence>
          </filter>
          <rect width="100%" height="100%" filter="url(#grain-shell)" />
        </svg>
      </div>

      <header className={styles.commandBar}>
        <div className={styles.brand}>
          <span className={styles.brandName}>VM—01</span>
          <span className={styles.brandReg}>®</span>
        </div>

        <button
          type="button"
          className={styles.mobileToggle}
          onClick={() => setMobileNavOpen(!mobileNavOpen)}
          aria-label="Toggle navigation"
        >
          {mobileNavOpen ? <LuX /> : <LuMenu />}
        </button>

        <nav className={`${styles.nav} ${mobileNavOpen ? styles.navOpen : ''}`}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
              onClick={() => setMobileNavOpen(false)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className={styles.controls}>
          <GlobalBatchIndicator />
          <div className={styles.avatar}>{avatarLetter}</div>
          <button
            type="button"
            className={styles.logoutBtn}
            onClick={() => logout()}
          >
            OUT
          </button>
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
  )
}
