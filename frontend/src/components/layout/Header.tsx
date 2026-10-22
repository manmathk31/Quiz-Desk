import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { GraduationCap, Menu, X, User as UserIcon, LogOut, LogIn } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export const Header: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const { session, user, role, signOut } = useAuth()

  const navLinks = [
    { label: 'Overview', path: '/' },
    { label: 'System Status', path: '/status' },
    ...(session
      ? [
          { label: 'Student Portal', path: '/student/portal' },
          { label: 'Teacher Portal', path: '/teacher/portal' },
          { label: 'Question Bank', path: '/teacher/question-bank' },
        ]
      : []),
  ]


  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3">
            <Link to="/" className="flex items-center space-x-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded">
              <div className="w-9 h-9 bg-blue-600 rounded flex items-center justify-center text-white">
                <GraduationCap className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-lg tracking-tight text-white">Quizdesk</span>
                <span className="text-[10px] text-slate-400 uppercase tracking-wider font-medium -mt-1">
                  Academic Portal
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1" aria-label="Main Navigation">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                    isActive
                      ? 'bg-slate-800 text-white'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </nav>

          {/* Right Section: System Indicator, Auth Status & Actions */}
          <div className="hidden md:flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-2.5 py-1 bg-slate-800/80 border border-slate-700/60 rounded text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="font-mono text-[11px]">API: Online</span>
            </div>

            {session && user ? (
              <div className="flex items-center space-x-2.5 pl-2 border-l border-slate-800">
                <div className="flex items-center space-x-1.5 text-xs text-slate-300">
                  <UserIcon className="w-3.5 h-3.5 text-blue-400" />
                  <span className="font-mono text-[11px] max-w-[140px] truncate">{user.email}</span>
                  {role && (
                    <span className="px-1.5 py-0.5 text-[10px] font-bold uppercase rounded bg-blue-900/60 text-blue-300 border border-blue-700/50">
                      {role}
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => signOut()}
                  className="flex items-center space-x-1 p-1.5 text-slate-400 hover:text-rose-300 hover:bg-slate-800 rounded transition-colors text-xs"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded text-slate-400 hover:text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-800 bg-slate-900 px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3 py-2 rounded text-base font-medium ${
                  isActive
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                {link.label}
              </Link>
            )
          })}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
            {session && user ? (
              <div className="flex items-center justify-between w-full">
                <span className="text-xs font-mono text-slate-300 truncate max-w-[180px]">{user.email}</span>
                <button
                  type="button"
                  onClick={() => {
                    signOut()
                    setMobileMenuOpen(false)
                  }}
                  className="flex items-center space-x-1 text-xs text-rose-400"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center space-x-1.5 text-xs text-blue-400 font-medium"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In to Quizdesk</span>
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
