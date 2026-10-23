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
    <div className="max-w-md mx-auto my-12 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">Teacher Password Recovery</h1>
          <p className="text-xs text-slate-500">Reset your faculty credentials via Supabase Auth</p>
        </div>
      </div>

      {submitted ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-slate-700 space-y-3">
          <div className="flex items-center space-x-2 text-emerald-800 font-semibold">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>Recovery Instructions Dispatched</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            If an active faculty account is registered with{' '}
            <strong className="text-slate-900 font-mono">{email}</strong>, a secure password recovery
            link has been sent. Please check your inbox and spam folder.
          </p>
          <div className="pt-2">
            <Link
              to="/teacher/login"
              className="inline-flex items-center space-x-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-700"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Return to Faculty Login</span>
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-xs text-slate-600 leading-relaxed">
            Enter your registered institutional email address. We will verify your credentials and
            send a password recovery link to your inbox.
          </p>

          {errorMessage && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div>
            <label htmlFor="recovery-email" className="block text-xs font-medium text-slate-700 mb-1">
              Registered Faculty Email
            </label>
            <input
              id="recovery-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="faculty@college.edu"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Mail className="w-4 h-4" />
            <span>{submitting ? 'Sending Link...' : 'Send Recovery Email'}</span>
          </button>

          <div className="pt-2 text-center">
            <Link
              to="/teacher/login"
              className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Faculty Sign In</span>
            </Link>
          </div>
        </form>
      )}
    </div>
  )
}
