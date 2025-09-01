import { useState, useCallback } from 'react'
import { useUpload } from '@/hooks/useUpload'
import { useNavigate } from 'react-router-dom'
import { 
  CloudArrowUpIcon,
  PhotoIcon,
  VideoCameraIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import type { UploadProgress } from '@/types'
import './FileUpload.css'

interface FileWithPreview extends File {
  preview?: string
  id: string
}

interface UploadResult {
  file: FileWithPreview
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress?: number
  error?: string
}

function FileUpload() {
  const navigate = useNavigate()
  const { uploadFile, uploadMultipleFiles, uploadProgress } = useUpload()
  const [isDragging, setIsDragging] = useState(false)
  const [uploadResults, setUploadResults] = useState<UploadResult[]>([])
  const [isUploading, setIsUploading] = useState(false)

  // Handle drag events
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    if (e.currentTarget === e.target) {
      setIsDragging(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }, [])

  // Handle file input change
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    handleFiles(files)
  }

  // Process selected files
  const handleFiles = async (files: File[]) => {
    if (files.length === 0) return

    // Create file previews and results
    const filesWithPreviews = files.map(file => {
      const fileWithPreview = file as FileWithPreview
      fileWithPreview.id = `${Date.now()}-${Math.random()}`
      
      // Create preview for images
      if (file.type.startsWith('image/')) {
        fileWithPreview.preview = URL.createObjectURL(file)
      }
      
      return fileWithPreview
    })

    // Initialize upload results
    const initialResults = filesWithPreviews.map(file => ({
      file,
      status: 'pending' as const,
      progress: 0,
    }))
    
    setUploadResults(initialResults)
    setIsUploading(true)

    // Upload files
    try {
      const results = await uploadMultipleFiles(files)
      
      // Update results with success/error status
      setUploadResults(prev => prev.map((result, index) => {
        const success = results.successful.find(
          upload => upload.filename === result.file.name
        )
        const failed = results.failed.find(
          fail => fail.filename === result.file.name
        )
        
        if (success) {
          return { ...result, status: 'success' }
        } else if (failed) {
          return { ...result, status: 'error', error: failed.error }
        }
        return result
      }))
    } catch (error) {
      // Mark all as error if batch upload fails
      setUploadResults(prev => prev.map(result => ({
        ...result,
        status: 'error',
        error: 'Upload failed'
      })))
    } finally {
      setIsUploading(false)
    }
  }

  // Clear completed uploads
  const clearCompleted = () => {
    setUploadResults(prev => prev.filter(
      result => result.status === 'uploading' || result.status === 'pending'
    ))
  }

  // Get icon for file type
  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <PhotoIcon className="w-8 h-8" />
    } else if (file.type.startsWith('video/')) {
      return <VideoCameraIcon className="w-8 h-8" />
    }
    return <CloudArrowUpIcon className="w-8 h-8" />
  }

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1048576).toFixed(1) + ' MB'
  }

  const hasResults = uploadResults.length > 0
  const allCompleted = uploadResults.every(r => r.status === 'success' || r.status === 'error')
  const successCount = uploadResults.filter(r => r.status === 'success').length

  return (
    <div className="file-upload-container">
      {/* Drop Zone */}
      <div
        className={`drop-zone ${isDragging ? 'dragging' : ''} ${hasResults ? 'compact' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-input"
          className="hidden"
          multiple
          accept="image/*,video/*"
          onChange={handleFileSelect}
          disabled={isUploading}
        />
        
        <label htmlFor="file-input" className="drop-zone-content cursor-pointer">
          <CloudArrowUpIcon className={`upload-icon ${hasResults ? 'w-12 h-12' : 'w-16 h-16'} text-gray-400 mb-4`} />
          <div className="text-center">
            <p className="text-lg font-medium text-white mb-2">
              {isDragging ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-sm text-gray-400 mb-4">or click to browse</p>
            <div className="file-types flex items-center justify-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <PhotoIcon className="w-4 h-4" />
                Images
              </span>
              <span className="flex items-center gap-1">
                <VideoCameraIcon className="w-4 h-4" />
                Videos
              </span>
              <span>Max 100MB</span>
            </div>
          </div>
        </label>
      </div>

      {/* Upload Results */}
      {hasResults && (
        <div className="upload-results pgv-glass rounded-xl p-4 mt-4">
          <div className="results-header flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              {isUploading ? 'Uploading...' : 'Upload Results'}
            </h3>
            {allCompleted && (
              <button
                className="text-sm text-gray-400 hover:text-white transition-colors duration-200"
                onClick={clearCompleted}
              >
                Clear all
              </button>
            )}
          </div>
          
          <div className="results-list space-y-2">
            {uploadResults.map((result) => (
              <div
                key={result.file.id}
                className="result-item flex items-center gap-3 p-3 rounded-lg bg-black/20"
              >
                {/* File Preview or Icon */}
                <div className="file-preview flex-shrink-0">
                  {result.file.preview ? (
                    <img
                      src={result.file.preview}
                      alt={result.file.name}
                      className="w-12 h-12 rounded object-cover"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded bg-gray-800 flex items-center justify-center">
                      {getFileIcon(result.file)}
                    </div>
                  )}
                </div>
                
                {/* File Info */}
                <div className="file-info flex-grow min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {result.file.name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatFileSize(result.file.size)}
                  </p>
                </div>
                
                {/* Status */}
                <div className="file-status flex-shrink-0">
                  {result.status === 'pending' && (
                    <div className="text-gray-400">
                      <ExclamationTriangleIcon className="w-5 h-5" />
                    </div>
                  )}
                  {result.status === 'uploading' && (
                    <div className="relative w-8 h-8">
                      <ArrowPathIcon className="w-5 h-5 animate-spin text-blue-400" />
                    </div>
                  )}
                  {result.status === 'success' && (
                    <CheckCircleIcon className="w-5 h-5 text-green-400" />
                  )}
                  {result.status === 'error' && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-red-400">{result.error}</span>
                      <XCircleIcon className="w-5 h-5 text-red-400" />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {/* Summary */}
          {allCompleted && successCount > 0 && (
            <div className="results-summary mt-4 pt-4 border-t border-white/10">
              <p className="text-sm text-gray-300">
                Successfully uploaded {successCount} of {uploadResults.length} files
              </p>
              <button
                className="mt-2 text-sm font-medium text-white hover:text-gray-300 transition-colors duration-200"
                onClick={() => navigate('/dashboard')}
              >
                View in gallery →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default FileUpload
