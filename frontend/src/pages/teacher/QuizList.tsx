import React, { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import type { QuizListItem, QuizCreatePayload } from '../../types/quiz'
import { fetchQuizzes, createQuiz } from '../../services/quizApi'
import { QuizPreviewModal } from './QuizPreviewModal'
import {
  Plus,
  Search,
  Calendar,
  ChevronRight,
  Eye,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FolderOpen,
  X,
  Award,
} from 'lucide-react'

export const QuizList: React.FC = () => {
  const { session } = useAuth()
  const token = session?.access_token || ''
  const navigate = useNavigate()

  const [quizzes, setQuizzes] = useState<QuizListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'draft' | 'published'>('all')

  // Create Quiz Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  // Quick Preview state
  const [previewQuizId, setPreviewQuizId] = useState<string | null>(null)

  const [title, setTitle] = useState('')
  const [courseCode, setCourseCode] = useState('')
  const [description, setDescription] = useState('')
  const [opensAt, setOpensAt] = useState(() => {
    const t = new Date(Date.now() + 24 * 60 * 60 * 1000)
    return t.toISOString().slice(0, 16)
  })
  const [closesAt, setClosesAt] = useState(() => {
    const d = new Date(Date.now() + 48 * 60 * 60 * 1000)
    return d.toISOString().slice(0, 16)
  })
  const [durationMinutes, setDurationMinutes] = useState(60)

  const loadQuizzes = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchQuizzes(token)
      setQuizzes(data.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load quizzes.')
    } finally {
      setIsLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadQuizzes()
  }, [loadQuizzes])

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreateError(null)

    if (new Date(closesAt) <= new Date(opensAt)) {
      setCreateError('Closing time must be strictly after opening time.')
      return
    }

    if (durationMinutes <= 0) {
      setCreateError('Duration must be greater than 0 minutes.')
      return
    }

    const payload: QuizCreatePayload = {
      title: title.trim(),
      course_code: courseCode.trim().toUpperCase(),
      description: description.trim() || undefined,
      opens_at: new Date(opensAt).toISOString(),
      closes_at: new Date(closesAt).toISOString(),
      duration_minutes: durationMinutes,
      max_attempts: 1,
      allow_backtracking: true,
      shuffle_questions: false,
      shuffle_options: false,
      multi_answer_policy: 'all_or_nothing',
      tab_switch_limit: 3,
      tab_switch_penalty_marks: 0.0,
    }

    setIsSubmitting(true)
    try {
      const newQuiz = await createQuiz(token, payload)
      setIsCreateModalOpen(false)
      navigate(`/teacher/quizzes/${newQuiz.id}`)
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create quiz.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const filteredQuizzes = quizzes.filter((q) => {
    const matchesSearch =
      q.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.course_code.toLowerCase().includes(searchQuery.toLowerCase())
    if (statusFilter === 'draft') return matchesSearch && !q.is_published
    if (statusFilter === 'published') return matchesSearch && q.is_published
    return matchesSearch
  })

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6 text-slate-900">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Assessments & Quizzes</h1>
            <span className="px-2 py-0.5 bg-slate-100 text-slate-700 text-xs font-semibold rounded-full border border-slate-200">
              {quizzes.length} {quizzes.length === 1 ? 'Quiz' : 'Quizzes'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Author quizzes, configure academic parameters, clone question sets, and publish immutable versions
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setTitle('')
            setCourseCode('')
            setDescription('')
            setCreateError(null)
            setIsCreateModalOpen(true)
          }}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors shadow-2xs shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Quiz Draft</span>
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={loadQuizzes}
            className="text-xs font-semibold underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Search and Status Filters */}
      <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full sm:max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title or course code..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center space-x-1.5 w-full sm:w-auto">
          {(['all', 'draft', 'published'] as const).map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setStatusFilter(filter)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg capitalize transition-colors ${
                statusFilter === filter
                  ? 'bg-slate-900 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      {/* Quiz List */}
      {isLoading ? (
        <div className="py-20 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
          <p className="text-xs text-slate-500 font-medium">Loading your quizzes...</p>
        </div>
      ) : filteredQuizzes.length === 0 ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-xl space-y-3">
          <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto text-slate-400">
            <FolderOpen className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800">No quizzes found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {searchQuery || statusFilter !== 'all'
              ? 'No quizzes matched your active search or status filters.'
              : 'You have not authored any quizzes yet. Click "New Quiz Draft" to begin.'}
          </p>
          <div className="pt-2">
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create First Quiz</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredQuizzes.map((quiz) => (
            <div
              key={quiz.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs hover:border-slate-300 transition-all flex flex-col justify-between space-y-4"
            >
              {/* Header Badges */}
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                    {quiz.course_code}
                  </span>
                  <div className="flex items-center space-x-1.5">
                    <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                      v{quiz.version_number}
                    </span>
                    {quiz.is_published ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Published</span>
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200">
                        Draft
                      </span>
                    )}
                  </div>
                </div>

                <Link
                  to={`/teacher/quizzes/${quiz.id}`}
                  className="block text-base font-bold text-slate-900 hover:text-blue-600 transition-colors"
                >
                  {quiz.title}
                </Link>

                {quiz.description && (
                  <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                    {quiz.description}
                  </p>
                )}
              </div>

              {/* Assessment Stats */}
              <div className="pt-3 border-t border-slate-100 grid grid-cols-3 gap-2 text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase font-medium">Questions</span>
                  <span className="font-semibold text-slate-700">{quiz.total_questions}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase font-medium">Total Marks</span>
                  <span className="font-semibold text-emerald-700">+{Number(quiz.total_marks).toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase font-medium">Duration</span>
                  <span className="font-semibold text-slate-700">{quiz.duration_minutes}m</span>
                </div>
              </div>

              {/* Difficulty Pills & Window */}
              <div className="space-y-2 pt-1 text-[11px] text-slate-500">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="truncate">
                    {new Date(quiz.opens_at).toLocaleDateString()} – {new Date(quiz.closes_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex items-center space-x-1.5 pt-1">
                  <span className="text-[10px] text-slate-400 font-medium">Difficulty:</span>
                  <span className="px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
                    {quiz.difficulty_breakdown.easy} Easy
                  </span>
                  <span className="px-1.5 py-0.2 rounded bg-amber-50 text-amber-700 font-semibold text-[10px]">
                    {quiz.difficulty_breakdown.medium} Med
                  </span>
                  <span className="px-1.5 py-0.2 rounded bg-rose-50 text-rose-700 font-semibold text-[10px]">
                    {quiz.difficulty_breakdown.hard} Hard
                  </span>
                </div>
              </div>

              {/* Footer Actions */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setPreviewQuizId(quiz.id)}
                  className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 font-medium"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Preview</span>
                </button>

                <div className="flex items-center space-x-2">
                  {quiz.is_published && (
                    <Link
                      to={`/teacher/quizzes/${quiz.id}/results`}
                      className="inline-flex items-center space-x-1 px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold transition-colors"
                    >
                      <Award className="w-3.5 h-3.5" />
                      <span>Results</span>
                    </Link>
                  )}
                  <Link
                    to={`/teacher/quizzes/${quiz.id}`}
                    className="inline-flex items-center space-x-1 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition-colors"
                  >
                    <span>Open Builder</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* New Quiz Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full flex flex-col text-slate-900">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900">Create New Quiz Draft</h2>
                <p className="text-xs text-slate-500">Initializes assessment draft version 1</p>
              </div>
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4 text-xs">
              {createError && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{createError}</span>
                </div>
              )}

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block font-semibold text-slate-700 mb-1">Quiz Title</label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Midterm Assessment"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Course Code</label>
                  <input
                    type="text"
                    value={courseCode}
                    onChange={(e) => setCourseCode(e.target.value)}
                    placeholder="e.g. CS201"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase font-mono"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Instructions / Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Instructions displayed to students before starting..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Window Opens At</label>
                  <input
                    type="datetime-local"
                    value={opensAt}
                    onChange={(e) => setOpensAt(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Window Closes At</label>
                  <input
                    type="datetime-local"
                    value={closesAt}
                    onChange={(e) => setClosesAt(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Duration per Attempt (Minutes)
                </label>
                <input
                  type="number"
                  min="1"
                  max="1440"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(parseInt(e.target.value) || 60)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  required
                />
              </div>

              <div className="pt-3 border-t border-slate-200 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-3.5 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold"
                >
                  {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <span>Create & Open Builder</span>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewQuizId && (
        <QuizPreviewModal
          isOpen={true}
          token={token}
          quizId={previewQuizId}
          onClose={() => setPreviewQuizId(null)}
          onPublishSuccess={() => {
            setPreviewQuizId(null)
            loadQuizzes()
          }}
        />
      )}
    </div>
  )
}
