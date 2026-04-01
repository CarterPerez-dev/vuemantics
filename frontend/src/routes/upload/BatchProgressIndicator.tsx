// ===================
// © AngelaMos | 2026
// BatchProgressIndicator.tsx
// ===================

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
          <div className={styles.batchHeader}>
            <span className={styles.batchLabel}>
              {progress.status === 'processing' && 'PROCESSING'}
              {progress.status === 'completed' && 'COMPLETE'}
              {progress.status === 'failed' && 'FAILED'}
            </span>
            <span className={styles.batchCount}>
              {progress.processed}/{progress.total}
            </span>
          </div>

          <div className={styles.progressBar}>
            <div
              className={`${styles.progressFill} ${progress.status === 'failed' ? styles.progressError : ''}`}
              style={{ width: `${progress.progressPercentage}%` }}
            />
          </div>

          <div className={styles.batchStats}>
            <span>{progress.progressPercentage}%</span>
            {progress.successful > 0 && (
              <span className={styles.statSuccess}>
                {progress.successful} OK
              </span>
            )}
            {progress.failed > 0 && (
              <span className={styles.statFailed}>
                {progress.failed} FAILED
              </span>
            )}
          </div>

          {currentFile && progress.status === 'processing' && (
            <div className={styles.currentFile}>
              <div className={styles.fileRow}>
                <span className={styles.fileLabel}>CURRENT</span>
                <span className={styles.fileName}>
                  {currentFile.fileName} ({formatBytes(currentFile.fileSize)})
                </span>
              </div>
              <div className={styles.progressBarThin}>
                <div
                  className={styles.progressFillThin}
                  style={{ width: `${currentFile.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
