// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { useState } from 'react'
import { LuUpload, LuX } from 'react-icons/lu'
import { toast } from 'sonner'
import { useClientConfig, useCreateUpload, useUploads } from '@/api/hooks'
import styles from './upload.module.scss'

const ACCEPTED_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/webp': ['.webp'],
  'image/heic': ['.heic'],
  'image/heif': ['.heif'],
  'video/mp4': ['.mp4'],
  'video/webm': ['.webm'],
  'video/quicktime': ['.mov'],
}

export function Component(): React.ReactElement {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const { data: clientConfig } = useClientConfig()
  const maxFileSizeBytes = (clientConfig?.max_upload_size_mb ?? 100) * 1024 * 1024

  const createUpload = useCreateUpload()
  const { data: recentUploads } = useUploads({
    page: 1,
    page_size: 6,
    sort_by: 'created_at',
    sort_order: 'desc',
    show_hidden: false,
  })

  const validateFile = (file: File): boolean => {
    const maxSizeMB = clientConfig?.max_upload_size_mb ?? 100
    if (file.size > maxFileSizeBytes) {
      toast.error(`File too large. Max size is ${maxSizeMB}MB`)
      return false
    }

    if (!Object.keys(ACCEPTED_TYPES).includes(file.type)) {
      toast.error('File type not supported')
      return false
    }

    return true
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

  const handleDrop = (e: React.DragEvent): void => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files?.[0]) {
      const file = e.dataTransfer.files[0]
      if (validateFile(file)) {
        setSelectedFile(file)
        setPreviewUrl(URL.createObjectURL(file))
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files?.[0]) {
      const file = e.target.files[0]
      if (validateFile(file)) {
        setSelectedFile(file)
        setPreviewUrl(URL.createObjectURL(file))
      }
    }
  }

  const handleUpload = (): void => {
    if (!selectedFile) return

    createUpload.mutate(selectedFile, {
      onSuccess: () => {
        setSelectedFile(null)
        if (previewUrl) {
          URL.revokeObjectURL(previewUrl)
          setPreviewUrl(null)
        }
      },
    })
  }

  const handleCancel = (): void => {
    setSelectedFile(null)
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.uploadSection}>
          <div
            className={`${styles.dropzone} ${dragActive ? styles.active : ''} ${selectedFile ? styles.hasFile : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            role="button"
            tabIndex={0}
          >
            {selectedFile ? (
              <div className={styles.selectedFile}>
                {previewUrl && (
                  <div className={styles.preview}>
                    {selectedFile.type.startsWith('image/') ? (
                      <img
                        src={previewUrl}
                        alt={selectedFile.name}
                        className={styles.previewImg}
                      />
                    ) : (
                      <video
                        src={previewUrl}
                        className={styles.previewVideo}
                        controls
                      />
                    )}
                  </div>
                )}
                <div className={styles.fileInfo}>
                  <LuUpload className={styles.fileIcon} />
                  <div className={styles.fileDetails}>
                    <span className={styles.fileName}>{selectedFile.name}</span>
                    <span className={styles.fileSize}>
                      {formatFileSize(selectedFile.size)}
                    </span>
                  </div>
                </div>
                <div className={styles.actions}>
                  <button
                    type="button"
                    className={styles.uploadBtn}
                    onClick={handleUpload}
                    disabled={createUpload.isPending}
                  >
                    {createUpload.isPending ? 'Uploading...' : 'Upload'}
                  </button>
                  <button
                    type="button"
                    className={styles.cancelBtn}
                    onClick={handleCancel}
                    disabled={createUpload.isPending}
                  >
                    <LuX />
                  </button>
                </div>
              </div>
            ) : (
              <>
                <LuUpload className={styles.icon} />
                <p className={styles.text}>Drag and drop your files here</p>
                <p className={styles.subtext}>or click to browse</p>
                <input
                  type="file"
                  className={styles.fileInput}
                  onChange={handleFileSelect}
                  accept={Object.values(ACCEPTED_TYPES).flat().join(',')}
                />
              </>
            )}
          </div>

          <div className={styles.info}>
            <p className={styles.infoText}>
              Supported formats: Images (JPG, PNG, WebP, HEIC) and Videos (MP4,
              WebM, MOV)
            </p>
            <p className={styles.infoText}>
              Maximum file size:{' '}
              <span className={styles.highlight}>
                {clientConfig?.max_upload_size_mb ?? 100}MB
              </span>
            </p>
          </div>
        </div>

        {recentUploads && recentUploads.items.length > 0 && (
          <div className={styles.recentSection}>
            <h2 className={styles.sectionTitle}>Recent Uploads</h2>
            <div className={styles.grid}>
              {recentUploads.items.map((upload) => (
                <div key={upload.id} className={styles.card}>
                  <div className={styles.thumbnail}>
                    {upload.thumbnail_path ? (
                      <img
                        src={upload.thumbnail_path}
                        alt={upload.filename}
                        className={styles.thumbnailImg}
                      />
                    ) : (
                      <div className={styles.thumbnailPlaceholder}>
                        <LuUpload />
                      </div>
                    )}
                  </div>
                  <div className={styles.cardContent}>
                    <span className={styles.cardTitle}>{upload.filename}</span>
                    <span className={styles.cardStatus}>
                      {upload.processing_status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

Component.displayName = 'Upload'
