import React, { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'
import type { Question, QuestionType, QuestionDifficulty, QuestionCreatePayload } from '../../types/question'
import {
  fetchQuestionBank,
  createQuestion,
  updateQuestion,
  deleteQuestion,
  downloadCsvTemplate,
} from '../../services/questionBankApi'
import { QuestionModal } from './QuestionModal'
import { CsvImportModal } from './CsvImportModal'
import {
  Plus,
  Upload,
  Download,
  Search,
  Pencil,
  Trash2,
  CheckCircle2,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Loader2,
  FolderOpen,
} from 'lucide-react'


export const QuestionBank: React.FC = () => {
  const { session } = useAuth()
  const token = session?.access_token || ''

  // Data state
  const [questions, setQuestions] = useState<Question[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [totalPages, setTotalPages] = useState(1)
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [difficultyFilter, setDifficultyFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')

  // UI state
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  // Modals state
  const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const loadQuestions = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchQuestionBank(token, {
        page,
        page_size: pageSize,
        question_type: typeFilter || undefined,
        difficulty: difficultyFilter || undefined,
        search: searchQuery.trim() || undefined,
      })
      setQuestions(data.items)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load question bank.')
    } finally {
      setIsLoading(false)
    }
  }, [token, page, pageSize, typeFilter, difficultyFilter, searchQuery])

  useEffect(() => {
    loadQuestions()
  }, [loadQuestions])

  const handleOpenCreateModal = () => {
    setEditingQuestion(null)
    setIsQuestionModalOpen(true)
  }

  const handleOpenEditModal = (q: Question) => {
    setEditingQuestion(q)
    setIsQuestionModalOpen(true)
  }

  const handleSaveQuestion = async (payload: QuestionCreatePayload) => {
    if (!token) return
    if (editingQuestion) {
      await updateQuestion(token, editingQuestion.id, payload)
      setFeedback('Question updated successfully.')
    } else {
      await createQuestion(token, payload)
      setFeedback('Question created successfully.')
    }
    loadQuestions()
    setTimeout(() => setFeedback(null), 3000)
  }

  const handleDeleteQuestion = async (id: string) => {
    if (!token) return
    try {
      setDeletingId(id)
      await deleteQuestion(token, id)
      setFeedback('Question removed from question bank.')
      loadQuestions()
      setTimeout(() => setFeedback(null), 3000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete question.')
    } finally {
      setDeletingId(null)
    }
  }

  const handleDownloadTemplate = async () => {
    if (!token) return
    try {
      await downloadCsvTemplate(token)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to download template.')
    }
  }

  const renderTypeBadge = (type: QuestionType) => {
    switch (type) {
      case 'single_choice':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">
            Single MCQ
          </span>
        )
      case 'multiple_choice':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-purple-50 text-purple-700 border border-purple-200">
            Multi MCQ
          </span>
        )
      case 'true_false':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-teal-50 text-teal-700 border border-teal-200">
            True / False
          </span>
        )
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

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6 text-slate-900">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Question Bank</h1>
            <span className="px-2 py-0.5 bg-slate-100 text-slate-700 text-xs font-semibold rounded-full border border-slate-200">
              {total} {total === 1 ? 'Question' : 'Questions'}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Author and manage reusable questions for quizzes, assignments, and question pools
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={handleDownloadTemplate}
            className="inline-flex items-center space-x-1.5 px-3 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium transition-colors shadow-2xs"
            title="Download CSV format template"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Template</span>
          </button>

          <button
            type="button"
            onClick={() => setIsImportModalOpen(true)}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 rounded-lg text-xs font-medium transition-colors shadow-2xs"
          >
            <Upload className="w-3.5 h-3.5 text-blue-600" />
            <span>Import CSV</span>
          </button>

          <button
            type="button"
            onClick={handleOpenCreateModal}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors shadow-2xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Question</span>
          </button>
        </div>
      </div>

      {/* Feedback banner */}
      {feedback && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={loadQuestions}
            className="text-xs font-semibold text-rose-800 underline hover:no-underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-3 bg-white border border-slate-200 rounded-xl shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setPage(1)
            }}
            placeholder="Search questions by prompt statement..."
            className="w-full text-xs pl-9 pr-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Type & Difficulty Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Difficulty Dropdown */}
          <select
            value={difficultyFilter}
            onChange={(e) => {
              setDifficultyFilter(e.target.value)
              setPage(1)
            }}
            className="text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>

          {/* Type Filter Pills */}
          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 md:pb-0">
            {[
              { label: 'All Types', value: '' },
              { label: 'Single MCQ', value: 'single_choice' },
              { label: 'Multi MCQ', value: 'multiple_choice' },
              { label: 'True / False', value: 'true_false' },
            ].map((pill) => (
              <button
                key={pill.value}
                type="button"
                onClick={() => {
                  setTypeFilter(pill.value)
                  setPage(1)
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-colors ${
                  typeFilter === pill.value
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {pill.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Questions List Content */}
      {isLoading ? (
        <div className="min-h-[40vh] flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          <p className="text-xs text-slate-500 font-medium">Loading question bank...</p>
        </div>
      ) : questions.length === 0 ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-xl space-y-3">
          <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto text-slate-400">
            <FolderOpen className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800">No questions found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {searchQuery || typeFilter || difficultyFilter
              ? 'No questions matched your active filters. Try resetting search, difficulty, or type filter.'
              : 'Your question bank is empty. Create questions manually or import a batch via CSV.'}
          </p>
          <div className="pt-2 flex items-center justify-center space-x-2">
            <button
              type="button"
              onClick={handleOpenCreateModal}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create First Question</span>
            </button>
            <button
              type="button"
              onClick={() => setIsImportModalOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Import CSV</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {questions.map((q, qIndex) => (
            <div
              key={q.id}
              className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs hover:border-slate-300 transition-colors space-y-3"
            >
              {/* Question Card Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-slate-400">
                    #{(page - 1) * pageSize + qIndex + 1}
                  </span>
                  {renderTypeBadge(q.question_type)}
                  {renderDifficultyBadge(q.difficulty)}
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    +{Number(q.positive_marks).toFixed(2)} pts
                  </span>
                  {Number(q.negative_marks) > 0 && (
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
                      -{Number(q.negative_marks).toFixed(2)} penalty
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-1.5">
                  <button
                    type="button"
                    onClick={() => handleOpenEditModal(q)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Edit question"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (window.confirm('Delete this question from your personal question bank?')) {
                        handleDeleteQuestion(q.id)
                      }
                    }}
                    disabled={deletingId === q.id}
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                    title="Delete question"
                  >
                    {deletingId === q.id ? (
                      <Loader2 className="w-4 h-4 animate-spin text-rose-500" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Prompt statement */}
              <p className="text-sm font-medium text-slate-900 leading-relaxed">
                {q.prompt}
              </p>

              {/* Options list */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                {q.options.map((opt, oIdx) => (
                  <div
                    key={opt.id}
                    className={`p-2.5 rounded-lg border text-xs flex items-center space-x-2 ${
                      opt.is_correct
                        ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950 font-medium'
                        : 'bg-slate-50/60 border-slate-200 text-slate-700'
                    }`}
                  >
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                        opt.is_correct
                          ? 'bg-emerald-600 text-white'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {String.fromCharCode(65 + oIdx)}
                    </span>
                    <span className="truncate flex-1">{opt.option_text}</span>
                    {opt.is_correct && (
                      <span className="text-[10px] font-semibold text-emerald-700 uppercase tracking-wider">
                        Correct
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-200 text-xs text-slate-600">
              <span>
                Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} questions
              </span>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page <= 1}
                  className="p-1.5 border border-slate-300 rounded-lg hover:bg-slate-100 disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="font-medium">
                  Page {page} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                  disabled={page >= totalPages}
                  className="p-1.5 border border-slate-300 rounded-lg hover:bg-slate-100 disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manual Create / Edit Modal */}
      <QuestionModal
        isOpen={isQuestionModalOpen}
        onClose={() => setIsQuestionModalOpen(false)}
        onSave={handleSaveQuestion}
        initialQuestion={editingQuestion}
      />

      {/* CSV Import Modal */}
      <CsvImportModal
        isOpen={isImportModalOpen}
        token={token}
        onClose={() => setIsImportModalOpen(false)}
        onImportSuccess={() => {
          setFeedback('CSV import successful. Question bank refreshed.')
          loadQuestions()
          setTimeout(() => setFeedback(null), 3000)
        }}
      />
    </div>
  )
}
