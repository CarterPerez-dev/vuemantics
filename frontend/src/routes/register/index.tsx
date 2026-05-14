// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { useState } from 'react'
import { LuEye, LuEyeOff } from 'react-icons/lu'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { z } from 'zod'
import { useRegister } from '@/api/hooks'
import { registerRequestSchema } from '@/api/types'
import { PASSWORD_CONSTRAINTS, ROUTES } from '@/config'
import { useAuthFormStore } from '@/core/lib/stores'
import styles from './register.module.scss'

const registerFormSchema = registerRequestSchema
  .extend({
    confirmPassword: z
      .string()
      .min(
        PASSWORD_CONSTRAINTS.MIN_LENGTH,
        `Password must be at least ${PASSWORD_CONSTRAINTS.MIN_LENGTH} characters`
      )
      .max(PASSWORD_CONSTRAINTS.MAX_LENGTH),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

export function Component(): React.ReactElement {
  const navigate = useNavigate()
  const register = useRegister()

  const { registerEmail, setRegisterEmail, clearRegisterForm } =
    useAuthFormStore()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault()

    const result = registerFormSchema.safeParse({
      email: registerEmail,
      password,
      confirmPassword,
    })

    if (!result.success) {
      toast.error(result.error.issues[0].message)
      return
    }

    register.mutate(
      { email: result.data.email, password: result.data.password },
      {
        onSuccess: () => {
          clearRegisterForm()
          toast.success('Credentials created successfully')
          navigate(ROUTES.LOGIN)
        },
      }
    )
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
            <span>NEW REGISTRATION</span>
            <span>REG—01</span>
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
                value={registerEmail}
                onChange={(e) => setRegisterEmail(e.target.value)}
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
                  autoComplete="new-password"
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

            <div className={styles.formField}>
              <label className={styles.label} htmlFor="confirmPassword">
                CONFIRM CREDENTIAL
              </label>
              <div className={styles.inputWrapper}>
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  className={styles.input}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className={styles.toggle}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  aria-label={
                    showConfirmPassword ? 'Hide password' : 'Show password'
                  }
                >
                  {showConfirmPassword ? <LuEyeOff /> : <LuEye />}
                </button>
              </div>
            </div>

            <div className={styles.constraint}>
              {PASSWORD_CONSTRAINTS.MIN_LENGTH}–{PASSWORD_CONSTRAINTS.MAX_LENGTH}{' '}
              CHARACTERS REQUIRED
            </div>

            <button
              type="submit"
              className={styles.submit}
              disabled={register.isPending}
            >
              {register.isPending ? 'CREATING...' : 'CREATE CREDENTIALS'}
            </button>
          </form>

          <div className={styles.docFooter}>
            <span className={styles.footerText}>
              Already registered?{' '}
              <Link to={ROUTES.LOGIN} className={styles.link}>
                AUTHENTICATE →
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

Component.displayName = 'Register'
