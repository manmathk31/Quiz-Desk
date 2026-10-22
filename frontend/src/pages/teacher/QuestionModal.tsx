import React, { useState, useEffect } from 'react'
import type { Question, QuestionCreatePayload, QuestionType } from '../../types/question'
import { X, Plus, Trash2, Check, AlertCircle, Loader2 } from 'lucide-react'

interface QuestionModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (payload: QuestionCreatePayload) => Promise<void>
  initialQuestion?: Question | null
}

interface OptionFormState {
  option_text: string
  is_correct: boolean
}

export const QuestionModal: React.FC<QuestionModalProps> = ({
  isOpen,
  onClose,
  onSave,
  initialQuestion,
}) => {
  const [questionType, setQuestionType] = useState<QuestionType>('single_choice')
  const [prompt, setPrompt] = useState('')
  const [positiveMarks, setPositiveMarks] = useState<number>(1.0)
  const [negativeMarks, setNegativeMarks] = useState<number>(0.0)
  const [options, setOptions] = useState<OptionFormState[]>([
    { option_text: '', is_correct: true },
    { option_text: '', is_correct: false },
    { option_text: '', is_correct: false },
    { option_text: '', is_correct: false },
  ])
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (initialQuestion) {
      setQuestionType(initialQuestion.question_type)
      setPrompt(initialQuestion.prompt)
      setPositiveMarks(Number(initialQuestion.positive_marks))
      setNegativeMarks(Number(initialQuestion.negative_marks))
      setOptions(
        initialQuestion.options.map((o) => ({
          option_text: o.option_text,
          is_correct: o.is_correct,
        }))
      )
    } else {
      setQuestionType('single_choice')
      setPrompt('')
      setPositiveMarks(1.0)
      setNegativeMarks(0.0)
      setOptions([
        { option_text: '', is_correct: true },
        { option_text: '', is_correct: false },
        { option_text: '', is_correct: false },
        { option_text: '', is_correct: false },
      ])
    }
    setError(null)
  }, [initialQuestion, isOpen])

  if (!isOpen) return null

  const handleTypeChange = (newType: QuestionType) => {
    setQuestionType(newType)
    setError(null)
    if (newType === 'true_false') {
      setOptions([
        { option_text: 'True', is_correct: true },
        { option_text: 'False', is_correct: false },
      ])
    } else if (options.length < 2) {
      setOptions([
        { option_text: '', is_correct: true },
        { option_text: '', is_correct: false },
      ])
    } else if (newType === 'single_choice') {
      // Ensure only one is correct
      const firstCorrectIndex = options.findIndex((o) => o.is_correct)
      const targetIndex = firstCorrectIndex >= 0 ? firstCorrectIndex : 0
      setOptions(
        options.map((opt, idx) => ({
          ...opt,
          is_correct: idx === targetIndex,
        }))
      )
    }
  }

  const handleOptionTextChange = (index: number, text: string) => {
    setOptions(
      options.map((opt, idx) => (idx === index ? { ...opt, option_text: text } : opt))
    )
  }

  const handleCorrectSelect = (index: number) => {
    if (questionType === 'single_choice' || questionType === 'true_false') {
      setOptions(
        options.map((opt, idx) => ({
          ...opt,
          is_correct: idx === index,
        }))
      )
    } else {
      // multiple_choice: toggle
      setOptions(
        options.map((opt, idx) =>
          idx === index ? { ...opt, is_correct: !opt.is_correct } : opt
        )
      )
    }
  }

  const addOption = () => {
    if (options.length >= 6) return
    setOptions([...options, { option_text: '', is_correct: false }])
  }

  const removeOption = (index: number) => {
    if (options.length <= 2) return
    const newOptions = options.filter((_, idx) => idx !== index)
    // If we removed the only correct answer in single choice, set first option as correct
    if (
      questionType === 'single_choice' &&
      !newOptions.some((o) => o.is_correct) &&
      newOptions.length > 0
    ) {
      newOptions[0].is_correct = true
    }
    setOptions(newOptions)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Client-side pre-validation
    const cleanPrompt = prompt.trim()
    if (!cleanPrompt) {
      setError('Question prompt cannot be empty.')
      return
    }

    if (positiveMarks <= 0) {
      setError('Positive marks must be strictly greater than 0.')
      return
    }

    if (negativeMarks < 0) {
      setError('Negative marks cannot be negative.')
      return
    }

    // Validate options
    for (let i = 0; i < options.length; i++) {
      if (!options[i].option_text.trim()) {
        setError(`Option ${i + 1} cannot be blank.`)
        return
      }
    }

    // Duplicate options check
    const normalizedTexts = options.map((o) => o.option_text.trim().toLowerCase())
    if (new Set(normalizedTexts).size !== normalizedTexts.length) {
      setError('All options must have unique text.')
      return
    }

    const correctCount = options.filter((o) => o.is_correct).length
    if (questionType === 'single_choice' && correctCount !== 1) {
      setError('Please select exactly one correct option.')
      return
    }
    if (questionType === 'multiple_choice' && correctCount < 1) {
      setError('Please select at least one correct option.')
      return
    }
    if (questionType === 'true_false') {
      if (options.length !== 2 || correctCount !== 1) {
        setError('True/False questions must have exactly two options and one correct answer.')
        return
      }
    }

    const payload: QuestionCreatePayload = {
      question_type: questionType,
      prompt: cleanPrompt,
      positive_marks: positiveMarks,
      negative_marks: negativeMarks,
      options: options.map((opt, idx) => ({
        option_text: opt.option_text.trim(),
        order_index: idx,
        is_correct: opt.is_correct,
      })),
    }

    try {
      setIsSubmitting(true)
      await onSave(payload)
      onClose()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save question.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-2xl w-full max-h-[90vh] flex flex-col text-slate-900">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {initialQuestion ? 'Edit Question' : 'Create New Question'}
            </h2>
            <p className="text-xs text-slate-500">
              Add reusable question to your personal question bank
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

        {/* Modal Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Question Type & Marks Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Question Type
              </label>
              <select
                value={questionType}
                onChange={(e) => handleTypeChange(e.target.value as QuestionType)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="single_choice">Single Choice (MCQ)</option>
                <option value="multiple_choice">Multiple Choice (Multi-MCQ)</option>
                <option value="true_false">True / False</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Positive Marks
              </label>
              <input
                type="number"
                step="0.25"
                min="0.25"
                value={positiveMarks}
                onChange={(e) => setPositiveMarks(parseFloat(e.target.value) || 0)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Negative Penalty Marks
              </label>
              <input
                type="number"
                step="0.25"
                min="0"
                value={negativeMarks}
                onChange={(e) => setNegativeMarks(parseFloat(e.target.value) || 0)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          {/* Question Prompt */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Question Statement / Prompt
            </label>
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter the question text here..."
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
              required
            />
          </div>

          {/* Options Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-slate-700">
                Options & Correct Answer Choice(s)
              </label>
              <span className="text-[11px] text-slate-500">
                {questionType === 'single_choice' && 'Click radio button to mark correct answer'}
                {questionType === 'multiple_choice' && 'Select checkboxes for all correct answers'}
                {questionType === 'true_false' && 'Select whether True or False is correct'}
              </span>
            </div>

            <div className="space-y-2">
              {options.map((opt, idx) => (
                <div
                  key={idx}
                  className={`flex items-center space-x-2 p-2 rounded-lg border transition-colors ${
                    opt.is_correct
                      ? 'border-emerald-300 bg-emerald-50/50'
                      : 'border-slate-200 bg-slate-50/40'
                  }`}
                >
                  {/* Selector for correctness */}
                  <button
                    type="button"
                    onClick={() => handleCorrectSelect(idx)}
                    className={`w-6 h-6 rounded flex items-center justify-center border transition-colors shrink-0 ${
                      questionType === 'multiple_choice' ? 'rounded-md' : 'rounded-full'
                    } ${
                      opt.is_correct
                        ? 'bg-emerald-600 border-emerald-600 text-white'
                        : 'border-slate-300 hover:border-emerald-400 bg-white'
                    }`}
                    title={opt.is_correct ? 'Correct Option' : 'Mark as Correct'}
                  >
                    {opt.is_correct && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </button>

                  <span className="text-xs font-bold text-slate-500 w-4">
                    {String.fromCharCode(65 + idx)}
                  </span>

                  {/* Option Text Input */}
                  <input
                    type="text"
                    value={opt.option_text}
                    readOnly={questionType === 'true_false'}
                    onChange={(e) => handleOptionTextChange(idx, e.target.value)}
                    placeholder={`Option ${String.fromCharCode(65 + idx)} text`}
                    className={`flex-1 text-xs px-3 py-1.5 border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white ${
                      questionType === 'true_false' ? 'cursor-not-allowed bg-slate-100' : ''
                    }`}
                    required
                  />

                  {/* Remove option button (if > 2 and not True/False) */}
                  {questionType !== 'true_false' && options.length > 2 && (
                    <button
                      type="button"
                      onClick={() => removeOption(idx)}
                      className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                      title="Remove option"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* Add option button for MCQs */}
            {questionType !== 'true_false' && options.length < 6 && (
              <button
                type="button"
                onClick={addOption}
                className="inline-flex items-center space-x-1.5 text-xs text-blue-600 hover:text-blue-700 font-medium py-1 px-2 rounded hover:bg-blue-50 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Option ({String.fromCharCode(65 + options.length)})</span>
              </button>
            )}
          </div>
        </form>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-xl flex items-center justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 rounded-lg hover:bg-slate-200 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <span>{initialQuestion ? 'Save Changes' : 'Create Question'}</span>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
