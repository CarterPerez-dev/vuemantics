// ===================
// © AngelaMos | 2026
// BatchProgressIndicator.tsx
// ===================

import { LuCheck, LuRefreshCw, LuX } from 'react-icons/lu'
import styles from './batch-progress-indicator.module.scss'

interface BatchProgress {
  status: string
  total: number
  processed: number
  successful: number
  failed: number
  progressPercentage: number
}

interface FileProgressState {
  uploadId: string
  fileName: string
  fileSize: number
  progress: number
  status: 'processing' | 'completed' | 'failed'
}

interface BatchProgressIndicatorProps {
  batchProgress: Record<string, BatchProgress>
  currentFile: FileProgressState | null
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / k ** i).toFixed(1)} ${sizes[i]}`
}

export function BatchProgressIndicator({
  batchProgress,
  currentFile,
}: BatchProgressIndicatorProps): React.ReactElement | null {
  const batches = Object.entries(batchProgress)

  if (batches.length === 0) return null

  return (
    <div className={styles.container}>
      {batches.map(([batchId, progress]) => (
        <div key={batchId} className={styles.batch}>
          {/* Batch Header */}
          <div className={styles.header}>
            <div className={styles.title}>
              {progress.status === 'processing' && (
                <>
                  <LuRefreshCw className={styles.spinnerIcon} />
                  <span>
                    Processing {progress.processed}/{progress.total} files
                  </span>
                </>
              )}
              {progress.status === 'completed' && (
                <>
                  <LuCheck className={styles.successIcon} />
                  <span>Batch completed!</span>
                </>
              )}
              {progress.status === 'failed' && (
                <>
                  <LuX className={styles.errorIcon} />
                  <span>Batch failed</span>
                </>
              )}
            </div>
          </div>

          {/* Thick Batch Progress Bar */}
          <div className={styles.progressBarThick}>
            <div
              className={styles.progressFillThick}
              style={{ width: `${progress.progressPercentage}%` }}
            />
          </div>
          <div className={styles.progressLabel}>
            {progress.progressPercentage}%
          </div>

          {/* Batch Stats */}
          {(progress.successful > 0 || progress.failed > 0) && (
            <div className={styles.stats}>
              <span className={styles.success}>
                {progress.successful} successful
              </span>
              {progress.failed > 0 && (
                <>
                  <span className={styles.separator}>|</span>
                  <span className={styles.failed}>{progress.failed} failed</span>
                </>
              )}
            </div>
          )}

          {/* Current File Progress (Thin Bar) */}
          {currentFile && progress.status === 'processing' && (
            <div className={styles.fileProgress}>
              <div className={styles.fileInfo}>
                <span className={styles.fileLabel}>Currently processing:</span>
                <span className={styles.fileName}>
                  {progress.processed}/{progress.total}: {currentFile.fileName} (
                  {formatBytes(currentFile.fileSize)})
                </span>
              </div>
              <div className={styles.progressBarThin}>
                <div
                  className={styles.progressFillThin}
                  style={{ width: `${currentFile.progress}%` }}
                />
              </div>
              <div className={styles.progressLabel}>{currentFile.progress}%</div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
