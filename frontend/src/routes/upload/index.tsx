// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { useEffect, useRef, useState } from 'react'
import { GiCloudUpload } from 'react-icons/gi'
import { LuRefreshCw, LuX } from 'react-icons/lu'
import { TfiFaceSad } from 'react-icons/tfi'
import { toast } from 'sonner'
import {
  useClientConfig,
  useCreateUpload,
  useRegenerateDescription,
  useUploads,
} from '@/api/hooks'
import { useUploadUIStore } from '@/core/lib/stores'
import { useSocket, useUploadProgress } from '@/core/socket'
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [videoPoster, setVideoPoster] = useState<string | null>(null)
  const [thumbnailFailed, setThumbnailFailed] = useState(false)
  const hasShownPendingToast = useRef(false)

  const {
    pendingFile,
    setPendingFile,
    clearPendingFile,
    setDragActive,
    dragActive,
  } = useUploadUIStore()

  const { data: clientConfig } = useClientConfig()
  const maxFileSizeBytes = (clientConfig?.max_upload_size_mb ?? 100) * 1024 * 1024

  useEffect(() => {
    if (pendingFile && !selectedFile && !hasShownPendingToast.current) {
      hasShownPendingToast.current = true
      toast.info(
        `You had a pending upload: ${pendingFile.name}. Please re-select the file.`
      )
      clearPendingFile()
    }
  }, [pendingFile, selectedFile, clearPendingFile])

  const createUpload = useCreateUpload()
  const regenerateDescription = useRegenerateDescription()
  const { data: recentUploads, refetch: refetchUploads } = useUploads({
    page: 1,
    page_size: 6,
    sort_by: 'created_at',
    sort_order: 'desc',
    show_hidden: false,
  })

  const {
    uploadProgress,
    handleProgress,
    handleCompleted,
    handleFailed,
    setProgress,
  } = useUploadProgress()

  const { isConnected, subscribeToUpload } = useSocket({
    enabled: true,
    onProgress: handleProgress,
    onCompleted: async (data) => {
      toast.success('Upload processed successfully!')
      await handleCompleted(data, async () => {
        await refetchUploads()
      })
    },
    onFailed: (data) => {
      toast.error(`Processing failed: ${data.error_message}`)
      handleFailed(data, refetchUploads)
    },
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
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
        setPendingFile({ name: file.name, size: file.size, type: file.type })
        if (file.type.startsWith('video/')) {
          generateVideoThumbnail(url)
        }
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files?.[0]) {
      const file = e.target.files[0]
      if (validateFile(file)) {
        setSelectedFile(file)
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
        setPendingFile({ name: file.name, size: file.size, type: file.type })
        if (file.type.startsWith('video/')) {
          generateVideoThumbnail(url)
        }
      }
    }
  }

  const handleUpload = (): void => {
    if (!selectedFile) return

    createUpload.mutate(selectedFile, {
      onSuccess: (response) => {
        toast.success('File uploaded! Processing...')
        subscribeToUpload(response.id)
        setSelectedFile(null)
        clearPendingFile()
        if (previewUrl) {
          URL.revokeObjectURL(previewUrl)
          setPreviewUrl(null)
        }
        setVideoPoster(null)
        setThumbnailFailed(false)
      },
    })
  }

  const handleCancel = (): void => {
    setSelectedFile(null)
    clearPendingFile()
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
    }
    setVideoPoster(null)
    setThumbnailFailed(false)
  }

  const handleRegenerate = (uploadId: string): void => {
    setProgress(uploadId, {
      percent: 0,
      stage: 'regenerating',
      message: 'Regenerating description...',
    })
    regenerateDescription.mutate(uploadId, {
      onSuccess: () => {
        subscribeToUpload(uploadId)
      },
    })
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const generateVideoThumbnail = (videoUrl: string): void => {
    const video = document.createElement('video')
    video.src = videoUrl
    video.muted = true
    video.playsInline = true
    video.preload = 'metadata'

    const captureFrame = (): void => {
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      if (ctx && canvas.width > 0 && canvas.height > 0) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        const thumbnailUrl = canvas.toDataURL('image/jpeg', 0.8)
        setVideoPoster(thumbnailUrl)
        setThumbnailFailed(false)
      } else {
        setThumbnailFailed(true)
      }
    }

    video.addEventListener('loadedmetadata', () => {
      video.currentTime = Math.min(0.5, video.duration / 10)
    })

    video.addEventListener('seeked', captureFrame, { once: true })

    video.addEventListener('error', () => {
      setThumbnailFailed(true)
    })

    setTimeout(() => {
      if (!videoPoster) {
        setThumbnailFailed(true)
      }
    }, 3000)

    video.load()
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
                    ) : thumbnailFailed ? (
                      <div className={styles.hevcWarning}>
                        <TfiFaceSad className={styles.hevcIcon} />
                        <p className={styles.hevcText}>
                          Video codec (likely HEVC) cannot be previewed in browser
                        </p>
                        <p className={styles.hevcSubtext}>womp womp</p>
                      </div>
                    ) : (
                      <video
                        src={previewUrl}
                        className={styles.previewVideo}
                        controls
                        poster={videoPoster || undefined}
                      />
                    )}
                  </div>
                )}
                <div className={styles.fileInfo}>
                  <GiCloudUpload className={styles.fileIcon} />
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
                <GiCloudUpload className={styles.icon} />
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
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Recent Uploads</h2>
              <div className={styles.wsStatus}>
                <span
                  className={`${styles.indicator} ${isConnected ? styles.connected : ''}`}
                />
                {isConnected ? 'Live' : 'Offline'}
              </div>
            </div>
            <div className={styles.grid}>
              {recentUploads.items.map((upload) => {
                const progress = uploadProgress[upload.id]
                return (
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
                          <GiCloudUpload />
                        </div>
                      )}
                    </div>
                    <div className={styles.cardContent}>
                      <span className={styles.cardTitle}>{upload.filename}</span>
                      {progress ? (
                        <div className={styles.progress}>
                          <div className={styles.progressBar}>
                            <div
                              className={styles.progressFill}
                              style={{ width: `${progress.percent}%` }}
                            />
                          </div>
                          <span className={styles.progressText}>
                            {progress.percent}% - {progress.message}
                          </span>
                        </div>
                      ) : (
                        <div className={styles.cardFooter}>
                          <span
                            className={`${styles.cardStatus} ${
                              upload.processing_status === 'completed'
                                ? styles.completed
                                : ''
                            }`}
                          >
                            {upload.processing_status}
                          </span>
                          {upload.description_audit_score !== null && (
                            <span
                              className={styles.qualityScore}
                              style={{
                                color:
                                  upload.description_audit_score >= 90
                                    ? 'rgb(34, 197, 94)'
                                    : upload.description_audit_score >= 70
                                      ? 'rgb(234, 179, 8)'
                                      : 'rgb(239, 68, 68)',
                              }}
                            >
                              {upload.description_audit_score}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    {upload.processing_status === 'completed' && (
                      <button
                        type="button"
                        className={styles.regenerateBtn}
                        onClick={() => handleRegenerate(upload.id)}
                        disabled={regenerateDescription.isPending}
                        title="Regenerate description"
                      >
                        <LuRefreshCw />
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

Component.displayName = 'Upload'
