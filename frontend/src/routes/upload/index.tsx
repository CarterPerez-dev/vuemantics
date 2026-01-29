// ===================
// © AngelaMos | 2026
// index.tsx - WITH BULK UPLOAD SUPPORT
// ===================

import { GiCloudUpload } from 'react-icons/gi'
import { LuFolderUp } from 'react-icons/lu'
import { toast } from 'sonner'
import { useClientConfig, useCreateBulkUpload } from '@/api/hooks'
import { useGlobalBatchProgress } from '@/core/lib/stores'
import {
  type QueuedFile,
  useBulkUploadUIStore,
} from '@/core/lib/stores/bulk-upload.ui.store'
import { useFileProgress, useSocket } from '@/core/socket'
import { BatchProgressIndicator } from './BatchProgressIndicator'
import { BulkUploadQueue } from './BulkUploadQueue'
import styles from './upload.module.scss'

const ACCEPTED_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/webp': ['.webp'],
  'image/heic': ['.heic'],
  'image/heif': ['.heif'],
  // VIDEO UPLOADS DISABLED (uncomment below to re-enable)
  // 'video/mp4': ['.mp4'],
  // 'video/webm': ['.webm'],
  // 'video/quicktime': ['.mov'],
}

export function Component(): React.ReactElement {
  const {
    fileQueue,
    addFiles,
    removeFile,
    clearQueue,
    setDragActive,
    dragActive,
    setCurrentBatchId,
  } = useBulkUploadUIStore()

  const { data: clientConfig } = useClientConfig()
  const maxFileSizeBytes = (clientConfig?.max_upload_size_mb ?? 100) * 1024 * 1024

  const createBulkUpload = useCreateBulkUpload()

  const { batchProgress, setBatchProgress, setCurrentFile } =
    useGlobalBatchProgress()
  const { currentFile, handleFileProgress } = useFileProgress()

  useSocket({
    enabled: true,
    onBatchProgress: (data) => {
      setBatchProgress(data.payload.batch_id, {
        status: data.payload.status,
        total: data.payload.total,
        processed: data.payload.processed,
        successful: data.payload.successful,
        failed: data.payload.failed,
        progressPercentage: data.payload.progress_percentage,
      })
    },
    onFileProgress: (data) => {
      handleFileProgress(data)
      // Also update global store for header indicator
      if (data.payload.status === 'processing') {
        setCurrentFile({
          uploadId: data.payload.upload_id,
          fileName: data.payload.file_name,
          fileSize: data.payload.file_size,
          progress: data.payload.progress_percentage,
          status: data.payload.status,
        })
      } else {
        setCurrentFile(null)
      }
    },
  })

  const validateFile = (file: File): { valid: boolean; error?: string } => {
    const maxSizeMB = clientConfig?.max_upload_size_mb ?? 100
    if (file.size > maxFileSizeBytes) {
      return { valid: false, error: `Too large (max ${maxSizeMB}MB)` }
    }

    if (!Object.keys(ACCEPTED_TYPES).includes(file.type)) {
      return { valid: false, error: 'Unsupported file type' }
    }

    return { valid: true }
  }

  const handleDrag = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const processFiles = (files: FileList | File[]): void => {
    const fileArray = Array.from(files)
    const newQueuedFiles: QueuedFile[] = []

    // Check for duplicates in existing queue
    const existingNames = new Set(fileQueue.map((f) => f.file.name))

    fileArray.forEach((file) => {
      const validation = validateFile(file)
      const isDuplicate = existingNames.has(file.name)

      const queuedFile: QueuedFile = {
        id: `${Date.now()}-${Math.random()}`,
        file,
        status: isDuplicate
          ? 'duplicate'
          : validation.valid
            ? 'valid'
            : validation.error?.includes('large')
              ? 'too-large'
              : 'unsupported',
        error: isDuplicate ? 'Already in queue' : validation.error,
      }

      // Generate preview for images
      if (file.type.startsWith('image/') && validation.valid) {
        queuedFile.preview = URL.createObjectURL(file)
      }

      newQueuedFiles.push(queuedFile)
    })

    addFiles(newQueuedFiles)
  }

  const handleDrop = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files) {
      processFiles(e.dataTransfer.files)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files) {
      processFiles(e.target.files)
    }
    // Reset input so same files can be selected again
    e.target.value = ''
  }

  const handleUploadAll = (): void => {
    const validFiles = fileQueue
      .filter((f) => f.status === 'valid')
      .map((f) => f.file)

    if (validFiles.length === 0) {
      toast.error('No valid files to upload')
      return
    }

    createBulkUpload.mutate(validFiles, {
      onSuccess: (result) => {
        setCurrentBatchId(result.batch_id)
        clearQueue()
        toast.success(`Batch upload started: ${result.queued} files queued`)
      },
    })
  }

  const totalQueueSize = fileQueue.reduce((sum, f) => sum + f.file.size, 0)

  return (
    <div className={styles.page}>
      <BatchProgressIndicator
        batchProgress={batchProgress}
        currentFile={currentFile}
      />
      <div className={styles.container}>
        <div className={styles.uploadSection}>
          <div
            className={`${styles.dropzone} ${dragActive ? styles.active : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            role="button"
            tabIndex={0}
          >
            <GiCloudUpload className={styles.icon} />
            <p className={styles.text}>Drag and drop files or folders</p>
            <p className={styles.subtext}>Upload 1-1000 files at once</p>
            <div className={styles.bulkInputs}>
              <input
                type="file"
                className={styles.fileInput}
                onChange={handleFileSelect}
                accept={Object.values(ACCEPTED_TYPES).flat().join(',')}
                multiple
              />
              <label className={styles.folderBtn}>
                <LuFolderUp />
                <span>Upload Folder</span>
                <input
                  type="file"
                  className={styles.fileInputHidden}
                  onChange={handleFileSelect}
                  // @ts-expect-error - webkitdirectory is not in types
                  webkitdirectory=""
                  directory=""
                />
              </label>
            </div>
          </div>

          <BulkUploadQueue
            files={fileQueue}
            onRemoveFile={removeFile}
            onClearAll={clearQueue}
            onUploadAll={handleUploadAll}
            isUploading={createBulkUpload.isPending}
            totalSize={totalQueueSize}
            maxSize={maxFileSizeBytes * 1000} // Generous limit for bulk
          />

          <div className={styles.info}>
            <p className={styles.infoText}>
              Supported formats: Images (JPG, PNG, WebP, HEIC) and Videos (MP4,
              WebM, MOV)
            </p>
            <p className={styles.infoText}>
              Maximum per file:{' '}
              <span className={styles.highlight}>
                {clientConfig?.max_upload_size_mb ?? 100}MB
              </span>
            </p>
            <p className={styles.infoText}>
              Maximum batch: <span className={styles.highlight}>1000 files</span>{' '}
              or <span className={styles.highlight}>10GB total</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

Component.displayName = 'Upload'
