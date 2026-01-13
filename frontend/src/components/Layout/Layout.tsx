import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { 
  PhotoIcon,
  HomeIcon,
  ArrowUpOnSquareIcon,
  ChevronDownIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import './Layout.css'

function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const navItems = [
    { path: '/dashboard', label: 'Gallery', icon: HomeIcon },
    { path: '/upload', label: 'Upload', icon: ArrowUpOnSquareIcon },
  ]

  return (
    <div className="layout">
      <nav className="navbar pgv-glass">
        <div className="nav-container">
          {/* Logo with Glass Effect */}
          <div className="nav-brand">
            <NavLink to="/dashboard" className="brand-link">
              <PhotoIcon className="brand-icon w-8 h-8 text-white" />
              <span className="brand-text font-display font-bold tracking-tighter text-lg">VueMantic</span>
            </NavLink>
          </div>

          {/* Desktop Navigation with Glass Pills */}
          <div className="nav-links desktop-only">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `nav-link pgv-glass transition-all duration-300 ${isActive ? 'nav-link-active border-accent-primary' : ''}`
                }
              >
                <item.icon className="nav-icon w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            ))}
          </div>

          {/* User Menu with Glass Effect */}
          <div className="nav-user">
            <button
              className="user-menu-button pgv-glass transition-all duration-300"
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              aria-label="User menu"
            >
              <div className="user-avatar w-10 h-10 rounded-full bg-gradient-to-br from-black to-gray-800 flex items-center justify-center text-white font-semibold">
                {user?.email[0].toUpperCase()}
              </div>
              <span className="user-email desktop-only text-sm font-medium">{user?.email}</span>
              <ChevronDownIcon 
                className={`menu-chevron w-5 h-5 transition-transform duration-200 ${isUserMenuOpen ? 'rotate-180' : ''}`}
              />
            </button>

            {/* Glass Dropdown Menu */}
            {isUserMenuOpen && (
              <>
                <div
                  className="menu-overlay fixed inset-0 z-10"
                  onClick={() => setIsUserMenuOpen(false)}
                />
                <div className="user-dropdown pgv-glass-heavy absolute top-full right-0 mt-2 w-64 rounded-lg shadow-lg z-20 pgv-fade-in">
                  <div className="dropdown-header p-4">
                    <div className="user-info">
                      <p className="user-email-full text-white font-medium">{user?.email}</p>
                      <p className="user-id text-gray-400 text-sm">ID: {user?.id.slice(0, 8)}...</p>
                    </div>
                  </div>
                  <div className="dropdown-divider h-px bg-white/10" />
                  <button
                    className="dropdown-item logout-button w-full p-4 text-left hover:bg-white/10 transition-colors duration-200 flex items-center gap-3"
                    onClick={handleLogout}
                  >
                    <ArrowRightOnRectangleIcon className="w-5 h-5" />
                    <span className="font-medium">Logout</span>
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="mobile-menu-button mobile-only"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Mobile menu"
          >
            {isMobileMenuOpen ? (
              <XMarkIcon className="w-6 h-6" />
            ) : (
              <Bars3Icon className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="mobile-nav">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `mobile-nav-link ${isActive ? 'mobile-nav-link-active' : ''}`
                }
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <item.icon className="nav-icon w-5 h-5" />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-container">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default Layout
