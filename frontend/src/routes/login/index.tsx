// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { useState } from 'react'
import { LuEye, LuEyeOff } from 'react-icons/lu'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useLogin } from '@/api/hooks'
import { loginRequestSchema } from '@/api/types'
import { ROUTES } from '@/config'
import { useAuthFormStore } from '@/core/lib/stores'
import styles from './login.module.scss'

export function Component(): React.ReactElement {
  const navigate = useNavigate()
  const login = useLogin()

  const { loginEmail, setLoginEmail, clearLoginForm } = useAuthFormStore()
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault()

    const result = loginRequestSchema.safeParse({
      username: loginEmail,
      password,
    })

    if (!result.success) {
      toast.error(result.error.issues[0].message)
      return
    }

    login.mutate(result.data, {
      onSuccess: () => {
        clearLoginForm()
        navigate(ROUTES.UPLOAD)
      },
    })
  }

  return (
    <div className={styles.page}>
      <header className={styles.strip}>
        <div className={styles.stripLeft}>
          <span>&gt;&gt; ANGELAMOS</span>
        </div>
        <div className={styles.stripRight}>
          <span>© 2026</span>
        </div>
      </header>

      <main className={styles.field}>
        <div className={styles.document}>
          <div className={styles.accentBar} />
          <div className={styles.docHeader}>
            <span>IDENTITY VERIFICATION</span>
            <span>AUTH—01</span>
          </div>

          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={styles.formField}>
              <label className={styles.label} htmlFor="email">
                IDENTIFICATION
              </label>
              <input
                id="email"
                type="email"
                className={styles.input}
                placeholder="operator@domain.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                autoComplete="email"
              />
            </div>

            <div className={styles.formField}>
              <label className={styles.label} htmlFor="password">
                CREDENTIAL
              </label>
              <div className={styles.inputWrapper}>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  className={styles.input}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className={styles.toggle}
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <LuEyeOff /> : <LuEye />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className={styles.submit}
              disabled={login.isPending}
            >
              {login.isPending ? 'AUTHENTICATING...' : 'AUTHENTICATE'}
            </button>
          </form>

          <div className={styles.docFooter}>
            <span className={styles.footerText}>
              No clearance?{'  '}
              <Link to={ROUTES.REGISTER} className={styles.link}>
                REQUEST ACCESS →
              </Link>
            </span>
          </div>
        </div>
      </main>

      <footer className={styles.bottom}>
        <Link to={ROUTES.HOME} className={styles.returnLink}>
          ← RETURN
        </Link>
      </footer>
    </div>
  )
}

Component.displayName = 'Login'
