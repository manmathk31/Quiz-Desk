import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { fetchStudentQuizzes, startOrResumeAttempt } from '../../services/assessmentApi'
import type { StudentQuizSummary } from '../../types/assessment'
import {
  GraduationCap,
  Clock,
  Calendar,
  AlertCircle,
  PlayCircle,
  RotateCcw,
  CheckCircle2,
  RefreshCw,
  Search,
} from 'lucide-react'

export const StudentDashboard: React.FC = () => {
  const { session, profile } = useAuth()
  const token = session?.access_token || ''
  const navigate = useNavigate()

  const [quizzes, setQuizzes] = useState<StudentQuizSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [startingQuizId, setStartingQuizId] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')

  const loadQuizzes = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetchStudentQuizzes(token)
      setQuizzes(res.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assigned assessments.')
    } finally {
      setIsLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadQuizzes()
  }, [loadQuizzes])

  const handleStartOrResume = async (quizId: string) => {
    if (!token) return
    setStartingQuizId(quizId)
    setError(null)
    try {
      const res = await startOrResumeAttempt(token, quizId)
      navigate(`/student/assessments/${res.attempt_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start or resume assessment.')
    } finally {
      setStartingQuizId(null)
    }
  }

  const filteredQuizzes = quizzes.filter(
    (q) =>
      q.quiz_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.course_code.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatDateTime = (dateStr: string) => {
    try {
      const dt = new Date(dateStr)
      return dt.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 text-slate-900">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Student Assessment Portal</h1>
              <p className="text-xs text-slate-500">
                Institutional testing area & assigned course examinations
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {profile?.email && (
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-slate-800">{profile.email}</div>
              <div className="text-xs text-slate-500">Verified Student Account</div>
            </div>
          )}
          <button
            onClick={loadQuizzes}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="text-xs text-red-800">
            <div className="font-semibold">Assessment Notice</div>
            <p className="mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Search & Filters */}
      <div className="mt-6 flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by assessment title or course code..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="text-xs text-slate-500">
          Showing <span className="font-semibold text-slate-800">{filteredQuizzes.length}</span>{' '}
          assigned assessment{filteredQuizzes.length === 1 ? '' : 's'}
        </div>
      </div>

      {/* Assessments Grid */}
      {isLoading ? (
        <div className="mt-8 text-center py-16 bg-white border border-slate-200 rounded-xl">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-600 font-medium">Verifying assessment eligibility...</p>
        </div>
      ) : filteredQuizzes.length === 0 ? (
        <div className="mt-8 text-center py-16 bg-white border border-slate-200 rounded-xl">
          <GraduationCap className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-800">No Assessments Found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {searchTerm
              ? 'No assigned quizzes match your search criteria.'
              : 'You have no active assessments assigned to your student roster at this time.'}
          </p>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredQuizzes.map((quiz) => {
            const hasActiveAttempt = Boolean(quiz.active_attempt_id)
            const isCompleted = quiz.availability_status === 'COMPLETED'
            const isUpcoming = quiz.availability_status === 'UPCOMING'
            const isClosed = quiz.availability_status === 'CLOSED'
            const canStart = quiz.availability_status === 'OPEN' && !isCompleted

            return (
              <div
                key={quiz.quiz_id}
                className={`bg-white border rounded-xl p-5 flex flex-col justify-between transition-shadow hover:shadow-sm ${
                  hasActiveAttempt
                    ? 'border-amber-300 ring-1 ring-amber-300'
                    : isCompleted
                    ? 'border-slate-200 opacity-80'
                    : 'border-slate-200'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-100 text-slate-700">
                      {quiz.course_code}
                    </span>
                    {hasActiveAttempt ? (
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-800 flex items-center space-x-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                        <span>Attempt In Progress</span>
                      </span>
                    ) : isCompleted ? (
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-600 flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        <span>Completed</span>
                      </span>
                    ) : isUpcoming ? (
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700">
                        Upcoming
                      </span>
                    ) : isClosed ? (
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-red-50 text-red-700">
                        Closed
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 flex items-center space-x-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <span>Open</span>
                      </span>
                    )}
                  </div>

                  <h3 className="text-base font-bold text-slate-900 leading-snug">
                    {quiz.quiz_title}
                  </h3>
                  {quiz.description && (
                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                      {quiz.description}
                    </p>
                  )}

                  <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs text-slate-600">
                    <div className="flex items-center space-x-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>{quiz.duration_minutes} Minutes</span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <RotateCcw className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>
                        Attempts: {quiz.attempts_taken} / {quiz.max_attempts}
                      </span>
                    </div>
                    <div className="col-span-2 flex items-center space-x-1.5 text-[11px] text-slate-500">
                      <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>
                        Window: {formatDateTime(quiz.opens_at)} – {formatDateTime(quiz.closes_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-500 italic">
                    {quiz.status_message}
                  </span>

                  {hasActiveAttempt ? (
                    <button
                      onClick={() => handleStartOrResume(quiz.quiz_id)}
                      disabled={startingQuizId === quiz.quiz_id}
                      className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-700 text-white flex items-center space-x-1.5 transition-colors shadow-sm disabled:opacity-50"
                    >
                      <PlayCircle className="w-3.5 h-3.5" />
                      <span>Resume Attempt</span>
                    </button>
                  ) : canStart ? (
                    <button
                      onClick={() => handleStartOrResume(quiz.quiz_id)}
                      disabled={startingQuizId === quiz.quiz_id}
                      className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-1.5 transition-colors shadow-sm disabled:opacity-50"
                    >
                      <PlayCircle className="w-3.5 h-3.5" />
                      <span>Start Assessment</span>
                    </button>
                  ) : (
                    <button
                      disabled
                      className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 text-slate-400 cursor-not-allowed"
                    >
                      {isCompleted ? 'Completed' : isUpcoming ? 'Not Open Yet' : 'Closed'}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
