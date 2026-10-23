import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X, User as UserIcon, LogOut, LogIn } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { Logo } from '../common/Logo'

export const Header: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const { session, user, role, signOut } = useAuth()

  const navLinks = [
    ...(session && role === 'student'
      ? [{ label: 'My Assessments', path: '/student/portal' }]
      : []),
    ...(session && role === 'teacher'
      ? [
          { label: 'Quizzes', path: '/teacher/quizzes' },
          { label: 'Question Bank', path: '/teacher/question-bank' },
        ]
      : []),
    ...(session && role === 'admin'
      ? [
          { label: 'Admin Dashboard', path: '/admin/dashboard' },
          { label: 'System Diagnostics', path: '/status' },
          { label: 'Architecture Overview', path: '/admin/overview' },
        ]
      : []),
  ]

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3">
            <Link to="/" className="focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg">
              <Logo subtitle="MIT Academy of Engineering" />
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

          {/* Right Section: Auth Status & Role-Segregated Actions */}
          <div className="hidden md:flex items-center space-x-3">
            {role === 'admin' && (
              <div className="flex items-center space-x-2 px-2.5 py-1 bg-slate-800/80 border border-slate-700/60 rounded text-xs text-slate-300">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="font-mono text-[11px]">API: Online</span>
              </div>
            )}

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
              <div className="flex items-center space-x-3">
                <Link
                  to="/student/login"
                  className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-lg text-xs font-semibold transition-all shadow-md shadow-blue-600/20 hover:scale-[1.02]"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Take Assessment</span>
                </Link>
              </div>
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
          <div className="pt-3 border-t border-slate-800">
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
              <div className="pt-1">
                <Link
                  to="/student/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center space-x-1.5 py-2.5 px-3 bg-blue-600 text-white rounded-lg text-sm font-semibold shadow-sm"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Take Assessment</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
