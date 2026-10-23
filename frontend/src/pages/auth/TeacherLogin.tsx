import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  BookOpen,
  ShieldAlert,
  LogIn,
  CheckCircle2,
  Mail,
  Lock,
  Eye,
  EyeOff,
  GraduationCap,
  Loader2,
  ArrowRight,
} from 'lucide-react'

export const TeacherLogin: React.FC = () => {
  const { session, user, role, signInWithEmail, isConfigured } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const navigate = useNavigate()

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setSubmitting(true)

    try {
      const { error } = await signInWithEmail(email.trim().toLowerCase(), password)
      if (error) {
        setErrorMsg(error.message)
      } else {
        navigate('/teacher/quizzes', { replace: true })
      }
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error ? err.message : 'An unexpected error occurred during faculty sign in.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (session && user) {
    return (
      <div className="relative min-h-[calc(100vh-14rem)] flex flex-col justify-center items-center py-6 sm:py-10">
        <div className="relative w-full max-w-md mx-auto bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl shadow-xl shadow-slate-200/50 p-7 sm:p-8 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-emerald-500 to-teal-500" />

          <div className="flex items-center space-x-3 mb-5">
            <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                Active Session
              </span>
              <h2 className="text-base font-bold text-slate-900 mt-0.5">Faculty Portal</h2>
              <p className="text-xs text-slate-500 font-mono truncate max-w-[240px]">{user.email}</p>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 mb-6 text-xs flex justify-between items-center">
            <span className="text-slate-500">Authorized Role:</span>
            <span className="font-bold text-indigo-700 uppercase bg-indigo-50 border border-indigo-100 px-2.5 py-0.5 rounded-md">
              {role || 'Faculty'}
            </span>
          </div>

          <div className="space-y-2.5">
            <Link
              to="/teacher/quizzes"
              className="flex items-center justify-between w-full py-3 px-4 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 active:scale-[0.99] rounded-xl shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
            >
              <span>Access Quiz Management</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/teacher/question-bank"
              className="flex items-center justify-between w-full py-3 px-4 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200/80 active:scale-[0.99] rounded-xl transition-all cursor-pointer"
            >
              <span>Access Question Bank</span>
              <ArrowRight className="w-4 h-4 text-slate-400" />
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative min-h-[calc(100vh-14rem)] flex flex-col justify-center items-center py-6 sm:py-10">
      {/* Ambient background glow orbs */}
      <div className="absolute top-1/4 -left-12 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-12 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md mx-auto bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl shadow-xl shadow-slate-200/50 p-7 sm:p-9 overflow-hidden">
        {/* Top accent gradient bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-600" />

        {/* Header Block */}
        <div className="flex items-center space-x-3.5 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center text-white shadow-md shadow-indigo-600/25">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-100 text-[10px] font-bold text-indigo-700 uppercase tracking-wider mb-0.5">
              <span>Faculty & Instructor Portal</span>
            </div>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Faculty Sign In</h1>
            <p className="text-xs text-slate-500">Manage quizzes, question banks, and class grading</p>
          </div>
        </div>

        {!isConfigured && (
          <div className="mb-5 p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-slate-700">
            <div className="flex items-center space-x-2 text-amber-900 font-semibold mb-1">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span>Development Notice</span>
            </div>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              Authentication requires credentials configured in{' '}
              <code className="bg-amber-100 font-mono text-[10px] px-1 py-0.5 rounded">frontend/.env.local</code>.
            </p>
          </div>
        )}

        {errorMsg && (
          <div className="mb-5 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 leading-relaxed">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSignIn} className="space-y-4">
          <div>
            <label htmlFor="teacher-email" className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Faculty Email Address
            </label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-600 transition-colors">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="teacher-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="prof.name@college.edu"
                className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50/60 hover:bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="teacher-password" className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                Password
              </label>
              <Link
                to="/teacher/forgot-password"
                className="text-xs text-indigo-600 hover:text-indigo-700 font-medium transition-colors"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-600 transition-colors">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="teacher-password"
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your account password"
                className="w-full pl-10 pr-10 py-2.5 bg-slate-50/60 hover:bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || !isConfigured}
            className="w-full flex items-center justify-center space-x-2 py-3 px-4 bg-gradient-to-r from-indigo-600 via-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/25 active:scale-[0.99] transition-all cursor-pointer mt-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Verifying Credentials...</span>
              </>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In as Faculty</span>
              </>
            )}
          </button>
        </form>

        {/* Cross-portal switcher */}
        <div className="mt-6 pt-5 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500">Are you a student taking a quiz?</span>
          <Link
            to="/student/login"
            className="inline-flex items-center space-x-1 font-semibold text-blue-600 hover:text-blue-700 transition-colors"
          >
            <GraduationCap className="w-3.5 h-3.5" />
            <span>Student Entrance</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
