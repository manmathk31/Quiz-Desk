import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { GraduationCap, Mail, ArrowLeft, CheckCircle2, AlertCircle } from 'lucide-react'
import { supabase, isSupabaseConfigured } from '../../lib/supabase'

export const TeacherForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)
    setSubmitting(true)

    try {
      if (!isSupabaseConfigured) {
        throw new Error(
          'Supabase authentication is unconfigured in this environment. Live email dispatch requires valid credentials in frontend/.env.local.'
        )
      }

      const redirectTo = `${window.location.origin}/teacher/reset-password`
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim().toLowerCase(), {
        redirectTo,
      })

      if (error) {
        // Log technical message on console but show safe generic response to avoid email enumeration
        console.warn('[Password Recovery] Supabase recovery error:', error.message)
      }

      // Always present consistent generic message to avoid user enumeration
      setSubmitted(true)
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : 'An unexpected error occurred during password recovery.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative min-h-[calc(100vh-14rem)] flex flex-col justify-center items-center py-6 sm:py-10">
      <div className="absolute top-1/4 -left-12 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-12 w-72 h-72 bg-violet-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md mx-auto bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl shadow-xl shadow-slate-200/50 p-7 sm:p-9 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-600" />

        <div className="flex items-center space-x-3.5 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center text-white shadow-md shadow-indigo-600/25">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-100 text-[10px] font-bold text-indigo-700 uppercase tracking-wider mb-0.5">
              <span>Faculty Recovery</span>
            </div>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Password Reset</h1>
            <p className="text-xs text-slate-500">Recover your faculty credentials via Supabase Auth</p>
          </div>
        </div>

        {submitted ? (
          <div className="p-5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-slate-700 space-y-3">
            <div className="flex items-center space-x-2 text-emerald-800 font-semibold">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <span>Recovery Link Dispatched</span>
            </div>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              If an active faculty account is registered with{' '}
              <strong className="text-slate-900 font-mono">{email}</strong>, a secure password recovery
              link has been sent. Please check your inbox and spam folder.
            </p>
            <div className="pt-2">
              <Link
                to="/teacher/login"
                className="inline-flex items-center space-x-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Return to Faculty Sign In</span>
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <p className="text-xs text-slate-600 leading-relaxed">
              Enter your registered faculty email address. We will verify your credentials and
              send a password recovery link to your inbox.
            </p>

            {errorMessage && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div>
              <label htmlFor="recovery-email" className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Registered Faculty Email
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-indigo-600 transition-colors">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="recovery-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="faculty@college.edu"
                  className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50/60 hover:bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center space-x-2 py-3 px-4 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/25 active:scale-[0.99] transition-all cursor-pointer mt-2"
            >
              <Mail className="w-4 h-4" />
              <span>{submitting ? 'Dispatching Recovery Email...' : 'Send Recovery Link'}</span>
            </button>

            <div className="pt-2 text-center">
              <Link
                to="/teacher/login"
                className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Faculty Sign In</span>
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
