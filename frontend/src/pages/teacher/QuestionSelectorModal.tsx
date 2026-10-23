import React, { useState, useEffect, useCallback } from 'react'
import type { Question, QuestionDifficulty } from '../../types/question'
import { fetchQuestionBank } from '../../services/questionBankApi'
import { X, Search, Plus, Loader2, AlertCircle } from 'lucide-react'

interface QuestionSelectorModalProps {
  isOpen: boolean
  token: string
  existingQuestionIds: string[]
  onClose: () => void
  onAddSelected: (selectedIds: string[]) => Promise<void>
}

export const QuestionSelectorModal: React.FC<QuestionSelectorModalProps> = ({
  isOpen,
  token,
  existingQuestionIds,
  onClose,
  onAddSelected,
}) => {
  const [questions, setQuestions] = useState<Question[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [difficultyFilter, setDifficultyFilter] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadBankQuestions = useCallback(async () => {
    if (!token || !isOpen) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchQuestionBank(token, {
        page: 1,
        page_size: 100,
        question_type: typeFilter || undefined,
        difficulty: difficultyFilter || undefined,
        search: searchQuery.trim() || undefined,
      })
      setQuestions(data.items)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load question bank.')
    } finally {
      setIsLoading(false)
    }
  }, [token, isOpen, typeFilter, difficultyFilter, searchQuery])

  useEffect(() => {
    if (isOpen) {
      setSelectedIds(new Set())
      loadBankQuestions()
    }
  }, [isOpen, loadBankQuestions])

  if (!isOpen) return null

  const existingSet = new Set(existingQuestionIds)

  const toggleSelect = (id: string) => {
    if (existingSet.has(id)) return
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleSelectAllAvailable = () => {
    const available = questions.filter((q) => !existingSet.has(q.id)).map((q) => q.id)
    if (selectedIds.size === available.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(available))
    }
  }

  const handleAdd = async () => {
    if (selectedIds.size === 0) return
    setIsSubmitting(true)
    setError(null)
    try {
      await onAddSelected(Array.from(selectedIds))
      onClose()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to add questions.')
    } finally {
      setIsSubmitting(false)
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
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-3xl w-full max-h-[90vh] flex flex-col text-slate-900">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Select Questions from Question Bank</h2>
            <p className="text-xs text-slate-500">
              Selected questions are safely cloned into your quiz draft as independent copies
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Bar */}
        <div className="p-4 border-b border-slate-200 bg-slate-50 space-y-3">
          {error && (
            <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-center gap-2">
            <div className="relative flex-1 w-full">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search question bank prompt..."
                className="w-full text-xs pl-8 pr-3 py-1.5 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center space-x-2 w-full sm:w-auto">
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="single_choice">Single MCQ</option>
                <option value="multiple_choice">Multi-MCQ</option>
                <option value="true_false">True / False</option>
              </select>

              <select
                value={difficultyFilter}
                onChange={(e) => setDifficultyFilter(e.target.value)}
                className="text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
              >
                <option value="">All Difficulties</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>
              {questions.length} questions available in bank
            </span>
            <button
              type="button"
              onClick={handleSelectAllAvailable}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Toggle Select All Available
            </button>
          </div>
        </div>

        {/* Question List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading ? (
            <div className="py-12 text-center space-y-2">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600 mx-auto" />
              <p className="text-xs text-slate-500">Loading questions from bank...</p>
            </div>
          ) : questions.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No matching questions found in your Question Bank.
            </div>
          ) : (
            questions.map((q) => {
              const isAlreadyInDraft = existingSet.has(q.id)
              const isSelected = selectedIds.has(q.id)

              return (
                <div
                  key={q.id}
                  onClick={() => toggleSelect(q.id)}
                  className={`p-3.5 rounded-lg border text-xs transition-colors flex items-start space-x-3 cursor-pointer ${
                    isAlreadyInDraft
                      ? 'bg-slate-50 border-slate-200 opacity-60 cursor-not-allowed'
                      : isSelected
                      ? 'bg-blue-50/70 border-blue-400'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="pt-0.5">
                    <input
                      type="checkbox"
                      checked={isSelected || isAlreadyInDraft}
                      disabled={isAlreadyInDraft}
                      onChange={() => toggleSelect(q.id)}
                      className="rounded text-blue-600 focus:ring-blue-500 h-4 w-4"
                    />
                  </div>

                  <div className="flex-1 space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-800 uppercase text-[10px] tracking-wider px-1.5 py-0.5 bg-slate-100 rounded">
                        {q.question_type.replace('_', ' ')}
                      </span>
                      {renderDifficultyBadge(q.difficulty)}
                      <span className="font-mono text-emerald-700 text-[11px]">
                        +{Number(q.positive_marks).toFixed(2)} pts
                      </span>
                      {isAlreadyInDraft && (
                        <span className="text-[10px] font-semibold text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">
                          Already Added
                        </span>
                      )}
                    </div>
                    <p className="text-slate-800 font-medium leading-relaxed">{q.prompt}</p>
                    <p className="text-slate-500 text-[11px]">
                      {q.options.length} options ({q.options.filter((o) => o.is_correct).length} correct)
                    </p>
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <span className="text-xs text-slate-600 font-medium">
            {selectedIds.size} {selectedIds.size === 1 ? 'question' : 'questions'} selected
          </span>
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleAdd}
              disabled={selectedIds.size === 0 || isSubmitting}
              className="inline-flex items-center space-x-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-300 text-white rounded-lg text-xs font-medium transition-colors"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Adding...</span>
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Selected ({selectedIds.size})</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
