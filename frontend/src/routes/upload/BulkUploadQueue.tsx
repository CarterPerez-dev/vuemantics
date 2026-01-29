// ===================
// © AngelaMos | 2026
// BulkUploadQueue.tsx
// ===================

import { CiCircleAlert } from 'react-icons/ci'
import { LuCheck, LuTrash2, LuUpload, LuX } from 'react-icons/lu'
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

export function BulkUploadQueue({
  files,
  onRemoveFile,
  onClearAll,
  onUploadAll,
  isUploading,
  totalSize,
  maxSize,
}: BulkUploadQueueProps): React.ReactElement {
  const validFiles = files.filter((f) => f.status === 'valid')
  const invalidFiles = files.filter((f) => f.status !== 'valid')

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getStatusIcon = (status: QueuedFile['status']): React.ReactElement => {
    switch (status) {
      case 'valid':
        return <LuCheck className={styles.statusIconValid} />
      case 'too-large':
      case 'unsupported':
      case 'duplicate':
        return <CiCircleAlert className={styles.statusIconError} />
    }
  }

  const getStatusLabel = (
    status: QueuedFile['status'],
    error?: string
  ): string => {
    if (error) return error
    switch (status) {
      case 'valid':
        return 'Ready'
      case 'too-large':
        return 'Too large'
      case 'unsupported':
        return 'Unsupported'
      case 'duplicate':
        return 'Duplicate'
    }
  }

  if (files.length === 0) {
    return <div />
  }

  return (
    <div className={styles.queue}>
      <div className={styles.queueHeader}>
        <div className={styles.queueTitle}>
          <span className={styles.queueTitleText}>
            Upload Queue ({files.length} file{files.length !== 1 ? 's' : ''})
          </span>
          <span className={styles.queueSubtitle}>
            Total: {formatFileSize(totalSize)}
            {totalSize > maxSize && (
              <span className={styles.sizeWarning}> (Exceeds limit!)</span>
            )}
          </span>
        </div>
        <div className={styles.queueActions}>
          <button
            type="button"
            className={styles.clearAllBtn}
            onClick={onClearAll}
            disabled={isUploading}
          >
            <LuTrash2 />
            Clear All
          </button>
          <button
            type="button"
            className={styles.uploadAllBtn}
            onClick={onUploadAll}
            disabled={isUploading || validFiles.length === 0}
          >
            <LuUpload />
            Upload {validFiles.length > 0 ? `(${validFiles.length})` : 'All'}
          </button>
        </div>
      </div>

      <div className={styles.fileList}>
        {files.map((queuedFile) => (
          <div
            key={queuedFile.id}
            className={`${styles.fileItem} ${
              queuedFile.status !== 'valid' ? styles.fileItemInvalid : ''
            }`}
          >
            <div className={styles.filePreview}>
              {queuedFile.preview ? (
                <img
                  src={queuedFile.preview}
                  alt={queuedFile.file.name}
                  className={styles.previewImage}
                />
              ) : (
                <div className={styles.previewPlaceholder}>
                  {queuedFile.file.type.startsWith('video/') ? '🎥' : '📄'}
                </div>
              )}
            </div>
            <div className={styles.fileInfo}>
              <span className={styles.fileName}>{queuedFile.file.name}</span>
              <span className={styles.fileSize}>
                {formatFileSize(queuedFile.file.size)}
              </span>
            </div>
            <div className={styles.fileStatus}>
              {getStatusIcon(queuedFile.status)}
              <span
                className={`${styles.statusLabel} ${
                  queuedFile.status !== 'valid' ? styles.statusLabelError : ''
                }`}
              >
                {getStatusLabel(queuedFile.status, queuedFile.error)}
              </span>
            </div>
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
          <CiCircleAlert className={styles.warningIcon} />
          <span className={styles.warningText}>
            {invalidFiles.length} file{invalidFiles.length !== 1 ? 's' : ''}{' '}
            cannot be uploaded
          </span>
        </div>
      )}
    </div>
  )
}
