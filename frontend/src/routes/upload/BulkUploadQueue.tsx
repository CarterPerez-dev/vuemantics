// ===================
// © AngelaMos | 2026
// BulkUploadQueue.tsx
// ===================

import { LuX } from 'react-icons/lu'
import type { QueuedFile } from '@/core/lib/stores/bulk-upload.ui.store'
import styles from './bulk-upload-queue.module.scss'

interface BulkUploadQueueProps {
  files: QueuedFile[]
  onRemoveFile: (id: string) => void
  onClearAll: () => void
  onUploadAll: () => void
  isUploading: boolean
  totalSize: number
  maxSize: number
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const getStatusLabel = (
  status: QueuedFile['status'],
  error?: string
): string => {
  if (error) return error
  switch (status) {
    case 'valid':
      return 'READY'
    case 'too-large':
      return 'TOO LARGE'
    case 'unsupported':
      return 'UNSUPPORTED'
    case 'duplicate':
      return 'DUPLICATE'
  }
}

export function BulkUploadQueue({
  files,
  onRemoveFile,
  onClearAll,
  onUploadAll,
  isUploading,
  totalSize,
  maxSize,
}: BulkUploadQueueProps): React.ReactElement | null {
  const validFiles = files.filter((f) => f.status === 'valid')
  const invalidFiles = files.filter((f) => f.status !== 'valid')

  if (files.length === 0) return null

  return (
    <div className={styles.queue}>
      <div className={styles.queueHeader}>
        <div className={styles.queueHeaderLeft}>
          <span className={styles.queueLabel}>INTAKE QUEUE</span>
          <span className={styles.queueMeta}>
            {files.length} FILE{files.length !== 1 ? 'S' : ''} ·{' '}
            {formatFileSize(totalSize)}
            {totalSize > maxSize && (
              <span className={styles.overLimit}> EXCEEDS LIMIT</span>
            )}
          </span>
        </div>
        <div className={styles.queueActions}>
          <button
            type="button"
            className={styles.actionBtn}
            onClick={onClearAll}
            disabled={isUploading}
          >
            CLEAR
          </button>
          <button
            type="button"
            className={styles.uploadBtn}
            onClick={onUploadAll}
            disabled={isUploading || validFiles.length === 0}
          >
            {isUploading
              ? 'UPLOADING...'
              : `UPLOAD${validFiles.length > 0 ? ` (${validFiles.length})` : ''}`}
          </button>
        </div>
      </div>

      <div className={styles.fileList}>
        {files.map((queuedFile) => (
          <div
            key={queuedFile.id}
            className={`${styles.fileItem} ${queuedFile.status !== 'valid' ? styles.fileItemInvalid : ''}`}
          >
            <div className={styles.filePreview}>
              {queuedFile.preview ? (
                <img
                  src={queuedFile.preview}
                  alt={queuedFile.file.name}
                  className={styles.previewImg}
                />
              ) : (
                <span className={styles.previewFallback}>
                  {queuedFile.file.type.startsWith('video/') ? 'VID' : 'FILE'}
                </span>
              )}
            </div>
            <div className={styles.fileInfo}>
              <span className={styles.fileName}>{queuedFile.file.name}</span>
              <span className={styles.fileSize}>
                {formatFileSize(queuedFile.file.size)}
              </span>
            </div>
            <span
              className={`${styles.fileStatus} ${queuedFile.status !== 'valid' ? styles.fileStatusError : ''}`}
            >
              {getStatusLabel(queuedFile.status, queuedFile.error)}
            </span>
            <button
              type="button"
              className={styles.removeBtn}
              onClick={() => onRemoveFile(queuedFile.id)}
              disabled={isUploading}
              aria-label="Remove file"
            >
              <LuX />
            </button>
          </div>
        ))}
      </div>

      {invalidFiles.length > 0 && (
        <div className={styles.queueFooter}>
          {invalidFiles.length} FILE{invalidFiles.length !== 1 ? 'S' : ''}{' '}
          CANNOT BE UPLOADED
        </div>
      )}
    </div>
  )
}
