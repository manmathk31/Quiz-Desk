import React, { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import type {
  QuizDetail,
  QuizVersion,
  QuizUpdatePayload,
  MultiAnswerPolicy,
} from '../../types/quiz'
import type { QuestionDifficulty } from '../../types/question'
import {
  getQuiz,
  updateQuiz,
  addQuestionsToQuiz,
  removeQuestionFromQuiz,
  reorderQuizQuestions,
} from '../../services/quizApi'
import { QuestionSelectorModal } from './QuestionSelectorModal'
import { QuizPreviewModal } from './QuizPreviewModal'
import { RosterTab } from './RosterTab'
import {
  ArrowLeft,
  Save,
  Send,
  Eye,
  Plus,
  ArrowUp,
  ArrowDown,
  Trash2,
  Layers,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Settings,
  Users,
  Award,
} from 'lucide-react'

export const QuizBuilder: React.FC = () => {
  const { quizId } = useParams<{ quizId: string }>()
  const { session } = useAuth()
  const token = session?.access_token || ''

  const [activeTab, setActiveTab] = useState<'content' | 'roster'>('content')
  const [quiz, setQuiz] = useState<QuizDetail | null>(null)
  const [activeVersion, setActiveVersion] = useState<QuizVersion | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successFeedback, setSuccessFeedback] = useState<string | null>(null)


  // Modals
  const [isSelectorOpen, setIsSelectorOpen] = useState(false)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)

  // Form settings state
  const [title, setTitle] = useState('')
  const [courseCode, setCourseCode] = useState('')
  const [description, setDescription] = useState('')
  const [opensAt, setOpensAt] = useState('')
  const [closesAt, setClosesAt] = useState('')
  const [durationMinutes, setDurationMinutes] = useState(60)
  const [maxAttempts, setMaxAttempts] = useState(1)
  const [allowBacktracking, setAllowBacktracking] = useState(true)
  const [shuffleQuestions, setShuffleQuestions] = useState(false)
  const [shuffleOptions, setShuffleOptions] = useState(false)
  const [multiAnswerPolicy, setMultiAnswerPolicy] = useState<MultiAnswerPolicy>('all_or_nothing')
  const [tabSwitchLimit, setTabSwitchLimit] = useState(3)
  const [tabSwitchPenaltyMarks, setTabSwitchPenaltyMarks] = useState(0.0)

  const loadQuizData = useCallback(async () => {
    if (!token || !quizId) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await getQuiz(token, quizId)
      setQuiz(data)
      // Pick active version: draft takes precedence, fallback to published
      const currentV = data.draft_version || data.published_version
      setActiveVersion(currentV || null)

      // Sync form fields from version & quiz metadata
      setTitle(data.title)
      setCourseCode(data.course_code)
      setDescription(data.description || '')

      if (currentV) {
        setOpensAt(new Date(currentV.opens_at).toISOString().slice(0, 16))
        setClosesAt(new Date(currentV.closes_at).toISOString().slice(0, 16))
        setDurationMinutes(currentV.duration_minutes)
        setMaxAttempts(currentV.max_attempts)
        setAllowBacktracking(currentV.allow_backtracking)
        setShuffleQuestions(currentV.shuffle_questions)
        setShuffleOptions(currentV.shuffle_options)
        setMultiAnswerPolicy(currentV.multi_answer_policy)
        setTabSwitchLimit(currentV.tab_switch_limit)
        setTabSwitchPenaltyMarks(Number(currentV.tab_switch_penalty_marks))
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load quiz.')
    } finally {
      setIsLoading(false)
    }
  }, [token, quizId])

  useEffect(() => {
    loadQuizData()
  }, [loadQuizData])

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !quizId) return

    if (new Date(closesAt) <= new Date(opensAt)) {
      setError('Closing time must be strictly after opening time.')
      return
    }

    if (durationMinutes <= 0) {
      setError('Duration must be greater than 0 minutes.')
      return
    }

    const payload: QuizUpdatePayload = {
      title: title.trim(),
      course_code: courseCode.trim().toUpperCase(),
      description: description.trim() || undefined,
      opens_at: new Date(opensAt).toISOString(),
      closes_at: new Date(closesAt).toISOString(),
      duration_minutes: durationMinutes,
      max_attempts: maxAttempts,
      allow_backtracking: allowBacktracking,
      shuffle_questions: shuffleQuestions,
      shuffle_options: shuffleOptions,
      multi_answer_policy: multiAnswerPolicy,
      tab_switch_limit: tabSwitchLimit,
      tab_switch_penalty_marks: tabSwitchPenaltyMarks,
    }

    setIsSaving(true)
    setError(null)
    try {
      const updated = await updateQuiz(token, quizId, payload)
      setQuiz(updated)
      setActiveVersion(updated.draft_version || updated.published_version || null)
      setSuccessFeedback('Quiz settings updated successfully.')
      setTimeout(() => setSuccessFeedback(null), 3500)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update quiz settings.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleAddQuestions = async (questionIds: string[]) => {
    if (!token || !quizId) return
    try {
      const updatedVersion = await addQuestionsToQuiz(token, quizId, questionIds)
      setActiveVersion(updatedVersion)
      setSuccessFeedback(`Added ${questionIds.length} question(s) to draft.`)
      setTimeout(() => setSuccessFeedback(null), 3000)
      loadQuizData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to add questions.')
    }
  }

  const handleRemoveQuestion = async (questionId: string) => {
    if (!token || !quizId) return
    try {
      const updatedVersion = await removeQuestionFromQuiz(token, quizId, questionId)
      setActiveVersion(updatedVersion)
      setSuccessFeedback('Question removed from draft.')
      setTimeout(() => setSuccessFeedback(null), 3000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to remove question.')
    }
  }

  const handleMoveQuestion = async (currentIndex: number, direction: 'up' | 'down') => {
    if (!token || !quizId || !activeVersion) return
    const questions = [...activeVersion.questions]
    const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1
    if (targetIndex < 0 || targetIndex >= questions.length) return

    // Swap elements
    const temp = questions[currentIndex]
    questions[currentIndex] = questions[targetIndex]
    questions[targetIndex] = temp

    try {
      const updatedVersion = await reorderQuizQuestions(token, quizId, questions.map((q) => q.id))
      setActiveVersion(updatedVersion)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to reorder questions.')
    }
  }

  const renderDifficultyBadge = (difficulty: QuestionDifficulty) => {
    switch (difficulty) {
      case 'easy':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200">
            Easy
          </span>
        )
      case 'medium':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200">
            Medium
          </span>
        )
      case 'hard':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-200">
            Hard
          </span>
        )
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        <p className="text-xs text-slate-500 font-medium">Loading assessment builder...</p>
      </div>
    )
  }

  if (!quiz || !activeVersion) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center space-y-3">
        <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
        <h2 className="text-base font-bold text-slate-800">Quiz Not Found</h2>
        <p className="text-xs text-slate-500">The requested quiz does not exist or you lack authorization to access it.</p>
        <Link
          to="/teacher/quizzes"
          className="inline-flex items-center space-x-1.5 text-xs text-blue-600 font-semibold"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Quizzes</span>
        </Link>
      </div>
    )
  }

  const isPublished = quiz.is_published && !quiz.draft_version

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6 text-slate-900">
      {/* Top Breadcrumb & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="space-y-1">
          <Link
            to="/teacher/quizzes"
            className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 font-medium transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Quizzes</span>
          </Link>

          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold tracking-tight text-slate-900">{quiz.title}</h1>
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
              {quiz.course_code}
            </span>
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              Version {activeVersion.version_number} {activeVersion.is_published ? '(Published)' : '(Draft)'}
            </span>
            {isPublished ? (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Published Snapshot</span>
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200">
                Draft Editing
              </span>
            )}
          </div>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center space-x-2.5">
          {isPublished && (
            <Link
              to={`/teacher/quizzes/${quiz.id}/results`}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-blue-50 border border-blue-200 hover:bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold transition-colors shadow-2xs"
            >
              <Award className="w-3.5 h-3.5 text-blue-600" />
              <span>Results & Grading</span>
            </Link>
          )}

          <button
            type="button"
            onClick={() => setIsPreviewOpen(true)}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium transition-colors shadow-2xs"
          >
            <Eye className="w-3.5 h-3.5 text-slate-500" />
            <span>Preview Assessment</span>
          </button>

          {!isPublished && (
            <button
              type="button"
              onClick={() => setIsPreviewOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors shadow-2xs"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Publish Version</span>
            </button>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-2">
        <button
          type="button"
          onClick={() => setActiveTab('content')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'content'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span>Quiz Settings & Questions</span>
          <span className="px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-bold">
            {activeVersion.questions.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('roster')}
          className={`px-4 py-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'roster'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Student Roster & Eligibility</span>
        </button>
      </div>

      {/* Success Notification */}
      {successFeedback && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-lg text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successFeedback}</span>
        </div>
      )}

      {/* Error Notification */}
      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-xs text-rose-500 hover:text-rose-700"
          >
            Dismiss
          </button>
        </div>
      )}

      {activeTab === 'roster' ? (
        <RosterTab quizId={quiz.id} token={token} />
      ) : (
        /* Two-Column Editor Layout */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Assessment Configuration Form (5 cols) */}
          <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2">
                <Settings className="w-4 h-4 text-blue-600" />
                <h2 className="text-sm font-bold text-slate-900">Assessment Settings</h2>
              </div>

            {isPublished && (
              <span className="text-[10px] text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                Editing forks v{activeVersion.version_number + 1}
              </span>
            )}
          </div>

          <form onSubmit={handleSaveSettings} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Quiz Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Course Code</label>
                <input
                  type="text"
                  value={courseCode}
                  onChange={(e) => setCourseCode(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono uppercase"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Per-Attempt Duration</label>
                <div className="relative">
                  <input
                    type="number"
                    min="1"
                    max="1440"
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(parseInt(e.target.value) || 60)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono pr-12"
                    required
                  />
                  <span className="absolute right-3 top-2 text-slate-400 text-xs">mins</span>
                </div>
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Instructions / Description</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Guidelines displayed before candidate starts attempt..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Opens At (UTC)</label>
                <input
                  type="datetime-local"
                  value={opensAt}
                  onChange={(e) => setOpensAt(e.target.value)}
                  className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-[11px]"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Closes At (UTC)</label>
                <input
                  type="datetime-local"
                  value={closesAt}
                  onChange={(e) => setClosesAt(e.target.value)}
                  className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-[11px]"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Max Attempts</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={maxAttempts}
                  onChange={(e) => setMaxAttempts(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Multi-Answer Scoring</label>
                <select
                  value={multiAnswerPolicy}
                  onChange={(e) => setMultiAnswerPolicy(e.target.value as MultiAnswerPolicy)}
                  className="w-full px-2.5 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="all_or_nothing">All or Nothing</option>
                  <option value="partial_with_penalty">Partial with Penalty</option>
                  <option value="partial_no_penalty">Partial without Penalty</option>
                </select>
              </div>
            </div>

            {/* Navigation & Randomization Policies */}
            <div className="space-y-2 pt-2 border-t border-slate-200">
              <label className="font-semibold text-slate-700 block">Assessment Experience Policies</label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={allowBacktracking}
                  onChange={(e) => setAllowBacktracking(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                />
                <span className="text-slate-700">Allow candidate backtracking between questions</span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={shuffleQuestions}
                  onChange={(e) => setShuffleQuestions(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                />
                <span className="text-slate-700">Randomize question order per candidate</span>
              </label>

              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={shuffleOptions}
                  onChange={(e) => setShuffleOptions(e.target.checked)}
                  className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                />
                <span className="text-slate-700">Randomize answer option order</span>
              </label>
            </div>

            {/* Telemetry Configuration */}
            <div className="space-y-2 pt-2 border-t border-slate-200">
              <label className="font-semibold text-slate-700 block">Proctoring Telemetry Settings</label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="text-[11px] text-slate-500 block mb-1">Tab Switch Warnings</span>
                  <input
                    type="number"
                    min="0"
                    max="20"
                    value={tabSwitchLimit}
                    onChange={(e) => setTabSwitchLimit(parseInt(e.target.value) || 0)}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>
                <div>
                  <span className="text-[11px] text-slate-500 block mb-1">Penalty Deduction Marks</span>
                  <input
                    type="number"
                    step="0.25"
                    min="0"
                    value={tabSwitchPenaltyMarks}
                    onChange={(e) => setTabSwitchPenaltyMarks(parseFloat(e.target.value) || 0)}
                    className="w-full px-2.5 py-1.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors shadow-2xs"
              >
                {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                <span>Save Assessment Settings</span>
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Questions Assembly (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Questions Assembly Header */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Quiz Content & Questions</h2>
                <p className="text-xs text-slate-500">
                  Questions locked to Version {activeVersion.version_number} snapshot
                </p>
              </div>

              <button
                type="button"
                onClick={() => setIsSelectorOpen(true)}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors shadow-2xs shrink-0"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add from Question Bank</span>
              </button>
            </div>

            {/* Metrics Bar */}
            <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center space-x-4">
                <span className="font-semibold text-slate-700">
                  {activeVersion.total_questions} Questions
                </span>
                <span className="font-semibold text-emerald-700">
                  +{Number(activeVersion.total_marks).toFixed(2)} Total Marks
                </span>
              </div>

              {/* Difficulty breakdown pills */}
              <div className="flex items-center space-x-1.5">
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
                  {activeVersion.difficulty_breakdown.easy} Easy
                </span>
                <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 font-semibold text-[10px]">
                  {activeVersion.difficulty_breakdown.medium} Medium
                </span>
                <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-semibold text-[10px]">
                  {activeVersion.difficulty_breakdown.hard} Hard
                </span>
              </div>
            </div>
          </div>

          {/* Questions List */}
          {activeVersion.questions.length === 0 ? (
            <div className="p-12 text-center bg-white border border-slate-200 rounded-xl space-y-3">
              <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto text-slate-400">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-slate-800">No questions in this quiz draft</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Add questions from your reusable Question Bank to prepare this quiz for publication.
              </p>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setIsSelectorOpen(true)}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Select Bank Questions</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {activeVersion.questions.map((q, idx) => (
                <div
                  key={q.id}
                  className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs space-y-3 text-xs"
                >
                  {/* Card Header & Controls */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-slate-400">#{idx + 1}</span>
                      <span className="px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-bold uppercase tracking-wider">
                        {q.question_type.replace('_', ' ')}
                      </span>
                      {renderDifficultyBadge(q.difficulty)}
                      <span className="font-mono text-emerald-700 font-semibold text-[11px]">
                        +{Number(q.positive_marks).toFixed(2)} pts
                      </span>
                      {Number(q.negative_marks) > 0 && (
                        <span className="font-mono text-rose-700 text-[11px]">
                          -{Number(q.negative_marks).toFixed(2)}
                        </span>
                      )}
                    </div>

                    {/* Order & Remove Controls */}
                    <div className="flex items-center space-x-1">
                      <button
                        type="button"
                        onClick={() => handleMoveQuestion(idx, 'up')}
                        disabled={idx === 0}
                        className="p-1 text-slate-400 hover:text-slate-700 disabled:opacity-30 rounded hover:bg-slate-100"
                        title="Move Up"
                      >
                        <ArrowUp className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleMoveQuestion(idx, 'down')}
                        disabled={idx === activeVersion.questions.length - 1}
                        className="p-1 text-slate-400 hover:text-slate-700 disabled:opacity-30 rounded hover:bg-slate-100"
                        title="Move Down"
                      >
                        <ArrowDown className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRemoveQuestion(q.id)}
                        className="p-1 text-slate-400 hover:text-rose-600 rounded hover:bg-rose-50 ml-1"
                        title="Remove Question from Draft"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Prompt */}
                  <p className="font-medium text-slate-900 leading-relaxed">{q.prompt}</p>

                  {/* Options List */}
                  <div className="space-y-1 pl-2 border-l-2 border-slate-200">
                    {q.options.map((opt, optIdx) => (
                      <div
                        key={opt.id}
                        className={`px-2 py-0.5 rounded text-[11px] flex items-center justify-between ${
                          opt.is_correct ? 'bg-emerald-50 text-emerald-900 font-medium' : 'text-slate-600'
                        }`}
                      >
                        <span>
                          {String.fromCharCode(65 + optIdx)}. {opt.option_text}
                        </span>
                        {opt.is_correct && (
                          <span className="text-[10px] text-emerald-700 font-bold uppercase">Correct</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )}



      {/* Question Selector Modal */}
      {isSelectorOpen && (
        <QuestionSelectorModal
          isOpen={true}
          token={token}
          existingQuestionIds={activeVersion.questions.map((q) => q.id)}
          onClose={() => setIsSelectorOpen(false)}
          onAddSelected={handleAddQuestions}
        />
      )}

      {/* Quiz Preview Modal */}
      {isPreviewOpen && (
        <QuizPreviewModal
          isOpen={true}
          token={token}
          quizId={quizId!}
          onClose={() => setIsPreviewOpen(false)}
          onPublishSuccess={() => {
            setIsPreviewOpen(false)
            setSuccessFeedback('Assessment version successfully published and locked as immutable!')
            setTimeout(() => setSuccessFeedback(null), 4000)
            loadQuizData()
          }}
        />
      )}
    </div>
  )
}
