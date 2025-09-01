import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { PhotoIcon, EyeIcon, EyeSlashIcon, ExclamationCircleIcon, CheckIcon } from '@heroicons/react/24/outline'
import './Register.css'

function Register() {
  const { register, isRegistering, registerError } = useAuth()
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const validatePassword = (password: string): string[] => {
    const errors: string[] = []
    
    if (password.length < 8) {
      errors.push('At least 8 characters long')
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('One uppercase letter')
    }
    if (!/[a-z]/.test(password)) {
      errors.push('One lowercase letter')
    }
    if (!/\d/.test(password)) {
      errors.push('One number')
    }
    if (!/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password)) {
      errors.push('One special character')
    }
    
    return errors
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }))

    // Clear validation errors on change
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }

    // Real-time password validation
    if (name === 'password') {
      const errors = validatePassword(value)
      if (errors.length > 0) {
        setValidationErrors(prev => ({
          ...prev,
          password: `Password must have: ${errors.join(', ')}`,
        }))
      }
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    
    // Validate
    const errors: Record<string, string> = {}
    
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }
    
    const passwordErrors = validatePassword(formData.password)
    if (passwordErrors.length > 0) {
      errors.password = `Password must have: ${passwordErrors.join(', ')}`
    }
    
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors)
      return
    }

    // Register
    try {
      await register.mutateAsync({
        email: formData.email,
        password: formData.password,
      })
      
      // Navigate to login with success message
      navigate('/login', { 
        state: { message: 'Registration successful! Please sign in.' }
      })
    } catch (error) {
      // Error is handled by the hook
    }
  }

  return (
    <div className="auth-page-with-grid min-h-screen flex items-center justify-center bg-gray-950 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="pgv-glass p-8 rounded-2xl space-y-6">
          {/* Logo */}
          <div className="text-center">
            <PhotoIcon className="w-12 h-12 mx-auto text-white mb-4" />
            <h1 className="text-2xl font-display font-bold text-white tracking-tighter">VueMantic</h1>
          </div>

          {/* Title */}
          <div className="text-center">
            <h2 className="text-xl font-display font-semibold text-white mb-2 tracking-tight">Create an account</h2>
          </div>

          {/* Error message */}
          {registerError && (
            <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
              <ExclamationCircleIcon className="w-5 h-5 text-red-400 flex-shrink-0" />
              <span className="text-red-100 text-sm">
                {registerError.response?.data?.detail || 'Registration failed. Please try again.'}
              </span>
            </div>
          )}

          {/* Form */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium text-white">
                Email address
              </label>
              <input
                type="email"
                id="email"
                name="email"
                className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-white/30 focus:bg-black/50 transition-all duration-200"
                placeholder="you@example.com"
                value={formData.email}
                onChange={handleInputChange}
                required
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium text-white">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  className={`w-full px-4 py-3 pr-12 bg-black/30 border rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-white/30 focus:bg-black/50 transition-all duration-200 ${
                    validationErrors.password ? 'border-red-500/50' : 'border-white/10'
                  }`}
                  placeholder="Create a strong password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors duration-200"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="w-5 h-5" />
                  ) : (
                    <EyeIcon className="w-5 h-5" />
                  )}
                </button>
              </div>
              {validationErrors.password && (
                <p className="text-red-400 text-xs mt-1">{validationErrors.password}</p>
              )}
              
              {/* Password requirements */}
              {formData.password && (
                <div className="mt-3 p-3 bg-black/20 rounded-lg">
                  <p className="text-xs font-medium text-white mb-2">Password requirements:</p>
                  <div className="grid grid-cols-1 gap-1 text-xs">
                    <div className={`flex items-center gap-2 ${formData.password.length >= 8 ? 'text-green-400' : 'text-gray-400'}`}>
                      <CheckIcon className="w-3 h-3" />
                      <span>At least 8 characters</span>
                    </div>
                    <div className={`flex items-center gap-2 ${/[A-Z]/.test(formData.password) ? 'text-green-400' : 'text-gray-400'}`}>
                      <CheckIcon className="w-3 h-3" />
                      <span>One uppercase letter</span>
                    </div>
                    <div className={`flex items-center gap-2 ${/[a-z]/.test(formData.password) ? 'text-green-400' : 'text-gray-400'}`}>
                      <CheckIcon className="w-3 h-3" />
                      <span>One lowercase letter</span>
                    </div>
                    <div className={`flex items-center gap-2 ${/\d/.test(formData.password) ? 'text-green-400' : 'text-gray-400'}`}>
                      <CheckIcon className="w-3 h-3" />
                      <span>One number</span>
                    </div>
                    <div className={`flex items-center gap-2 ${/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(formData.password) ? 'text-green-400' : 'text-gray-400'}`}>
                      <CheckIcon className="w-3 h-3" />
                      <span>One special character</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-white">
                Confirm password
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                id="confirmPassword"
                name="confirmPassword"
                className={`w-full px-4 py-3 bg-black/30 border rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-white/30 focus:bg-black/50 transition-all duration-200 ${
                  validationErrors.confirmPassword ? 'border-red-500/50' : 'border-white/10'
                }`}
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                required
              />
              {validationErrors.confirmPassword && (
                <p className="text-red-400 text-xs mt-1">{validationErrors.confirmPassword}</p>
              )}
            </div>

            <button
              type="submit"
              className="w-full py-3 px-4 bg-black text-white font-medium rounded-xl hover:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 mt-6"
              disabled={isRegistering}
            >
              {isRegistering ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                  <span>Creating account...</span>
                </div>
              ) : (
                'Create account'
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="text-center pt-4">
            <p className="text-sm text-gray-300">
              Already have an account?{' '}
              <Link to="/login" className="text-white font-medium hover:text-gray-300 transition-colors duration-200">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Register
