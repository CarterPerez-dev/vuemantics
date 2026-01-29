// ===================
// © AngelaMos | 2026
// GlobalBatchIndicator.tsx
// ===================

import { LuRefreshCw } from 'react-icons/lu'
import { useNavigate } from 'react-router-dom'
import { ROUTES } from '@/config'
import { useGlobalBatchProgress } from '@/core/lib/stores'
import styles from './global-batch-indicator.module.scss'

export function GlobalBatchIndicator(): React.ReactElement | null {
  const navigate = useNavigate()
  const { hasActiveProcessing, getActiveCount } = useGlobalBatchProgress()

  if (!hasActiveProcessing()) {
    return null
  }

  const { processed, total } = getActiveCount()

  return (
    <button
      type="button"
      className={styles.indicator}
      onClick={() => navigate(ROUTES.UPLOAD)}
      title="View upload progress"
    >
      <LuRefreshCw className={styles.spinner} />
      <span className={styles.text}>
        {processed}/{total} Processing
      </span>
    </button>
  )
}
