import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import FileUpload from '@/components/FileUpload/FileUpload'
import { useUpload } from '@/hooks/useUpload'
import { 
  PhotoIcon,
  VideoCameraIcon,
  FolderIcon,
  BoltIcon,
  CpuChipIcon,
  ArrowRightIcon,
  XMarkIcon,
  ScaleIcon
} from '@heroicons/react/24/outline'

function Upload() {
  const navigate = useNavigate()
  const { useUploadsList, getFileUrl } = useUpload()
  const { data: uploads, refetch } = useUploadsList({ page: 1, page_size: 5 })
  const [hiddenUploads, setHiddenUploads] = useState<Set<string>>(() => {
    // Load from localStorage on init
    const saved = localStorage.getItem('hiddenUploads')
    return saved ? new Set(JSON.parse(saved)) : new Set()
  })
  
  // Toast notifications for failed uploads
  const [toasts, setToasts] = useState<Array<{id: string, message: string, type: 'error' | 'success'}>>([])
  const [failedUploads, setFailedUploads] = useState<Set<string>>(() => {
    // Load from localStorage on init
    const saved = localStorage.getItem('failedUploads')
    return saved ? new Set(JSON.parse(saved)) : new Set()
  })

  // Auto-refresh uploads list when there are processing uploads
  useEffect(() => {
    if (!uploads?.items) return

    const processingUploads = uploads.items.filter(upload => 
      ['pending', 'analyzing', 'embedding'].includes(upload.processing_status)
    )

    // Check for newly failed uploads
    const newlyFailed = uploads.items.filter(upload => 
      upload.processing_status === 'failed' && !failedUploads.has(upload.id)
    )

    // Show toast for newly failed uploads
    newlyFailed.forEach(upload => {
      const toastId = `toast-${upload.id}`
      setToasts(prev => [...prev, {
        id: toastId,
        message: `Failed to process "${upload.filename}"`,
        type: 'error'
      }])
      
      // Remove toast after 5 seconds
      setTimeout(() => {
        setToasts(prev => prev.filter(toast => toast.id !== toastId))
      }, 5000)
      
      // Mark as failed and hide after 10 seconds
      setFailedUploads(prev => {
        const newSet = new Set(prev).add(upload.id)
        localStorage.setItem('failedUploads', JSON.stringify([...newSet]))
        return newSet
      })
      setTimeout(() => {
        setHiddenUploads(prev => new Set(prev).add(upload.id))
      }, 10000)
    })

    if (processingUploads.length > 0) {
      const interval = setInterval(() => {
        refetch()
      }, 2000) // Check every 2 seconds

      return () => clearInterval(interval)
    }
  }, [uploads, refetch, failedUploads])

  // Navigate to dashboard after uploads
  const handleUploadsComplete = () => {
    refetch()
    // Optional: Navigate to dashboard after a delay
    setTimeout(() => {
      navigate('/dashboard')
    }, 2000)
  }

  // Hide upload from recent uploads (visual only - doesn't cancel processing)
  const hideUpload = (uploadId: string) => {
    setHiddenUploads(prev => {
      const newSet = new Set(prev).add(uploadId)
      localStorage.setItem('hiddenUploads', JSON.stringify([...newSet]))
      return newSet
    })
  }

  // Clear all hidden uploads
  const clearAllHidden = () => {
    setHiddenUploads(new Set())
    localStorage.removeItem('hiddenUploads')
  }

  // Clear failed uploads tracking (useful for debugging)
  const clearAllFailed = () => {
    setFailedUploads(new Set())
    localStorage.removeItem('failedUploads')
  }

  // Hide all visible uploads
  const hideAllUploads = () => {
    const allUploadIds = visibleUploads.map(upload => upload.id)
    setHiddenUploads(prev => {
      const newSet = new Set([...prev, ...allUploadIds])
      localStorage.setItem('hiddenUploads', JSON.stringify([...newSet]))
      return newSet
    })
  }

  // Filter out hidden uploads
  const visibleUploads = uploads?.items.filter(upload => !hiddenUploads.has(upload.id)) || []

  return (
    <div className="upload-page min-h-screen p-8 pgv-fade-in">
      {/* Toast Notifications */}
      <div className="fixed top-4 right-4 z-[9999] space-y-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`toast-notification px-4 py-3 rounded-lg shadow-lg backdrop-blur-md border transition-all duration-300 transform ${
              toast.type === 'error' 
                ? 'bg-red-500/90 border-red-400 text-white' 
                : 'bg-green-500/90 border-green-400 text-white'
            } animate-slide-in-right`}
          >
            <p className="text-sm font-medium">{toast.message}</p>
          </div>
        ))}
      </div>
      {/* Hero Header with Glass Effect */}
      <div className="upload-header text-center mb-12">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
          Upload Media
        </h1>
        <p className="upload-description text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
          Upload your photos and videos to make them searchable with AI vector semantic search
        </p>
      </div>

      {/* Main Upload Area */}
      <div className="max-w-4xl mx-auto space-y-8">
        {/* File Upload Component with Glass Container */}
        <div className="pgv-glass p-8 rounded-2xl">
          <FileUpload />
        </div>

        {/* Recent Uploads Section with Masonry Layout */}
        {uploads && uploads.items.length > 0 && (
          <div className="recent-uploads pgv-glass p-8 rounded-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-display font-semibold text-white tracking-tight">Recent Uploads</h2>
              <div className="flex items-center gap-4">
                {visibleUploads.length > 0 && (
                  <button
                    className="text-sm text-gray-400 hover:text-white transition-colors duration-200"
                    onClick={hideAllUploads}
                  >
                    Hide all
                  </button>
                )}
                {hiddenUploads.size > 0 && (
                  <button
                    className="text-sm text-gray-400 hover:text-white transition-colors duration-200"
                    onClick={clearAllHidden}
                  >
                    Show all ({hiddenUploads.size} hidden)
                  </button>
                )}
              </div>
            </div>
            
            {visibleUploads.length > 0 ? (
              <>
                <div className="recent-uploads-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {visibleUploads.slice(0, 5).map((upload) => (
                    <div key={upload.id} className="recent-upload-item pgv-glass rounded-xl overflow-hidden transition-all duration-300 relative group glass-swish-hover">
                      {/* X button - always visible */}
                      <button
                        className="absolute top-2 right-2 text-white hover:text-gray-300 transition-colors duration-200 z-10 bg-black/50 backdrop-blur-sm rounded-full p-1"
                        onClick={() => hideUpload(upload.id)}
                        title="Hide from recent uploads (doesn't cancel processing)"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                      
                      {/* Status badge overlaid on image */}
                      <div className="absolute top-2 left-2 z-10">
                        <span className={`status-badge px-2 py-1 rounded-md text-xs font-medium backdrop-blur-md ${
                          upload.processing_status === 'completed' ? 'bg-green-500/80 text-white' :
                          upload.processing_status === 'failed' ? 'bg-red-500/80 text-white' :
                          upload.processing_status === 'pending' ? 'bg-yellow-500/80 text-white' :
                          'bg-blue-500/80 text-white'
                        }`}>
                          {upload.processing_status}
                        </span>
                      </div>
                      
                      {/* Image thumbnail or placeholder */}
                      <div className="upload-thumbnail aspect-square">
                        {upload.thumbnail_path ? (
                          <img
                            src={getFileUrl(upload.thumbnail_path)}
                            alt={upload.filename}
                            className="w-full h-full object-cover"
                            loading="lazy"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
                            {upload.file_type === 'image' ? (
                              <PhotoIcon className="w-12 h-12 text-gray-600" />
                            ) : (
                              <VideoCameraIcon className="w-12 h-12 text-gray-600" />
                            )}
                          </div>
                        )}
                      </div>
                      
                      {/* Filename below image */}
                      <div className="upload-info p-3 text-center">
                        <p className="upload-filename text-white font-medium text-sm truncate">
                          {upload.filename}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
                <button 
                  className="view-all-button pgv-button pgv-button-primary w-full py-3 rounded-lg font-medium transition-all duration-300 flex items-center justify-center gap-2 glass-swish-hover" 
                  onClick={() => navigate('/dashboard')}
                >
                  View all uploads
                  <ArrowRightIcon className="w-4 h-4" />
                </button>
              </>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-400">No recent uploads to show</p>
                {hiddenUploads.size > 0 && (
                  <button
                    className="mt-2 text-sm text-white hover:text-gray-300 transition-colors duration-200"
                    onClick={clearAllHidden}
                  >
                    Show {hiddenUploads.size} hidden upload{hiddenUploads.size !== 1 ? 's' : ''}
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tips Section with Glass Cards */}
        <div className="upload-tips pgv-glass p-8 rounded-2xl">
          <h3 className="text-2xl font-display font-semibold mb-6 text-white flex items-center gap-3 tracking-tight">
            <BoltIcon className="w-8 h-8 text-yellow-400" />
            Tips for best results
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { icon: PhotoIcon, text: 'Upload clear, high-quality images and videos', color: 'text-blue-600' },
              { icon: FolderIcon, text: 'Supported formats: JPEG, PNG, WebP, MP4, MOV', color: 'text-green-500' },
              { icon: ScaleIcon, text: 'Maximum file size: 100MB per file', color: 'text-red-500' },
              { icon: CpuChipIcon, text: 'Our AI will analyze your media and make it searchable', color: 'text-purple-700' }
            ].map((tip, index) => (
              <div key={index} className="flex items-start gap-4 p-4 rounded-lg hover:bg-white/5 transition-colors duration-200">
                <tip.icon className={`w-6 h-6 ${tip.color} flex-shrink-0 mt-0.5`} />
                <span className="text-gray-300">{tip.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Upload
