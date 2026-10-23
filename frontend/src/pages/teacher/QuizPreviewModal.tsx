import React, { useState, useEffect } from 'react'
import type { QuizPreview } from '../../types/quiz'
import type { QuestionDifficulty } from '../../types/question'
import { previewQuiz, publishQuiz } from '../../services/quizApi'
import {
  X,
  CheckCircle2,
  AlertCircle,
  Clock,
  Calendar,
  Award,
  ShieldAlert,
  Loader2,
  Send,
} from 'lucide-react'

interface QuizPreviewModalProps {
  isOpen: boolean
  token: string
  quizId: string
  onClose: () => void
  onPublishSuccess: () => void
}

export const QuizPreviewModal: React.FC<QuizPreviewModalProps> = ({
  isOpen,
  token,
  quizId,
  onClose,
  onPublishSuccess,
}) => {
  const [previewData, setPreviewData] = useState<QuizPreview | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfirmPublish, setShowConfirmPublish] = useState(false)

  useEffect(() => {
    if (isOpen && quizId && token) {
      setIsLoading(true)
      setError(null)
      setShowConfirmPublish(false)
      previewQuiz(token, quizId)
        .then((data) => setPreviewData(data))
        .catch((err) => setError(err.message || 'Failed to load preview.'))
        .finally(() => setIsLoading(false))
    }
  }, [isOpen, quizId, token])

  if (!isOpen) return null

  const handlePublish = async () => {
    if (!token || !quizId) return
    setIsPublishing(true)
    setError(null)
    try {
      await publishQuiz(token, quizId)
      onPublishSuccess()
      onClose()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Publish failed.')
      setShowConfirmPublish(false)
    } finally {
      setIsPublishing(false)
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
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-3xl w-full max-h-[92vh] flex flex-col text-slate-900">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h2 className="text-base font-bold text-slate-900">Assessment Pre-Publication Preview</h2>
            {previewData && (
              <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                Version {previewData.version_number} Draft
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="whitespace-pre-line">{error}</div>
            </div>
          )}

          {isLoading ? (
            <div className="py-16 text-center space-y-2">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
              <p className="text-xs text-slate-500 font-medium">Validating quiz readiness and calculating metrics...</p>
            </div>
          ) : previewData ? (
            <>
              {/* Validation Status Banner */}
              {previewData.can_publish ? (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start space-x-3 text-emerald-900">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider">Ready for Publication</h4>
                    <p className="text-xs text-emerald-800 mt-0.5">
                      All pre-flight checks passed. Publishing will create an immutable Version {previewData.version_number} snapshot.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl space-y-2 text-rose-900">
                  <div className="flex items-center space-x-2 font-bold text-xs uppercase tracking-wider text-rose-700">
                    <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                    <span>Publication Blocked — Fix Issues Below:</span>
                  </div>
                  <ul className="text-xs text-rose-800 space-y-1 pl-6 list-disc">
                    {previewData.validation_errors.map((err, idx) => (
                      <li key={idx}>{err.message}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Assessment Meta Summary Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Course Code</span>
                  <span className="font-bold text-slate-800 text-sm font-mono">{previewData.course_code}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Duration</span>
                  <span className="font-bold text-slate-800 text-sm flex items-center space-x-1 mt-0.5">
                    <Clock className="w-3.5 h-3.5 text-blue-600" />
                    <span>{previewData.duration_minutes} mins</span>
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Max Attempts</span>
                  <span className="font-bold text-slate-800 text-sm">{previewData.max_attempts}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-semibold">Total Possible Marks</span>
                  <span className="font-bold text-emerald-700 text-sm flex items-center space-x-1 mt-0.5">
                    <Award className="w-3.5 h-3.5" />
                    <span>{Number(previewData.total_marks).toFixed(2)} pts</span>
                  </span>
                </div>
              </div>

              {/* Schedule and Policies */}
              <div className="space-y-2 text-xs">
                <div className="flex items-center space-x-2 text-slate-600">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span>
                    <strong>Window:</strong> {new Date(previewData.opens_at).toLocaleString()} – {new Date(previewData.closes_at).toLocaleString()}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <span className="px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700 font-medium">
                    Backtracking: {previewData.allow_backtracking ? 'Permitted' : 'Disabled (Forward Only)'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700 font-medium">
                    Shuffle Questions: {previewData.shuffle_questions ? 'Yes' : 'No'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700 font-medium">
                    Multi-Answer: {previewData.multi_answer_policy.replace(/_/g, ' ')}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700 font-medium">
                    Tab-switch Warning: {previewData.tab_switch_limit} (Penalty: {previewData.tab_switch_penalty_marks} pts)
                  </span>
                </div>
              </div>

              {/* Difficulty Breakdown */}
              <div className="p-3 bg-white border border-slate-200 rounded-lg flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700">Questions Breakdown:</span>
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold text-[11px]">
                    {previewData.difficulty_breakdown.easy} Easy
                  </span>
                  <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-semibold text-[11px]">
                    {previewData.difficulty_breakdown.medium} Medium
                  </span>
                  <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-semibold text-[11px]">
                    {previewData.difficulty_breakdown.hard} Hard
                  </span>
                </div>
              </div>

              {/* Questions List Preview */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Questions in Assessment ({previewData.questions.length})
                </h3>
                {previewData.questions.map((q, qIdx) => (
                  <div key={q.id} className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-slate-400">#{qIdx + 1}</span>
                        <span className="font-semibold uppercase text-[10px] text-slate-600 bg-white px-2 py-0.5 border border-slate-200 rounded">
                          {q.question_type.replace('_', ' ')}
                        </span>
                        {renderDifficultyBadge(q.difficulty)}
                      </div>
                      <span className="font-mono text-emerald-700 font-semibold">
                        +{Number(q.positive_marks).toFixed(2)} pts
                      </span>
                    </div>

                    <p className="font-medium text-slate-900 leading-relaxed">{q.prompt}</p>

                    <div className="space-y-1 pl-2 pt-1 border-l-2 border-slate-300">
                      {q.options.map((opt, optIdx) => (
                        <div
                          key={opt.id}
                          className={`px-2.5 py-1 rounded text-[11px] flex items-center justify-between ${
                            opt.is_correct ? 'bg-emerald-100/70 text-emerald-900 font-semibold' : 'text-slate-600'
                          }`}
                        >
                          <span>{String.fromCharCode(65 + optIdx)}. {opt.option_text}</span>
                          {opt.is_correct && <span className="text-[10px] uppercase font-bold text-emerald-700">Correct Answer</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-medium transition-colors"
          >
            Close Preview
          </button>

          {previewData?.can_publish && (
            <div>
              {!showConfirmPublish ? (
                <button
                  type="button"
                  onClick={() => setShowConfirmPublish(true)}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors shadow-2xs"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Publish Version {previewData.version_number}</span>
                </button>
              ) : (
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold text-amber-800 bg-amber-50 px-2.5 py-1 rounded border border-amber-200">
                    Lock Version {previewData.version_number} as Immutable?
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowConfirmPublish(false)}
                    className="px-2.5 py-1 text-xs text-slate-500 hover:text-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handlePublish}
                    disabled={isPublishing}
                    className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-colors"
                  >
                    {isPublishing ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <span>Yes, Confirm & Publish</span>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
